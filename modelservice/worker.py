import socket
import grpc
import signal

from modelservice import modelservice_pb2_grpc
from concurrent.futures import ThreadPoolExecutor, as_completed
from logging import info

from modelservice.modelservice_pb2 import BuildModelsRequest, BuildModelsResponse, GetModelsRequest, GetModelsResponse


class Worker(modelservice_pb2_grpc.WorkerServicer):

    def __init__(self, master_hostname: str, master_port: int, hostname: str, port: int):
        super(Worker, self).__init__()
        self.master_hostname = master_hostname
        self.master_port = master_port
        self.hostname = hostname
        self.port = port

    def deregister(self):
        info("Deregistering...")  # TODO

    def BuildModels(self, request: BuildModelsRequest, context):
        info(f"Received request to build models")
        return BuildModelsResponse()

    def GetModels(self, request: GetModelsRequest, context):
        info(f"Received request to retrieve model(s)")
        return GetModelsResponse()


def shutdown_gracefully(worker: Worker) -> None:
    worker.deregister()
    exit(0)


def run(master_hostname="localhost", master_port=50051, worker_port=50055) -> None:

    # Initialize server and worker
    server = grpc.server(ThreadPoolExecutor(max_workers=10))
    hostname = socket.gethostname()
    worker = Worker(master_hostname, master_port, hostname, worker_port)

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
