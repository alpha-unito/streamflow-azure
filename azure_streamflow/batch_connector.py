from __future__ import annotations

import logging
from streamflow.core.deployment import Connector, ExecutionLocation
from streamflow.core.exception import WorkflowDefinitionException, WorkflowExecutionException
from azure_streamflow.executor import AzureExecutor
from azure_streamflow.config import AzureConfig

class AzureBatchConnector(Connector):
    def __init__(self, config):
        self.config = AzureConfig(config)
        self.executor = AzureExecutor(self.config)
        self.job_id = config["job"]["id"]
        self.task_id = config["task"]["id"]

    async def setup(self, location: ExecutionLocation | None = None):
        logging.info("[AzureBatch] Setting up environment...")
        try:
            pool_cfg = self.config.config["pool"]
            os_image = pool_cfg["os_image"]

            await self.executor.create_pool(
                pool_id=pool_cfg["id"],
                vm_size=pool_cfg["vm_size"],
                node_count=pool_cfg["node_count"],
                publisher=os_image["publisher"],
                offer=os_image["offer"],
                sku=os_image["sku"]
            )

            job_cfg = self.config.config["job"]
            await self.executor.submit_job(job_cfg["id"], job_cfg["pool_id"])
        except Exception as e:
            raise WorkflowExecutionException(f"Failed during setup: {e}") from e

    async def run(self, command: str, location: ExecutionLocation | None = None):
        try:
            task_cfg = self.config.config["task"]
            await self.executor.submit_task(
                job_id=self.job_id,
                task_id=self.task_id,
                command_line=command,
                resource_files=task_cfg.get("resource_files", [])
            )
            return self.task_id
        except Exception as e:
            raise WorkflowExecutionException(f"Failed to submit task: {e}") from e

    async def status(self, task_id: str, location: ExecutionLocation | None = None):
        try:
            state = await self.executor.monitor_job(self.job_id)
            return {"job_id": self.job_id, "task_id": task_id, "state": state}
        except Exception as e:
            raise WorkflowExecutionException(f"Failed to retrieve status: {e}") from e

    async def teardown(self, location: ExecutionLocation | None = None):
        logging.info("[AzureBatch] Tearing down environment...")
        try:
            await self.executor.delete_pool(self.config.config["pool"]["id"])
        except Exception as e:
            raise WorkflowExecutionException(f"Failed during teardown: {e}") from e

    async def close(self):
        try:
            await self.executor.batch_client.close()
            await self.executor.credentials.close()
        except Exception as e:
            raise WorkflowExecutionException(f"Failed to close resources: {e}") from e