from __future__ import annotations

import asyncio
import logging
from uuid import uuid4

from app.observability import capture_exception, get_tracer, observe_job


class JobRunner:
    def __init__(self, repository, integration_manager, poll_interval_ms: int = 1000) -> None:
        self.repository = repository
        self.integration_manager = integration_manager
        self.poll_interval_ms = poll_interval_ms
        self.worker_id = str(uuid4())[:8]
        self.logger = logging.getLogger("relayops.worker")
        self.tracer = get_tracer()

    async def process_pending_jobs(self, run_id: str) -> None:
        while True:
            job = self.repository.claim_next_job(run_id, self.worker_id)
            if not job:
                self.repository.finalize_run_status(run_id)
                return

            run = self.repository.get_run(run_id)
            if not run:
                self.repository.fail_job(job.id, "Workflow run no longer exists.", retry_delay_seconds=0)
                observe_job(job.provider, "failed")
                return

            try:
                with self.tracer.start_as_current_span(f"job.{job.provider}") as span:
                    span.set_attribute("relayops.run_id", run_id)
                    span.set_attribute("relayops.provider", job.provider)
                    updated_run = await self.integration_manager.process_provider(job.provider, run)
                self.repository.save_run(updated_run)
                self.repository.complete_job(job.id, "completed", f"{job.provider} job processed by {self.worker_id}.")
                observe_job(job.provider, "completed")
            except Exception as exc:  # pragma: no cover - defensive path
                capture_exception(exc)
                self.logger.exception("job_processing_failed run_id=%s provider=%s", run_id, job.provider)
                self.repository.fail_job(job.id, f"{job.provider} job failed: {exc}")
                observe_job(job.provider, "failed")

    async def run_forever(self) -> None:
        while True:
            self.repository.purge_expired_sessions()
            for run_id in self.repository.list_pending_run_ids():
                await self.process_pending_jobs(run_id)
            await asyncio.sleep(self.poll_interval_ms / 1000)
