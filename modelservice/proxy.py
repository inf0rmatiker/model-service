import grpc

from flask import Flask, request
from modelservice import modelservice_pb2_grpc
from modelservice.modelservice_pb2 import BuildModelsRequest, BuildModelsResponse, LossFunction, ModelCategory, ModelFramework, GetModelRequest, GetModelResponse, GisJoinMetadata, WorkerRegistrationResponse, WorkerRegistrationRequest

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

    with grpc.insecure_channel(f"{app.config['MASTER_HOSTNAME']}:{app.config['MASTER_PORT']}") as channel:
        stub: modelservice_pb2_grpc.MasterStub = modelservice_pb2_grpc.MasterStub(channel)

        # Build and log gRPC request
        build_models_grpc_request: BuildModelsRequest = BuildModelsRequest(
            model_framework=request_data.model_framework,
            model_category=request_data.model_category,
            feature_fields=request_data.feature_fields,
            label_field=request_data.label_field,
            normalize_inputs=request_data.normalize_inputs,
            loss_function=request_data.loss_function
        )

        info(build_models_grpc_request)

        # Submit validation job
        build_models_grpc_response: BuildModelsResponse = stub.BuildModels(build_models_grpc_request)
        info(f"Build Models Response received: {build_models_grpc_response}")

    response_code: int = HTTPStatus.OK if build_models_grpc_response.ok else HTTPStatus.INTERNAL_SERVER_ERROR
    return build_json_response(build_models_grpc_response), response_code

    # TODO Parse query from HTTP JSON -> build gRPC request to Master

    # TODO Send gRPC request to master and relay response back to client

    return "At some point, your job will be submitted"
