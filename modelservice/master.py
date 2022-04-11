import grpc
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed
from logging import info, error

from modelservice import modelservice_pb2_grpc
from modelservice.modelservice_pb2 import WorkerRegistrationRequest, WorkerRegistrationResponse, BuildModelsRequest, \
    GetModelRequest, GetModelResponse, BuildModelsResponse


class WorkerMetadata:

    def __init__(self, hostname, port):
        self.hostname = hostname
        self.port = port

    def __repr__(self):
        return f"WorkerMetadata: hostname={self.hostname}, port={self.port}"


# Master Service
class Master(modelservice_pb2_grpc.MasterServicer):

    # def __init__(self, hostname: str = "localhost", port: int = 50051):
    def __init__(self, hostname: str, port: int):
        super(Master, self).__init__()
        self.hostname = hostname
        self.port = port

        # Data structures
        self.tracked_workers = {}       # Mapping of { hostname -> WorkerMetadata }
        self.gis_join_locations = {}    # Mapping of { gis_join -> WorkerMetadata }

    def is_worker_registered(self, hostname):
        return hostname in self.tracked_workers

    def RegisterWorker(self, request: WorkerRegistrationRequest, context):
        info(f"Received request to register worker: hostname={request.hostname}, port={request.port}")

        # Create a WorkerMetadata object for tracking
        worker: WorkerMetadata = WorkerMetadata(request.hostname, request.port)
        info(f"Successfully added Worker: {worker}, responsible for {len(request.local_gis_joins)} GISJOINs")
        # Add worker metadata to tracked_workers map for easy reference later
        self.tracked_workers[request.hostname] = worker

        # Loop through list of GIS joins and store their ID and metadata about worker that is hosting them
        for local_gis_join in request.local_gis_joins:
            info(f"Worker at hostname={request.hostname}, port={request.port} has gis join={local_gis_join.gis_join}")
            self.gis_join_locations[local_gis_join.gis_join] = worker

        return WorkerRegistrationResponse(success=True)

    def DeregisterWorker(self, request, context):
        info(f"Received request to deregister worker: hostname={request.hostname}, port={request.port}")
        return WorkerRegistrationResponse(success=True)

    def BuildModels(self, request: BuildModelsRequest, context):
        info(f"Received request to build models")
        return BuildModelsResponse()

    def GetModels(self, request: GetModelRequest, context):
        info(f"Received request to retrieve model(s)")
        return GetModelResponse()


def run(master_port=50051):

    # Initialize server and master
    server = grpc.server(ThreadPoolExecutor(max_workers=10))
    hostname = socket.gethostname()
    master = Master(hostname, master_port)
    modelservice_pb2_grpc.add_MasterServicer_to_server(master, server)

    # Start the server
    info(f"Starting master server on {hostname}:{master_port}")
    server.add_insecure_port(f"{hostname}:{master_port}")
    server.start()
    server.wait_for_termination()
