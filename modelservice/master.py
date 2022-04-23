import asyncio
import grpc
import socket
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from logging import info, error

from modelservice import modelservice_pb2_grpc
from modelservice.modelservice_pb2 import WorkerRegistrationRequest, WorkerRegistrationResponse, BuildModelsRequest, \
    GetModelRequest, GetModelResponse, BuildModelsResponse, WorkerBuildModelsResponse


class WorkerMetadata:

    def __init__(self, hostname, port):
        self.hostname = hostname
        self.port = port
        self.gis_joins = []

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

    def is_worker_registered(self, hostname: str) -> bool:
        return hostname in self.tracked_workers

    def RegisterWorker(self, request: WorkerRegistrationRequest, context) -> WorkerRegistrationResponse:
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
            worker.gis_joins.append(local_gis_join.gis_join)

        return WorkerRegistrationResponse(success=True)

    def DeregisterWorker(self, request: WorkerRegistrationRequest, context) -> WorkerRegistrationResponse:
        info(f"Received request to deregister worker: hostname={request.hostname}, port={request.port}")

        if self.is_worker_registered(request.hostname):
            info(f"Worker {request.hostname} is registered. Removing...")
            del self.tracked_workers[request.hostname]
            info(f"Worker {request.hostname} is now deregistered and removed.")
            return WorkerRegistrationResponse(success=True)
        else:
            error(f"Worker {request.hostname} is not registered, can't remove")
            return WorkerRegistrationResponse(success=False)

    def BuildModels(self, request: BuildModelsRequest, context) -> BuildModelsResponse:
        info(f"Received request to build models: {request}")

        # Generate and set unique job ID
        job_id: str = generate_job_id()
        request.id = job_id

        known_workers: list = list(self.tracked_workers.values())
        worker_responses: list = submit_worker_jobs(known_workers, request)

        info(f"Jobs completed, returning results")
        return BuildModelsResponse(
            id=job_id,
            duration_sec=0.0,       # TODO: Add actual job profile
            error_occurred=False,   # TODO: Check for errors
            error_msg="",
            worker_responses=worker_responses
        )

    def GetModel(self, request: GetModelRequest, context) -> GetModelResponse:
        info(f"Received request to retrieve model(s)")
        return GetModelResponse()


def generate_job_id() -> str:
    return uuid.uuid4().hex


# Asynchronously submits Worker jobs, and returns a list(WorkerBuildModelsResponse)
def submit_worker_jobs(workers: list, request: BuildModelsRequest) -> list:
    info(f"Submitting jobs to {len(workers)} Workers")

    # Define async function for launching a BuildModels job on a Worker gRPC stub
    async def run_worker_job(_worker: WorkerMetadata, _request: BuildModelsRequest) -> WorkerBuildModelsResponse:
        info(f"Launching async submit_worker_jobs() for {_worker.hostname}...")
        async with grpc.aio.insecure_channel(f"{_worker.hostname}:{_worker.port}") as channel:
            stub = modelservice_pb2_grpc.WorkerStub(channel)
            request_copy = BuildModelsRequest()
            request_copy.CopyFrom(_request)
            request_copy.gis_joins.extend(_worker.gis_joins)
            return await stub.BuildModels(request_copy)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    tasks: list = []  # list of concurrent.Futures
    for worker in workers:
        tasks.append(
            loop.create_task(
                run_worker_job(worker, request)
            )
        )

    task_group = asyncio.gather(*tasks)
    responses = loop.run_until_complete(task_group)
    loop.close()  # Clean up event loop we created earlier
    return list(responses)


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
