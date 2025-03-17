import logging
from azure.batch import BatchServiceClient
from msrestazure.azure_active_directory import ServicePrincipalCredentials

class AzureBatchExecutor:
    def __init__(self, config):
        self.config = config
        self.credentials = ServicePrincipalCredentials(
            client_id=config.client_id,
            secret=config.client_secret,
            tenant_id=config.tenant_id
        )
        self.batch_client = BatchServiceClient(
            credentials=self.credentials,
            batch_url=config.batch_account_url
        )
        logging.info(f"Azure Batch Executor initialized with account URL: {config.batch_account_url}")

    def create_pool(self, pool_id, vm_size, node_count, publisher, offer, sku):
        logging.info(f"Creating pool with ID: {pool_id}")
        pool = self.batch_client.pool.add({
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
        logging.info(f"Pool {pool_id} created successfully")
        return pool

    def submit_job(self, job_id, pool_id):
        logging.info(f"Submitting job with ID: {job_id} to pool: {pool_id}")
        job = self.batch_client.job.add({
            'id': job_id,
            'pool_info': {
                'pool_id': pool_id
            }
        })
        logging.info(f"Job {job_id} submitted successfully")
        return job

    def submit_task(self, job_id, task_id, command_line, resource_files=None):
        logging.info(f"Submitting task with ID: {task_id} to job: {job_id}")
        task = {
            'id': task_id,
            'command_line': command_line,
        }

        if resource_files:
            task['resource_files'] = resource_files

        self.batch_client.task.add(job_id, task)
        logging.info(f"Task {task_id} submitted successfully")

    def monitor_job(self, job_id):
        logging.info(f"Monitoring job: {job_id}")
        # Implementazione di base per il monitoraggio del job
        job_status = self.batch_client.job.get(job_id)
        logging.info(f"Job {job_id} status: {job_status.state}")
        return job_status.state

    def delete_pool(self, pool_id):
        logging.info(f"Deleting pool with ID: {pool_id}")
        self.batch_client.pool.delete(pool_id)
        logging.info(f"Pool {pool_id} deleted successfully")
