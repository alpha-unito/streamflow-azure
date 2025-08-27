import logging
from azure.batch.aio import BatchClient
from azure.identity.aio import DefaultAzureCredential


class AzureExecutor:
    def __init__(self, config):
        self.config = config
        self.credentials: DefaultAzureCredential | None = None
        self.batch_client: BatchClient | None = None

    async def initialize(self):
        self.credentials = DefaultAzureCredential()
        self.batch_client = BatchClient(
            endpoint=self.config.batch_account_url,  # <-- CORRETTO QUI
            credential=self.credentials
        )
        logging.info(f"[AzureExecutor] Initialized with endpoint: {self.config.batch_account_url}")

    async def create_pool(self, pool_id, vm_size, node_count, publisher, offer, sku):
        logging.info(f"[AzureExecutor] Creating pool {pool_id}")
        await self.batch_client.pool.add({
            'id': pool_id,
            'vm_size': vm_size,
            'virtual_machine_configuration': {
                'image_reference': {
                    'publisher': publisher,
                    'offer': offer,
                    'sku': sku
                },
                'node_agent_sku_id': 'batch.node.ubuntu 18.04'
            },
            'target_dedicated_nodes': node_count
        })
        logging.info(f"[AzureExecutor] Pool {pool_id} created successfully")

    async def submit_job(self, job_id, pool_id):
        logging.info(f"[AzureExecutor] Submitting job {job_id} to pool {pool_id}")
        await self.batch_client.job.add({
            'id': job_id,
            'pool_info': {
                'pool_id': pool_id
            }
        })
        logging.info(f"[AzureExecutor] Job {job_id} submitted successfully")

    async def submit_task(self, job_id, task_id, command_line, resource_files=None):
        logging.info(f"[AzureExecutor] Submitting task {task_id} to job {job_id}")
        task = {
            'id': task_id,
            'command_line': command_line,
        }

        if resource_files:
            task['resource_files'] = resource_files

        await self.batch_client.task.add(job_id, task)
        logging.info(f"[AzureExecutor] Task {task_id} submitted successfully")

    async def monitor_job(self, job_id):
        logging.info(f"[AzureExecutor] Monitoring job: {job_id}")
        job_status = await self.batch_client.job.get(job_id)
        logging.info(f"[AzureExecutor] Job {job_id} status: {job_status.state}")
        return job_status.state

    async def delete_pool(self, pool_id):
        logging.info(f"[AzureExecutor] Deleting pool: {pool_id}")
        await self.batch_client.pool.delete(pool_id)
        logging.info(f"[AzureExecutor] Pool {pool_id} deleted successfully")

    async def close(self):
        logging.info("[AzureExecutor] Closing resources...")
        if self.batch_client:
            await self.batch_client.close()
        if self.credentials:
            await self.credentials.close()
