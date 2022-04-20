import grpc
import json
from flask import Flask, request
from google.protobuf.json_format import MessageToJson, Parse
from http import HTTPStatus
from logging import info, error

from modelservice import modelservice_pb2_grpc
from modelservice.modelservice_pb2 import BuildModelsRequest, BuildModelsResponse, HyperParameters

app = Flask(__name__)


def parameter_usage():
    return ("One or more parameters provided were of an incorrect type. Please check the types sent in your request.\n"
            "epochs -> integer (e.g., 10)\n"
            "learning_rate -> float (e.g., 0.1)\n"
            "normalize_inputs -> numeric boolean with value of one of [0, 1]\n"
            "train_split -> float (e.g., 0.8)\n"
            "optimizer_type -> string with value of one of ['ADAM', 'SGD']\n"
            "loss_type -> string with value of one of ['MEAN_SQUARED_ERROR', 'ROOT_MEAN_SQUARED_ERROR', 'MEAN_ABSOLUTE_ERROR']\n")


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
    request_data_string: str = request.json
    print(f"request_data: {request_data_string}")

    # # Try to cast request data to proper types and return parameter usage error if any are incorrect
    # try:
    #     param_epochs: int = int(request_data["epochs"]) if request_data["epochs"] else 50
    #     param_learning_rate: float = float(request_data["learning_rate"]) if request_data["learning_rate"] else 0.001
    #     param_normalize_inputs: bool = bool(request_data["normalize_inputs"]) if not request_data["normalize_inputs"] == "" else True
    #     param_train_split: float = float(request_data["train_split"]) if request_data["train_split"] else 0.8
    # except Exception as err:
    #     print("try-except exception for casting request values")
    #     print(err)
    #     return parameter_usage()
    #
    # # Check that optimizer_type is one of the correct types and return parameter usage error if not
    # if request_data["optimizer_type"] == "" or request_data["optimizer_type"] in ["ADAM", "SGD"]:
    #     param_optimizer_type: str = request_data["optimizer_type"] if request_data["optimizer_type"] else "ADAM"
    # else:
    #     print("if-else exception for optimizer_type")
    #     return parameter_usage()
    #
    # # Check that loss_type is one of the correct types and return parameter usage error if not
    # if request_data["loss_type"] == "" or request_data["loss_type"] in ["MEAN_SQUARED_ERROR", "ROOT_MEAN_SQUARED_ERROR", "MEAN_ABSOLUTE_ERROR"]:
    #     param_loss_type: str = request_data["loss_type"] if request_data["loss_type"] else "MEAN_SQUARED_ERROR"
    # else:
    #     print("if-else exception for loss_type")
    #     return parameter_usage()

    request_data: dict = json.loads(request_data_string)
    
    try:
        build_models_grpc_request: BuildModelsRequest = Parse(request_data, BuildModelsRequest())
    except Exception as err:
        print("try-except exception for casting request values")
        print(err)
        return parameter_usage()

    with grpc.insecure_channel(f"{app.config['MASTER_HOSTNAME']}:{app.config['MASTER_PORT']}") as channel:
        stub: modelservice_pb2_grpc.MasterStub = modelservice_pb2_grpc.MasterStub(channel)

        # # Set up HyperParameters object to be added to BuildModelsRequest
        # request_hyper_parameters: HyperParameters = HyperParameters(
        #     epochs=param_epochs,
        #     learning_rate=param_learning_rate,
        #     normalize_inputs=param_normalize_inputs,
        #     train_split=param_train_split,
        #     optimizer_type=param_optimizer_type,
        #     loss_type=param_loss_type
        # )
        #
        # # Build and log gRPC request
        # build_models_grpc_request: BuildModelsRequest = BuildModelsRequest(
        #     feature_fields=request_data["feature_fields"],
        #     label_field=request_data["label_field"],
        #     hyper_parameters=request_hyper_parameters
        # )

        info(build_models_grpc_request)

        # Submit validation job
        build_models_grpc_response: BuildModelsResponse = stub.BuildModels(build_models_grpc_request)
        info(f"Build Models Response received: {build_models_grpc_response}")

    response_code: int = HTTPStatus.INTERNAL_SERVER_ERROR if build_models_grpc_response.error_occurred else HTTPStatus.OK
    return build_json_response(build_models_grpc_response), response_code


def build_json_response(build_models_grpc_response: BuildModelsResponse) -> str:
    return MessageToJson(build_models_grpc_response, preserving_proto_field_name=True)
