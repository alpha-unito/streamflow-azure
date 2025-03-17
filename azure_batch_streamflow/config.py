import os

class AzureBatchConfig:
    def __init__(self, config):
        self.batch_account_url = config.get('batch_account_url', os.getenv('AZURE_BATCH_ACCOUNT_URL'))
        self.client_id = config.get('client_id', os.getenv('AZURE_CLIENT_ID'))
        self.client_secret = config.get('client_secret', os.getenv('AZURE_CLIENT_SECRET'))
        self.tenant_id = config.get('tenant_id', os.getenv('AZURE_TENANT_ID'))

        if not all([self.batch_account_url, self.client_id, self.client_secret, self.tenant_id]):
            raise ValueError("Missing Azure Batch or authentication configuration.")

    def validate(self):
        if not self.batch_account_url:
            raise ValueError("The Azure Batch account URL must be provided.")
        if not self.client_id:
            raise ValueError("The Azure Client ID must be provided.")
        if not self.client_secret:
            raise ValueError("The Azure Client Secret must be provided.")
        if not self.tenant_id:
            raise ValueError("The Azure Tenant ID must be provided.")

    def __str__(self):
        return f"AzureBatchConfig(batch_account_url={self.batch_account_url}, client_id={self.client_id}, tenant_id={self.tenant_id})"
