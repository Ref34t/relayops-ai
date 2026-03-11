from __future__ import annotations

import asyncio

from app.config import get_settings
from app.integrations import IntegrationManager
from app.jobs import JobRunner
from app.logging import configure_logging
from app.observability import setup_observability
from app.repository import WorkflowRepository


async def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_format)
    setup_observability(settings)
    repository = WorkflowRepository(settings.database_path, settings.demo_api_key, settings.demo_email, settings.demo_password)
    integration_manager = IntegrationManager(settings)
    runner = JobRunner(repository, integration_manager, settings.worker_poll_interval_ms)
    await runner.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
