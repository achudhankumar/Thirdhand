"""Trusted worker context, independent of unverified HTTP identity."""

from contextvars import ContextVar
from dataclasses import dataclass


@dataclass
class JobContext:
    inbox: object
    job_id: str
    lease_token: str
    sender: str
    customer_time: float
    sequence: int = 0


current_job: ContextVar[JobContext | None] = ContextVar("thirdhand_job", default=None)


async def assert_active():
    job = current_job.get()
    if job is not None:
        await job.inbox.check_lease(job.job_id, job.lease_token)
