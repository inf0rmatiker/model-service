import os
import socket
import grpc
# import hashlib
import signal
import tensorflow as tf
import pandas as pd
import shutil


from concurrent.futures import ThreadPoolExecutor, as_completed
from logging import info, error
from sklearn.preprocessing import MinMaxScaler

from modelservice.profiler import Timer
from modelservice import modelservice_pb2_grpc
from modelservice.modelservice_pb2 import BuildModelsRequest, GetModelRequest, GetModelResponse, GisJoinMetadata, \
    WorkerRegistrationResponse, WorkerRegistrationRequest, WorkerBuildModelsResponse, HyperParameters, OptimizerType, \
    LossType, ActivationType, HiddenLayer, OutputLayer, EvaluationMetric


class Worker(modelservice_pb2_grpc.WorkerServicer):

    def __init__(self, master_hostname: str, master_port: int, hostname: str, port: int, data_dir: str):
        super(Worker, self).__init__()
        self.master_hostname = master_hostname
        self.master_port = master_port
        self.hostname = hostname
        self.port = port
        self.data_dir = data_dir[:-1] if data_dir.endswith("/") else data_dir
        self.is_registered = False
        self.local_gis_joins: dict = discover_local_gis_joins(data_dir)  # mapping of { gis_join -> <csv_path> }

        # Register with master
        self.register()

    def deregister(self):
        info("Deregistering...")

        if self.is_registered:
            # Deregister Worker from the Master
            with grpc.insecure_channel(f"{self.master_hostname}:{self.master_port}") as channel:
                stub = modelservice_pb2_grpc.MasterStub(channel)
                registration_response: WorkerRegistrationResponse = stub.DeregisterWorker(
                    WorkerRegistrationRequest(hostname=self.hostname, port=self.port)
                )

                if registration_response.success:
                    info(f"Successfully deregistered from master: {registration_response}")
                    self.is_registered = False
                else:
                    error(f"Failed to deregister from master: {registration_response}")
        else:
            info("We are not registered, no need to deregister")

    def register(self):
        info("Registering...")
        # Send WorkerRegistrationRequest to master
        with grpc.insecure_channel(f"{self.master_hostname}:{self.master_port}") as channel:
            # Create gRPC GisJoinMetadata objects from discovered GISJOIN counts
            gis_join_metadata = []
            for gis_join in self.local_gis_joins:
                gis_join_metadata.append(GisJoinMetadata(
                    gis_join=gis_join
                ))

            stub = modelservice_pb2_grpc.MasterStub(channel)
            registration_response: WorkerRegistrationResponse = stub.RegisterWorker(
                WorkerRegistrationRequest(
                    hostname=self.hostname,
                    port=self.port,
                    local_gis_joins=gis_join_metadata
                ))

            if registration_response.success:
                self.is_registered = True
                info(f"Successfully registered worker {self.hostname}:{self.port}")
            else:
                error(f"Failed to register worker {self.hostname}:{self.port}: {registration_response}")

    def BuildModels(self, request: BuildModelsRequest, context) -> WorkerBuildModelsResponse:
        info(f"Received request to build models: {request}")

        worker_timer: Timer = Timer()
        worker_timer.start()

        feature_fields: list = list(request.feature_fields)
        label_field: str = request.label_field
        hyper_parameters: HyperParameters = request.hyper_parameters
        epochs: int = hyper_parameters.epochs
        learning_rate: float = hyper_parameters.learning_rate
        normalize_inputs: bool = hyper_parameters.normalize_inputs
        train_split: float = hyper_parameters.train_split
        test_split: float = 1.0 - train_split

        if hyper_parameters.optimizer_type == OptimizerType.ADAM:
            optimizer = tf.keras.optimizers.Adam(learning_rate)
        else:
            optimizer = tf.keras.optimizers.SGD(learning_rate)

        if hyper_parameters.loss_type == LossType.MEAN_SQUARED_ERROR:
            loss = "mean_squared_error"
        elif hyper_parameters.loss_type == LossType.MEAN_SQUARED_ERROR:
            loss = "mean_squared_error"
        else:
            loss = "mean_absolute_error"

        evaluation_metrics: list = []  # list(EvaluationMetric)

        # Make models dir for job id
        models_dir: str = f"{self.data_dir}/{request.id}"
        os.mkdir(models_dir)

        count = 1
        gis_join_timer: Timer = Timer()
        for gis_join in request.gis_joins:

            gis_join_timer.start()
            info(f"Loading data for GISJOIN {gis_join} ({count}/{len(request.gis_joins)})...")

            # Load data
            csv_path: str = f"{self.data_dir}/{gis_join}.csv"
            all_df: pd.DataFrame = pd.read_csv(csv_path, header=0).drop("GISJOIN", 1)
            len_df: int = len(all_df.index)
            info(f"Loaded data for GISJOIN {gis_join}: {len_df} records")
            if normalize_inputs:
                scaled = MinMaxScaler(feature_range=(0, 1)).fit_transform(all_df)
                all_df = pd.DataFrame(scaled, columns=all_df.columns)

            features = all_df[feature_fields]
            labels = all_df[label_field]

            # Create Sequential model
            model = tf.keras.Sequential()

            # Add input layer
            model.add(tf.keras.Input(shape=(len(request.feature_fields))))

            # Add hidden layers
            for hidden_layer in hyper_parameters.hidden_layers:
                name: str = hidden_layer.name
                units: int = hidden_layer.units
                activation = "relu"
                model.add(tf.keras.layers.Dense(units=units, activation=activation, name=name))

            # Add output layer
            output_layer: OutputLayer = hyper_parameters.output_layer
            name: str = output_layer.name
            activation = "relu"
            model.add(tf.keras.layers.Dense(units=1, activation=activation, name=name))

            # Compile the model and print its summary
            model.compile(loss=loss, optimizer=optimizer)
            model.summary()

            # Fit the model to the data
            history = model.fit(features, labels, epochs=epochs, validation_split=test_split)
            hist = pd.DataFrame(history.history)
            hist["epoch"] = history.epoch
            info(hist)

            last_row = hist.loc[hist["epoch"] == epochs - 1].values[0]
            training_loss = last_row[0]
            validation_loss = last_row[1]
            info(f"Training loss: {training_loss}, validation loss: {validation_loss}")
            gis_join_timer.stop()

            metric: EvaluationMetric = EvaluationMetric(
                training_loss=training_loss,
                validation_loss=validation_loss,
                duration_sec=gis_join_timer.elapsed,
                error_occurred=False,
                error_message="",
                gis_join_metadata=GisJoinMetadata(
                    gis_join=gis_join,
                    count=len_df
                )
            )
            evaluation_metrics.append(metric)
            model_path: str = f"{models_dir}/{gis_join}.tf"
            model.save(model_path)
            info(f"Saved model {model_path}")
            count += 1
            gis_join_timer.reset()

        info(f"Finished training {count}/{len(request.gis_joins)} models. Returning results...")
        worker_timer.stop()
        return WorkerBuildModelsResponse(
            id=request.id,
            hostname=self.hostname,
            duration_sec=worker_timer.elapsed,
            error_occurred=False,
            error_msg="",
            validation_metrics=evaluation_metrics
        )

    def GetModel(self, request: GetModelRequest, context) -> GetModelResponse:
        info(f"Received request to retrieve model")

        job_id: str = request.model_id
        gis_join: str = request.gis_join
        model_dir: str = f"{self.data_dir}/{job_id}"
        model_path: str = f"{model_dir}/{gis_join}.tf"

        current_dir: str = os.getcwd()
        output_path: str = f"{current_dir}/{gis_join}.tf"

        try:
            shutil.make_archive(output_path, 'zip', model_path)

            file = open(f"{output_path}.zip", 'rb')
            fileContents = file.read()
            file.close()

            os.remove(f"{output_path}.zip")
        except Exception as err:
            print(err)
            return GetModelResponse(
                model_id=job_id,
                error_occurred=True,
                error_msg="Error retrieving requested GIS join",
                filename="",
                data=""
            )

        # SHA1 generation for verifying and validating data received
        # sha1 = hashlib.sha1()
        # sha1.update(fileContents)
        # info("GetModel fileContents SHA1: {0}".format(sha1.hexdigest()))

        return GetModelResponse(
            model_id=job_id,
            error_occurred=False,
            error_msg="",
            filename=f"{gis_join}.tf.zip",
            data=fileContents
        )


# Returns a dictionary of { gis_join }
def discover_local_gis_joins(data_dir: str) -> dict:
    # Clean off trailing slash if present
    data_dir = data_dir[:-1] if data_dir.endswith("/") else data_dir
    gis_join_file_locations: dict = {}

    # Use data_dir to get list of all GISJOIN .csvs on this server
    for filename in os.listdir(data_dir):
        if filename.endswith(".csv"):
            name_parts = filename.split(".")
            gis_join: str = name_parts[0]
            gis_join_file_locations[gis_join] = f"{data_dir}/{filename}"

    return gis_join_file_locations


def shutdown_gracefully(worker: Worker) -> None:
    worker.deregister()
    exit(0)


def run(master_hostname="localhost", master_port=50051, worker_port=50055, data_dir="/data") -> None:

    # Initialize server and worker
    server = grpc.server(ThreadPoolExecutor(max_workers=10))
    hostname = socket.gethostname()
    worker = Worker(master_hostname, master_port, hostname, worker_port, data_dir)

    # Set up Ctrl-C signal handling
    def call_shutdown(signum, frame):
        shutdown_gracefully(worker)

    signal.signal(signal.SIGINT, call_shutdown)

    modelservice_pb2_grpc.add_WorkerServicer_to_server(worker, server)

    # Start the server
    info(f"Starting worker server on {hostname}:{worker_port}")
    server.add_insecure_port(f"{hostname}:{worker_port}")
    server.start()
    server.wait_for_termination()
