import os

class AzureConfig:
    def __init__(self, config: dict):
        self.batch_account_url = config.get("batch_account_url") or os.environ.get("AZURE_BATCH_ACCOUNT_URL")
        self.client_id = config.get("client_id") or os.environ.get("AZURE_CLIENT_ID")
        self.client_secret = config.get("client_secret") or os.environ.get("AZURE_CLIENT_SECRET")
        self.tenant_id = config.get("tenant_id") or os.environ.get("AZURE_TENANT_ID")

        self.validate()

    def validate(self):
        missing = []
        if not self.batch_account_url:
            missing.append("batch_account_url")
        if not self.client_id:
            missing.append("client_id")
        if not self.client_secret:
            missing.append("client_secret")
        if not self.tenant_id:
            missing.append("tenant_id")
        if missing:
            raise ValueError(f"Missing configuration values: {', '.join(missing)}")

    def as_dict(self):
        return {
            "batch_account_url": self.batch_account_url,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "tenant_id": self.tenant_id,
        }

    def __str__(self):
        return (
            f"AzureBatchConfig("
            f"batch_account_url={self.batch_account_url}, "
            f"client_id={self.client_id}, "
            f"tenant_id={self.tenant_id})"
        )
