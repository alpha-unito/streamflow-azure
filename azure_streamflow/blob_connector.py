from __future__ import annotations

import logging
import ssl
import aiofiles

from importlib_resources import files

from streamflow.core.deployment import Connector, ExecutionLocation
from streamflow.core.exception import WorkflowExecutionException

from azure.storage.blob.aio import BlobServiceClient
from azure.identity.aio import DefaultAzureCredential, CertificateCredential
from azure.core.pipeline.transport import AioHttpTransport  


class AzureBlobConnector(Connector):
    def __init__(self, deployment_name: str | None = None, **config):
        self.deployment_name = deployment_name
        self.config = config
        self.blob_service_client: BlobServiceClient | None = None
        self.credential: DefaultAzureCredential | CertificateCredential | None = None
        self.transport: AioHttpTransport | None = None  

    @classmethod
    def get_schema(cls) -> str:
        return files("azure_streamflow.schemas").joinpath("azure_blob.json").read_text("utf-8")

    async def get_stream_writer(self, local_path: str):
        async with aiofiles.open(local_path, "wb") as f:
            yield f

    # ---------------------------
    # CREAZIONE CREDENZIALE
    # ---------------------------
    def _create_credential(self):
        auth_mode = self.config.get("auth_mode", "default")

        if auth_mode == "certificate":
            tenant_id = self.config["tenant_id"]
            client_id = self.config["client_id"]
            cert_path = self.config["certificate_path"]

            return CertificateCredential(
                tenant_id=tenant_id,
                client_id=client_id,
                certificate_path=cert_path
            )

        # fallback: comportamento attuale
        return DefaultAzureCredential()

    # ---------------------------
    # CREAZIONE TRANSPORT (CA PATH)
    # ---------------------------
    def _create_transport(self) -> AioHttpTransport | None:
        """
        Crea un transport condiviso per tutte le richieste HTTP del BlobServiceClient.

        Usa 'certificate_ca_path' dal config per impostare la CA custom:
          - crea un SSLContext con quella CA
          - lo passa ad AioHttpTransport tramite 'connection_verify'
        """
        ca_path = self.config.get("certificate_ca_path")

        # Se non c'è una CA custom, lascia che il client usi il default
        if not ca_path:
            return None

        # Crea un contesto SSL personalizzato come nel tuo esempio
        context = ssl.create_default_context(cafile=ca_path)

        # Nel mondo async usiamo AioHttpTransport, che accetta direttamente
        # il path o un SSLContext in 'connection_verify'
        transport = AioHttpTransport(
            connection_verify=context
        )
        logging.info("[AzureBlob] Created custom AioHttpTransport with CA path %s", ca_path)
        return transport

    # ---------------------------
    # LIFECYCLE
    # ---------------------------
    async def setup(self, location: ExecutionLocation | None = None):
        logging.info("[AzureBlob] Setting up Blob client...")
        try:
            self.credential = self._create_credential()
            self.transport = self._create_transport()

            kwargs = {}
            if self.transport is not None:
                kwargs["transport"] = self.transport

            self.blob_service_client = BlobServiceClient(
                account_url=self.config["blob_account_url"],
                credential=self.credential,
                **kwargs,
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
        # Le operazioni Blob sono tipicamente sincrone lato servizio
        return {"task_id": task_id, "state": "completed"}

    async def teardown(self, location: ExecutionLocation | None = None):
        # Nessuna azione specifica, le connessioni vengono chiuse in close()
        pass

    async def close(self):
        try:
            if self.blob_service_client:
                await self.blob_service_client.close()
            if self.credential:
                await self.credential.close()
            if self.transport:
                await self.transport.close()
        except Exception as e:
            raise WorkflowExecutionException(f"Failed to close resources: {e}") from e

    # ---------------------------
    # OPERAZIONI BLOB
    # ---------------------------
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

    # ---------------------------
    # METODI ASTRATTI STREAMFLOW (STUB)
    # ---------------------------
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

    async def get_available_locations(self, service: str | None = None, **kwargs) -> dict:
        return {}

    async def get_stream_reader(self, location: ExecutionLocation, command: list[str]):
        return None
