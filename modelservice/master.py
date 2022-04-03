import grpc
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed
from logging import info, error

from modelservice import modelservice_pb2_grpc
from modelservice.modelservice_pb2 import WorkerRegistrationRequest, WorkerRegistrationResponse, BuildModelsRequest, \
    GetModelsRequest, GetModelsResponse, BuildModelsResponse


# Master Service
class Master(modelservice_pb2_grpc.MasterServicer):

    def __init__(self):
        super(Master, self).__init__()

    def RegisterWorker(self, request: WorkerRegistrationRequest, context):
        info(f"Received request to register worker: hostname={request.hostname}, port={request.port}")
        return WorkerRegistrationResponse(success=True)

    def DeregisterWorker(self, request, context):
        info(f"Received request to deregister worker: hostname={request.hostname}, port={request.port}")
        return WorkerRegistrationResponse(success=True)

    def BuildModels(self, request: BuildModelsRequest, context):
        info(f"Received request to build models")
        return BuildModelsResponse()

    def GetModels(self, request: GetModelsRequest, context):
        info(f"Received request to retrieve model(s)")
        return GetModelsResponse()


def run(master_port=50051):

    # Initialize server and master
    server = grpc.server(ThreadPoolExecutor(max_workers=10))
    master = Master()
    modelservice_pb2_grpc.add_MasterServicer_to_server(master, server)
    hostname = socket.gethostname()

    # Start the server
    info(f"Starting master server on {hostname}:{master_port}")
    server.add_insecure_port(f"{hostname}:{master_port}")
    server.start()
    server.wait_for_termination()
