from __future__ import annotations

import asyncio

from app.models import WorkflowRun


class JobRunner:
    def __init__(self, repository, integration_manager, poll_interval_ms: int = 1000) -> None:
        self.repository = repository
        self.integration_manager = integration_manager
        self.poll_interval_ms = poll_interval_ms

    async def process_pending_jobs(self, run_id: str) -> None:
        while True:
            job = self.repository.claim_next_job(run_id)
            if not job:
                self.repository.finalize_run_status(run_id)
                return

            run = self.repository.get_run(run_id)
            if not run:
                self.repository.complete_job(job.id, "failed", "Workflow run no longer exists.")
                return

            updated_run = await self.integration_manager.process_provider(job.provider, run)
            self.repository.save_run(updated_run)
            self.repository.complete_job(job.id, "completed", f"{job.provider} job processed.")

    async def run_forever(self) -> None:
        while True:
            run_ids = self.repository.list_pending_run_ids()
            for run_id in run_ids:
                await self.process_pending_jobs(run_id)
            await asyncio.sleep(self.poll_interval_ms / 1000)
