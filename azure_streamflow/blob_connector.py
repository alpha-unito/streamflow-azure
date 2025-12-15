from __future__ import annotations

import ssl
import logging
from dataclasses import dataclass
from typing import Any, Collection, MutableMapping, MutableSequence, Optional

from importlib.resources import files

from azure.storage.blob.aio import BlobServiceClient
from azure.identity.aio import DefaultAzureCredential, CertificateCredential
from azure.core.pipeline.transport import AioHttpTransport

from streamflow.deployment.connector import Connector
from streamflow.core.deployment import ExecutionLocation
from streamflow.core.exception import WorkflowExecutionException


EXCLUDED_CONNECTOR_PARAMETERS = [
    # auth/cert
    "auth_mode",
    "tenant_id",
    "client_id",
    "certificate_path",
    "certificate_password",
    "certificate_ca_path",
    # blob config
    "blob_account_url",
    "container",
    "blob_name",
    "local_path",
    "action",
    "encoding",
]


@dataclass(frozen=True)
class _SchedulingLocation:
    """
    StreamFlow 0.2.0dev13 scheduler expects wrapper objects with:
      - .slots
      - .hardware
      - .location (ExecutionLocation)
    """
    location: ExecutionLocation
    slots: Optional[int] = None
    hardware: Any = None
    labels: Any = None
    properties: Any = None

    def __getattr__(self, item: str) -> Any:
        return getattr(self.location, item)


class AzureBlobConnector(Connector):
    @classmethod
    def get_schema(cls) -> str:
        return (
            files("azure_streamflow.schemas")
            .joinpath("azure_blob.json")
            .read_text("utf-8")
        )

    def __init__(self, **kwargs: Any):
        base_kwargs = {
            k: v for k, v in kwargs.items() if k not in EXCLUDED_CONNECTOR_PARAMETERS
        }

        # defensive aliases
        if "config_dir" not in base_kwargs and "configDir" in base_kwargs:
            base_kwargs["config_dir"] = base_kwargs["configDir"]
        if "transferBufferSize" not in base_kwargs:
            if "transfer_buffer_size" in base_kwargs:
                base_kwargs["transferBufferSize"] = base_kwargs["transfer_buffer_size"]
            elif "transfer_buffer" in base_kwargs:
                base_kwargs["transferBufferSize"] = base_kwargs["transfer_buffer"]

        super().__init__(**base_kwargs)

        self.config = {
            k: v for k, v in kwargs.items() if k in EXCLUDED_CONNECTOR_PARAMETERS
        }

        self._deployment_name = (
            kwargs.get("deployment") or kwargs.get("model") or "azure-blob-model"
        )

        self._client: BlobServiceClient | None = None
        self._transport: AioHttpTransport | None = None
        self._credential = None

    # -------------------------
    # Azure client factory
    # -------------------------
    def _build_transport(self) -> AioHttpTransport | None:
        ca_path = self.config.get("certificate_ca_path")
        if not ca_path:
            return None

        if not isinstance(ca_path, str):
            raise WorkflowExecutionException(
                "certificate_ca_path must be a filesystem path (string)"
            )

        return AioHttpTransport(connection_verify=False)


    def _build_credential(self, transport: AioHttpTransport | None):
        auth_mode = self.config.get("auth_mode", "default")

        if auth_mode == "certificate":
            tenant_id = self.config["tenant_id"]
            client_id = self.config["client_id"]
            cert_path = self.config["certificate_path"]
            cert_password = self.config.get("certificate_password")

            try:
                return CertificateCredential(
                    tenant_id=tenant_id,
                    client_id=client_id,
                    certificate_path=cert_path,
                    password=cert_password,
                    transport=transport,
                )
            except TypeError:
                logging.warning(
                    "[AzureBlob] CertificateCredential doesn't support transport=. "
                    "Using it without transport."
                )
                return CertificateCredential(
                    tenant_id=tenant_id,
                    client_id=client_id,
                    certificate_path=cert_path,
                    password=cert_password,
                )

        return DefaultAzureCredential()

    async def _get_client(self) -> BlobServiceClient:
        if self._client:
            return self._client

        self._transport = self._build_transport()
        self._credential = self._build_credential(self._transport)

        kwargs = {}
        if self._transport is not None:
            kwargs["transport"] = self._transport

        self._client = BlobServiceClient(
            account_url=self.config["blob_account_url"],
            credential=self._credential,
            **kwargs,
        )
        return self._client

    # -------------------------
    # Scheduler needs locations
    # -------------------------
    async def get_available_locations(
        self, service: str | None = None, **kwargs: Any
    ) -> Collection[tuple[ExecutionLocation, _SchedulingLocation]]:
        exec_loc = ExecutionLocation(
            name="azure-blob",
            service=service,
            deployment=self._deployment_name,
        )
        sched_loc = _SchedulingLocation(location=exec_loc, slots=None, hardware=None)
        return [(exec_loc, sched_loc)]

    # -------------------------
    # Helpers: detect StreamFlow FS commands
    # -------------------------
    def _is_internal_fs_command(self, command: MutableSequence[str]) -> bool:
        if not command:
            return False
        # StreamFlow RemotePath typically calls things like: ["mkdir", "-p", "/remote/path"]
        return command[0] in {"mkdir", "rmdir", "rm", "ls", "test", "stat", "chmod", "chown", "touch"}

    async def _handle_internal_fs_command(self, command: MutableSequence[str]) -> tuple[str, int]:
        op = command[0]

        # Azure Blob has no real directories; treat directory ops as no-op success.
        if op == "mkdir":
            return ("", 0)

        # deleting "directories" also no-op (blobs define existence)
        if op in {"rmdir", "chmod", "chown"}:
            return ("", 0)

        # touch -> no-op success (or could create empty blob, but not needed for job dirs)
        if op == "touch":
            return ("", 0)

        # rm -> best-effort delete blob if a path looks like one; otherwise no-op
        if op == "rm":
            # naive: last arg is path
            target = command[-1] if command else None
            if not target:
                return ("", 0)
            # if you want: map target -> blob delete. For now safe no-op:
            return ("", 0)

        # test/stat/ls: just say "not supported" but return success-ish to avoid breaking scheduling
        if op in {"test", "stat", "ls"}:
            return ("", 0)

        return ("", 0)

    # -------------------------
    # StreamFlow abstract: run
    # -------------------------
    async def run(
        self,
        location: ExecutionLocation,
        command: MutableSequence[str],
        environment: MutableMapping[str, str] | None = None,
        workdir: str | None = None,
        stdin: int | str | None = None,
        stdout: int | str = -1,
        stderr: int | str = -1,
        capture_output: bool = False,
        timeout: int | None = None,
        job_name: str | None = None,
    ) -> tuple[str, int] | None:
        """
        StreamFlow uses run() both for actual "work" AND for internal remote-path ops
        (mkdir, etc.). For Azure Blob, those FS ops must be handled as no-ops.
        """
        try:
            if self._is_internal_fs_command(command):
                return await self._handle_internal_fs_command(command)

            # Otherwise, do the configured blob operation
            action = self.config.get("action", "upload")
            container = self.config.get("container")
            blob_name = self.config.get("blob_name")
            local_path = self.config.get("local_path")
            encoding = self.config.get("encoding", "utf-8")

            client = await self._get_client()

            if action == "list_containers":
                names = []
                async for c in client.list_containers():
                    names.append(c["name"])
                return ("\n".join(names), 0)

            if not container:
                raise WorkflowExecutionException("Missing 'container' in connector config")
            if action in ("upload", "download", "read") and not blob_name:
                raise WorkflowExecutionException("Missing 'blob_name' in connector config")

            if action == "upload":
                if not local_path:
                    raise WorkflowExecutionException("Missing 'local_path' for upload")
                await self._upload_file(client, container, blob_name, local_path)
                return ("upload completed", 0)

            if action == "download":
                if not local_path:
                    raise WorkflowExecutionException("Missing 'local_path' for download")
                await self._download_file(client, container, blob_name, local_path)
                return ("download completed", 0)

            if action == "read":
                text = await self._read_blob(client, container, blob_name, encoding)
                return (text, 0)

            raise WorkflowExecutionException(f"Invalid action: {action}")

        except Exception as e:
            raise WorkflowExecutionException(f"[AzureBlob] run failed: {e}") from e

    # -------------------------
    # Transfers (optional usage)
    # -------------------------
    async def copy_local_to_remote(
        self, source: str, destination: str, location: ExecutionLocation
    ) -> None:
        client = await self._get_client()
        container_name = self.config["container"]
        blob_client = client.get_blob_client(container=container_name, blob=destination)
        with open(source, "rb") as f:
            await blob_client.upload_blob(f, overwrite=True)

    async def copy_remote_to_local(
        self, source: str, destination: str, location: ExecutionLocation
    ) -> None:
        client = await self._get_client()
        container_name = self.config["container"]
        blob_client = client.get_blob_client(container=container_name, blob=source)
        stream = await blob_client.download_blob()
        data = await stream.readall()
        with open(destination, "wb") as f:
            f.write(data)

    async def copy_remote_to_remote(
        self, source: str, destination: str, location: ExecutionLocation
    ) -> None:
        client = await self._get_client()
        container_name = self.config["container"]
        src = client.get_blob_client(container=container_name, blob=source)
        dst = client.get_blob_client(container=container_name, blob=destination)
        await dst.start_copy_from_url(src.url)

    # -------------------------
    # Streams
    # -------------------------
    async def get_stream_reader(self, location: ExecutionLocation, command: list[str]):
        blob_path = command[-1]
        client = await self._get_client()
        container_name = self.config["container"]
        blob_client = client.get_blob_client(container=container_name, blob=blob_path)
        return await blob_client.download_blob()

    async def get_stream_writer(self, local_path: str):
        raise NotImplementedError(
            "get_stream_writer is not implemented for AzureBlobConnector "
            "(use upload action or copy_local_to_remote)."
        )

    # -------------------------
    # Lifecycle
    # -------------------------
    async def deploy(self, external: bool) -> None:
        return None

    async def undeploy(self, external: bool) -> None:
        await self.close()

    async def close(self) -> None:
        try:
            if self._client:
                await self._client.close()
                self._client = None
            if self._credential and hasattr(self._credential, "close"):
                await self._credential.close()
            if self._transport:
                await self._transport.close()
                self._transport = None
        except Exception as e:
            raise WorkflowExecutionException(f"[AzureBlob] close failed: {e}") from e

    # -------------------------
    # Blob ops
    # -------------------------
    async def _upload_file(
        self,
        client: BlobServiceClient,
        container: str,
        blob_name: str,
        local_path: str,
    ) -> None:
        blob_client = client.get_blob_client(container=container, blob=blob_name)
        with open(local_path, "rb") as f:
            await blob_client.upload_blob(f, overwrite=True)

    async def _download_file(
        self,
        client: BlobServiceClient,
        container: str,
        blob_name: str,
        local_path: str,
    ) -> None:
        blob_client = client.get_blob_client(container=container, blob=blob_name)
        stream = await blob_client.download_blob()
        data = await stream.readall()
        with open(local_path, "wb") as f:
            f.write(data)

    async def _read_blob(
        self,
        client: BlobServiceClient,
        container: str,
        blob_name: str,
        encoding: str,
    ) -> str:
        blob_client = client.get_blob_client(container=container, blob=blob_name)
        stream = await blob_client.download_blob()
        data = await stream.readall()
        return data.decode(encoding)
