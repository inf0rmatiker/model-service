import grpc
import socket
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from logging import info, error

from modelservice import modelservice_pb2_grpc
from modelservice.modelservice_pb2 import BudgetType, WorkerRegistrationRequest, WorkerRegistrationResponse, BuildModelsRequest, \
    GetModelRequest, GetModelResponse, BuildModelsResponse


class JobMetadata:

    def __init__(self, job_id: str, gis_joins: list):
        self.job_id = job_id
        self.worker_jobs = {}  # Mapping of { worker_hostname -> WorkerJobMetadata }
        self.status = "NEW"

class WorkerJobMetadata:

    def __init__(self, job_id, worker_ref):
        self.job_id = job_id
        self.worker = worker_ref
        self.status = "NEW"

    def complete(self):
        self.status = "DONE"

    def __repr__(self):
        return f"WorkerJobMetadata: job_id={self.job_id}, worker={self.worker.hostname}, status={self.status}, "

class WorkerMetadata:

    def __init__(self, hostname, port):
        self.hostname = hostname
        self.port = port

    def __repr__(self):
        return f"WorkerMetadata: hostname={self.hostname}, port={self.port}"

def get_or_create_worker_job(worker: WorkerMetadata, job_id: str) -> WorkerJobMetadata:
    if job_id not in worker.jobs:
        info(f"Creating job for worker={worker.hostname}, job={job_id}")
        worker.jobs[job_id] = WorkerJobMetadata(job_id, worker)
    return worker.jobs[job_id]

def generate_job_id() -> str:
    return uuid.uuid4().hex

# Launches a round of worker jobs based on the master job mode selected.
# Returns a list of WorkerValidationJobResponse objects.
def launch_worker_jobs(request: BuildModelsRequest, job: JobMetadata) -> list:
    # Define async function to launch worker job
    async def run_worker_job(_worker_job: WorkerJobMetadata, _request: BuildModelsRequest) -> BuildModelsResponses:
        info("Launching async run_worker_job()...")
        _worker = _worker_job.worker
        async with grpc.aio.insecure_channel(f"{_worker.hostname}:{_worker.port}") as channel:
            stub = validation_pb2_grpc.WorkerStub(channel)
            request_copy = BuildModelsRequest()
            request_copy.CopyFrom(_request)
            request_copy.id = _worker_job.job_id

            return await stub.BuildModels(request_copy)

    # Iterate over all the worker jobs created for this job and create asyncio tasks for them
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    tasks = []
    for worker_hostname, worker_job in job.worker_jobs.items():
        tasks.append(loop.create_task(run_worker_job(worker_job, request)))

    task_group = asyncio.gather(*tasks)
    responses = loop.run_until_complete(task_group)
    loop.close()

    return list(responses)

# Master Service
class Master(modelservice_pb2_grpc.MasterServicer):

    def __init__(self, hostname: str, port: int):
        super(Master, self).__init__()
        self.hostname = hostname
        self.port = port

        # Data structures
        self.tracked_workers = {}       # Mapping of { hostname -> WorkerMetadata }
        self.gis_join_locations = {}    # Mapping of { gis_join -> WorkerMetadata }

    # Generates a JobMetadata object from the set of GISJOIN allocations
    def create_job(self) -> JobMetadata:

        job_id: str = generate_job_id()  # Random UUID for the job
        job: JobMetadata = JobMetadata(job_id)
        info(f"Created job id {job_id}")

        # Add all tracked workers to job
        for worker in self.tracked_workers:
            # Found a registered worker for this GISJOIN, get or create a job for it, and update jobs map
            worker_job: WorkerJobMetadata = get_or_create_worker_job(worker, job_id)
            # worker_job.gis_joins.append(spatial_allocation)
            job.worker_jobs[worker.hostname] = worker_job

        return job

    def is_worker_registered(self, hostname):
        return hostname in self.tracked_workers

    # Processes a job and returns a list of WorkerValidationJobResponse objects.
    def process_job(self, request: BuildModelsRequest) -> (str, list):

        # Create and launch a job from allocations
        job: JobMetadata = self.create_job()
        return job.job_id, launch_worker_jobs(request, job)

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

        if self.is_worker_registered(request.hostname):
            info(f"Worker {request.hostname} is registered. Removing...")
            del self.tracked_workers[request.hostname]
            info(f"Worker {request.hostname} is now deregistered and removed.")
            return WorkerRegistrationResponse(success=True)
        else:
            error(f"Worker {request.hostname} is not registered, can't remove")
            return WorkerRegistrationResponse(success=False)

    def BuildModels(self, request: BuildModelsRequest, context):
        info(f"Received request to build models")

        # Time the entire job from start to finish
        profiler: Timer = Timer()
        profiler.start()

        job_id, worker_responses = self.process_job(request)

        errors = []
        ok = True

        if len(worker_responses) == 0:
            error_msg = "Did not receive any responses from workers"
            ok = False
            error(error_msg)
            errors.append(error_msg)
        else:
            for worker_response in worker_responses:
                if not worker_response.ok:
                    ok = False
                    error_msg = f"{worker_response.hostname} error: {worker_response.error_msg}"
                    errors.append(error_msg)

        error_msg = f"errors: {errors}"
        profiler.stop()

        return BuildModelsResponse(
            id=job_id,
            ok=ok,
            error_msg=error_msg,
            duration_sec=profiler.elapsed,
            worker_responses=worker_responses
        )

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
