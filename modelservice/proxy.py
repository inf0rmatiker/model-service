import grpc

from flask import Flask, request
from modelservice import modelservice_pb2_grpc
from modelservice.modelservice_pb2 import BuildModelsRequest, BuildModelsResponse, HyperParameters

app = Flask(__name__)


# Main entrypoint
def run(master_hostname="localhost", master_port=50051, flask_port=5000):
    print("Running flask server...")
    app.config["MASTER_HOSTNAME"] = master_hostname
    app.config["MASTER_PORT"] = master_port
    app.run(host="0.0.0.0", port=flask_port)  # Entrypoint


@app.route("/model", methods=["GET"])
def get_model():

    # TODO Parse query from HTTP JSON -> build gRPC request to Master

    # TODO Send gRPC request to master and relay response back to client

    return "At some point, your model will be returned from this endpoint"


@app.route("/model", methods=["POST"])
def submit_job():
    request_data: str = request.json
    print(f"request_data: {request_data}")

    # TODO: Add checks for optimizer and loss types to ensure the values provided exist in the enums

    with grpc.insecure_channel(f"{app.config['MASTER_HOSTNAME']}:{app.config['MASTER_PORT']}") as channel:
        stub: modelservice_pb2_grpc.MasterStub = modelservice_pb2_grpc.MasterStub(channel)

        request_hyper_parameters: HyperParameters = HyperParameters(
            epochs=request_data.epochs,
            learning_rate=request_data.learning_rate,
            normalize_inputs=request_data.normalize_inputs,
            train_split=request_data.train_split,
            optimizer_type=request_data.optimizer_type,
            loss_type=request_data.loss_type
        )

        # Build and log gRPC request
        build_models_grpc_request: BuildModelsRequest = BuildModelsRequest(
            feature_fields=request_data.feature_fields,
            label_field=request_data.label_field,
            hyper_parameters=request_hyper_parameters
        )

        info(build_models_grpc_request)

        # Submit validation job
        build_models_grpc_response: BuildModelsResponse = stub.BuildModels(build_models_grpc_request)
        info(f"Build Models Response received: {build_models_grpc_response}")

    # TODO: Set up proper handling of response from master and response to client

    response_code: int = HTTPStatus.OK if build_models_grpc_response.ok else HTTPStatus.INTERNAL_SERVER_ERROR
    return build_json_response(build_models_grpc_response), response_code
