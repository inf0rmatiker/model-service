import grpc
from flask import Flask, request
from google.protobuf.json_format import MessageToJson, Parse
# import hashlib
from http import HTTPStatus
from logging import info, error

from modelservice import modelservice_pb2_grpc
from modelservice.modelservice_pb2 import BuildModelsRequest, BuildModelsResponse, GetModelResponse, GetModelRequest, HyperParameters

app = Flask(__name__)


def parameter_usage():
    return ("One or more parameters provided were of an incorrect type or incorrect structure. "
            "Please check the types and structure sent in your request.\n"
            "feature_fields -> array/list (e.g., ['abc', 'def'])\n"
            "label_field -> string (e.g., 'def')\n"
            "hyper_parameters -> dict/object (e.g., { 'epochs': 10 })\n"
            "hyper_parameters: {\n"
            "   epochs -> integer (e.g., 10)\n"
            "   learning_rate -> float (e.g., 0.1)\n"
            "   normalize_inputs -> numeric boolean with value of one of [0, 1]\n"
            "   train_split -> float (e.g., 0.8)\n"
            "   optimizer_type -> string with value of one of ['ADAM', 'SGD']\n"
            "   loss_type -> string with value of one of ['MEAN_SQUARED_ERROR', 'ROOT_MEAN_SQUARED_ERROR', 'MEAN_ABSOLUTE_ERROR']\n"
            "}\n")


# Main entrypoint
def run(master_hostname="localhost", master_port=50051, flask_port=5000):
    print("Running flask server...")
    app.config["MASTER_HOSTNAME"] = master_hostname
    app.config["MASTER_PORT"] = master_port
    app.run(host="0.0.0.0", port=flask_port)  # Entrypoint


@app.route("/model/<model_id>/gis-join/<gis_join>", methods=["GET"])
def get_model(model_id, gis_join):

    # Try to cast request data to proper types and return error if there are any issues
    try:
        get_model_grpc_request: GetModelRequest = GetModelRequest(
            model_id=model_id,
            gis_join=gis_join
        )
    except Exception as err:
        print("try-except exception for casting GET model request values")
        print(err)
        return "There was a problem processing your request. Please check that you have requested a valid model ID and GIS join."

    with grpc.insecure_channel(f"{app.config['MASTER_HOSTNAME']}:{app.config['MASTER_PORT']}") as channel:
        stub: modelservice_pb2_grpc.MasterStub = modelservice_pb2_grpc.MasterStub(channel)

        info(get_model_grpc_request)

        # Submit validation job
        get_model_grpc_response: GetModelResponse = stub.GetModel(get_model_grpc_request)
        info(f"Get Model Response received: {get_model_grpc_response}")

    # SHA1 generation for verifying and validating data received
    # sha1 = hashlib.sha1()
    # sha1.update(get_model_grpc_response.data)
    # info("proxy get_model data SHA1: {0}".format(sha1.hexdigest()))

    response_code: int = HTTPStatus.INTERNAL_SERVER_ERROR if get_model_grpc_response.error_occurred else HTTPStatus.OK
    return get_json_response(get_model_grpc_response), response_code


@app.route("/model", methods=["POST"])
def submit_job():
    request_data_string: str = request.json
    print(f"request_data: {request_data_string}")
    print(f"request.data: {request.data}")

    # Try to cast request data to proper types and return parameter usage error if any are incorrect
    try:
        build_models_grpc_request: BuildModelsRequest = Parse(request.data, BuildModelsRequest())
    except Exception as err:
        print("try-except exception for casting request values")
        print(err)
        return parameter_usage()

    with grpc.insecure_channel(f"{app.config['MASTER_HOSTNAME']}:{app.config['MASTER_PORT']}") as channel:
        stub: modelservice_pb2_grpc.MasterStub = modelservice_pb2_grpc.MasterStub(channel)

        info(build_models_grpc_request)

        # Submit validation job
        build_models_grpc_response: BuildModelsResponse = stub.BuildModels(build_models_grpc_request)
        info(f"Build Models Response received: {build_models_grpc_response}")

    response_code: int = HTTPStatus.INTERNAL_SERVER_ERROR if build_models_grpc_response.error_occurred else HTTPStatus.OK
    return build_json_response(build_models_grpc_response), response_code


def build_json_response(build_models_grpc_response: BuildModelsResponse) -> str:
    return MessageToJson(build_models_grpc_response, preserving_proto_field_name=True)


def get_json_response(get_model_grpc_response: GetModelResponse) -> str:
    return MessageToJson(get_model_grpc_response, preserving_proto_field_name=True)
