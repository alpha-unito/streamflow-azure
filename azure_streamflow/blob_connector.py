from __future__ import annotations

import logging
import aiofiles
from importlib_resources import files
from streamflow.core.deployment import Connector, ExecutionLocation
from streamflow.core.exception import WorkflowExecutionException
from azure.storage.blob.aio import BlobServiceClient
from azure.identity.aio import DefaultAzureCredential

class AzureBlobConnector(Connector):
    def __init__(self, config):
        self.config = config
        self.blob_service_client: BlobServiceClient | None = None
        self.credential: DefaultAzureCredential | None = None

    @classmethod
    def get_schema(cls) -> str:
        return files("azure_streamflow.schemas").joinpath("azure_blob.schema.json").read_text("utf-8")

    async def setup(self, location: ExecutionLocation | None = None):
        logging.info("[AzureBlob] Setting up Blob client...")
        try:
            self.credential = DefaultAzureCredential()
            self.blob_service_client = BlobServiceClient(
                account_url=self.config["blob_account_url"],
                credential=self.credential
            )
        except Exception as e:
            raise WorkflowExecutionException(f"Failed to initialize Azure Blob Storage: {e}") from e

    async def run(self, command: str, location: ExecutionLocation | None = None):
        try:
            action = self.config.get("action")
            container = self.config["container"]
            blob_name = self.config["blob_name"]

            if action == "upload":
                local_path = self.config["local_path"]
                await self._upload_blob(local_path, container, blob_name)
                return f"{action} completed"
            elif action == "download":
                local_path = self.config["local_path"]
                await self._download_blob(container, blob_name, local_path)
                return f"{action} completed"
            elif action == "read":
                encoding = self.config.get("encoding", "utf-8")
                content = await self._read_blob(container, blob_name, encoding)
                return content
            else:
                raise WorkflowExecutionException(f"Invalid blob action: {action}")
        except Exception as e:
            raise WorkflowExecutionException(f"Failed to perform blob action: {e}") from e

    async def status(self, task_id: str, location: ExecutionLocation | None = None):
        return {"task_id": task_id, "state": "completed"}  # Blob ops are immediate

    async def teardown(self, location: ExecutionLocation | None = None):
        pass

    async def close(self):
        try:
            if self.blob_service_client:
                await self.blob_service_client.close()
            if self.credential:
                await self.credential.close()
        except Exception as e:
            raise WorkflowExecutionException(f"Failed to close resources: {e}") from e

    async def _upload_blob(self, local_path: str, container: str, blob_name: str):
        try:
            blob_client = self.blob_service_client.get_blob_client(container=container, blob=blob_name)
            async with aiofiles.open(local_path, "rb") as f:
                data = await f.read()
                await blob_client.upload_blob(data, overwrite=True)
            logging.info(f"Uploaded {local_path} to {container}/{blob_name}")
        except Exception as e:
            raise WorkflowExecutionException(f"Upload failed: {e}") from e

    async def _download_blob(self, container: str, blob_name: str, local_path: str):
        try:
            blob_client = self.blob_service_client.get_blob_client(container=container, blob=blob_name)
            stream = await blob_client.download_blob()
            data = await stream.readall()
            async with aiofiles.open(local_path, "wb") as f:
                await f.write(data)
            logging.info(f"Downloaded {container}/{blob_name} to {local_path}")
        except Exception as e:
            raise WorkflowExecutionException(f"Download failed: {e}") from e

    async def _read_blob(self, container: str, blob_name: str, encoding: str = "utf-8") -> str:
        try:
            blob_client = self.blob_service_client.get_blob_client(container=container, blob=blob_name)
            stream = await blob_client.download_blob()
            data = await stream.readall()
            text = data.decode(encoding)
            logging.info(f"Read {container}/{blob_name} with encoding={encoding}")
            return text
        except Exception as e:
            raise WorkflowExecutionException(f"Read failed: {e}") from e

    # Required abstract methods with stub implementations
    async def deploy(self, external: bool) -> None:
        pass

    async def undeploy(self, external: bool) -> None:
        pass

    async def copy_local_to_remote(self, source: str, destination: str, location: ExecutionLocation) -> None:
        pass

    async def copy_remote_to_local(self, source: str, destination: str, location: ExecutionLocation) -> None:
        pass

    async def copy_remote_to_remote(self, source: str, destination: str, location: ExecutionLocation) -> None:
        pass

    async def get_available_locations(self) -> dict:
        return {}

    async def get_stream_reader(self, location: ExecutionLocation, command: list[str]):
        return None
