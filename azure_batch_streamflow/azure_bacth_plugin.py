import os
from streamflow.ext.plugin import  StreamFlowPlugin
from azure.batch import BatchServiceClient
from azure.identity import DefaultAzureCredential

class AzureBatchPlugin(StreamFlowPlugin):
    def __init__(self, config):
        super().__init__(config)
        self.credential = DefaultAzureCredential()
        self.batch_client = BatchServiceClient(
            credentials=self.credential,
            batch_url=config["batch_account_url"]
        )

    def create_pool(self):
        pool_config = self.config["pool"]
        pool_id = pool_config["id"]
        vm_size = pool_config["vm_size"]
        node_count = pool_config["node_count"]
        os_image = pool_config["os_image"]

        self.batch_client.pool.add({
            'id': pool_id,
            'vm_size': vm_size,
            'virtual_machine_configuration': {
                'image_reference': {
                    'publisher': os_image["publisher"],
                    'offer': os_image["offer"],
                    'sku': os_image["sku"]
                },
                'node_agent_sku_id': 'batch.node.ubuntu 18.04'
            },
            'target_dedicated_nodes': node_count
        })

    def submit_job(self):
        job_config = self.config["job"]
        job_id = job_config["id"]
        pool_id = job_config["pool_id"]

        self.batch_client.job.add({
            'id': job_id,
            'pool_info': {
                'pool_id': pool_id
            }
        })

    def submit_task(self):
        task_config = self.config["task"]
        job_id = self.config["job"]["id"]
        task_id = task_config["id"]
        command_line = task_config["command_line"]

        self.batch_client.task.add(job_id, {
            'id': task_id,
            'command_line': command_line
        })

def create_plugin(config):
    return AzureBatchPlugin(config)
