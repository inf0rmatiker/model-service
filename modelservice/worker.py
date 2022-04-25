import os
import socket
import grpc
import signal

from modelservice import modelservice_pb2_grpc
from concurrent.futures import ThreadPoolExecutor, as_completed
from logging import info, error

from modelservice.modelservice_pb2 import BuildModelsRequest, BuildModelsResponse, GetModelRequest, GetModelResponse, \
    GisJoinMetadata, WorkerRegistrationResponse, WorkerRegistrationRequest, WorkerBuildModelsResponse


class Worker(modelservice_pb2_grpc.WorkerServicer):

    def __init__(self, master_hostname: str, master_port: int, hostname: str, port: int, data_dir: str):
        super(Worker, self).__init__()
        self.master_hostname = master_hostname
        self.master_port = master_port
        self.hostname = hostname
        self.port = port
        self.data_dir = data_dir
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
                    local_gis_joins=gis_join_metadata)
            )

            if registration_response.success:
                self.is_registered = True
                info(f"Successfully registered worker {self.hostname}:{self.port}")
            else:
                error(f"Failed to register worker {self.hostname}:{self.port}: {registration_response}")

    def BuildModels(self, request: BuildModelsRequest, context) -> WorkerBuildModelsResponse:
        info(f"Received request to build models: {request}")
        
        # Save model
        if not self.save_model(request):
            return WorkerBuildModelsResponse(ok=False, hostname=self.hostname)
			
		tf_validator: TensorflowValidator = TensorflowValidator(request, shared_executor, self.local_gis_joins)
		metrics = tf_validator.validate_gis_joins()

        else:
            return WorkerBuildModelsResponse(ok=False, hostname=self.hostname, error_msg="Building models currently unimplemented")

        # Create and return response from aggregated metrics
        return WorkerBuildModelsResponse(
            id=request.id,
            hostname=self.hostname,
            duration_sec=0.0,  # TODO: Capture job profile
            error_occurred=True,
            error_msg="Building models currently unimplemented"
        )
    
    def save_model(self, request: BuildModelsRequest) -> bool:
        ok = True

        # Make the directory
        model_dir = f"{self.saved_models_path}/{request.id}"
        os.mkdir(model_dir)
        info(f"Created directory {model_dir}")

        file_extension = "pkl"  # Default for Scikit-Learn pickle type


        # Saved Tensorflow models have to be either SavedModel or HDF5 format:
        # https://www.tensorflow.org/tutorials/keras/save_and_load#save_the_entire_model
        if request.model_file.type == ModelFileType.TENSORFLOW_SAVED_MODEL_ZIP:
            zip_file = zipfile.ZipFile(io.BytesIO(request.model_file.data))
            zip_file.extractall(model_dir)
            return ok
        elif request.model_file.type == ModelFileType.TENSORFLOW_HDF5:
            file_extension = "h5"
        else:
            return not ok

        # Save the model with appropriate extension
        model_file_path = f"{model_dir}/{request.id}.{file_extension}"
        with open(model_file_path, "wb") as binary_file:
            binary_file.write(request.model_file.data)

        info(f"Finished saving model to {model_file_path}")
        return ok
    

    def GetModel(self, request: GetModelRequest, context) -> GetModelResponse:
        info(f"Received request to retrieve model(s)")
        return GetModelResponse(
            id=request.id,
            error_occurred=True,
            error_msg="Fetching models currently unimplemented"
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
