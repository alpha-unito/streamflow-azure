from __future__ import annotations

import os
import logging
from dataclasses import dataclass
from typing import Any, Collection, MutableMapping, MutableSequence, Optional

from streamflow.deployment.connector import Connector
from streamflow.core.deployment import ExecutionLocation
from streamflow.core.exception import WorkflowExecutionException

from azure_streamflow.executor import AzureExecutor
from azure_streamflow.config import AzureConfig


# -------------------------
# Batch-specific parameters (not for base Connector)
# -------------------------
EXCLUDED_CONNECTOR_PARAMETERS = [
    # streamflow model/deployment naming (passed by framework sometimes)
    "model",
    "deployment",

    # azure-batch config (your AzureConfig expects this)
    "auth",
    "pool",
    "job",
    "task",

    # optional SSL knobs (we add support)
    "insecure_ssl",       # bool: skip TLS verification (DEBUG ONLY)
    "aad_verify",         # bool or path string
    "aad_ca_bundle",      # path to CA bundle (PEM)
]


@dataclass(frozen=True)
class _SchedulingLocation:
    """
    StreamFlow 0.2.0dev13 scheduler expects selected locations to have:
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


class AzureBatchConnector(Connector):
    """
    StreamFlow connector for Azure Batch (0.2.0dev13 compatible).

    Notes:
    - StreamFlow will call run() for internal remote-path operations (mkdir, etc.)
      while preparing job dirs. Batch doesn't implement a remote FS in that sense,
      so those commands are no-op success.
    - For actual execution, we submit a task to Azure Batch.
    """

    def __init__(self, **kwargs: Any):
        # Pass only base Connector args to super()
        base_kwargs = {k: v for k, v in kwargs.items() if k not in EXCLUDED_CONNECTOR_PARAMETERS}

        # Handle StreamFlow naming differences / required args on some builds
        if "config_dir" not in base_kwargs and "configDir" in base_kwargs:
            base_kwargs["config_dir"] = base_kwargs["configDir"]

        if "transferBufferSize" not in base_kwargs:
            if "transfer_buffer_size" in base_kwargs:
                base_kwargs["transferBufferSize"] = base_kwargs["transfer_buffer_size"]
            elif "transfer_buffer" in base_kwargs:
                base_kwargs["transferBufferSize"] = base_kwargs["transfer_buffer"]

        super().__init__(**base_kwargs)

        # Keep the rest as connector config
        self.config: dict[str, Any] = {k: v for k, v in kwargs.items() if k in EXCLUDED_CONNECTOR_PARAMETERS}

        # Name used by ExecutionLocation.deployment
        self._deployment_name = (
            kwargs.get("deployment") or kwargs.get("model") or "azure-batch-model"
        )

        # Optional TLS controls (DEBUG ONLY for insecure_ssl)
        self._insecure_ssl: bool = bool(self.config.get("insecure_ssl", False))
        self._aad_ca_bundle: str | None = self.config.get("aad_ca_bundle")

        # Azure Batch config (your existing classes)
        # Expecting kwargs to contain keys: pool/job/task/auth etc
        self.azure_cfg = AzureConfig({k: v for k, v in kwargs.items() if k in ("auth", "pool", "job", "task")})
        self.executor = AzureExecutor(self.azure_cfg)

        # Convenience ids
        self.job_id = self.azure_cfg.config["job"]["id"]
        self.task_id = self.azure_cfg.config["task"]["id"]

        self._setup_done = False

    # -------------------------
    # Scheduler integration
    # -------------------------
    async def get_available_locations(
        self, service: str | None = None, **kwargs: Any
    ) -> Collection[tuple[ExecutionLocation, _SchedulingLocation]]:
        exec_loc = ExecutionLocation(
            name="azure-batch",
            service=service,
            deployment=self._deployment_name,
        )
        sched_loc = _SchedulingLocation(location=exec_loc, slots=None, hardware=None)
        return [(exec_loc, sched_loc)]

    # -------------------------
    # Internal FS commands
    # -------------------------
    def _is_internal_fs_command(self, command: MutableSequence[str]) -> bool:
        if not command:
            return False
        return command[0] in {"mkdir", "rmdir", "rm", "ls", "test", "stat", "chmod", "chown", "touch"}

    async def _handle_internal_fs_command(self, command: MutableSequence[str]) -> tuple[str, int]:
        # Batch isn't a "remote filesystem backend" for StreamFlow.
        # Treat these as successful no-ops so StreamFlow can set up job dirs.
        return ("", 0)

    # -------------------------
    # TLS knobs (AAD / general)
    # -------------------------
    def _apply_tls_settings(self, environment: MutableMapping[str, str] | None) -> None:
        """
        If your environment breaks certificate validation to login.microsoftonline.com,
        this lets you either:
          - provide a CA bundle (preferred), or
          - disable verification entirely (debug only).
        """
        env = environment or {}

        if self._aad_ca_bundle:
            # Help requests/aiohttp/azure-core find the CA bundle
            env.setdefault("SSL_CERT_FILE", self._aad_ca_bundle)
            env.setdefault("REQUESTS_CA_BUNDLE", self._aad_ca_bundle)

        if self._insecure_ssl:
            # DEBUG ONLY: disable verification broadly
            env["PYTHONHTTPSVERIFY"] = "0"
            env["AZURE_HTTP_VERIFY"] = "false"
            env.setdefault("SSL_CERT_FILE", "")
            env.setdefault("REQUESTS_CA_BUNDLE", "")

        # Apply to process env too (azure sdk may not use `environment` mapping)
        for k, v in env.items():
            os.environ[k] = v

    # -------------------------
    # Lifecycle (deploy/undeploy)
    # -------------------------
    async def deploy(self, external: bool) -> None:
        # StreamFlow may call get_available_locations before running jobs; ensure setup at first real run.
        return None

    async def undeploy(self, external: bool) -> None:
        await self.close()

    async def close(self) -> None:
        try:
            # Your executor likely holds Batch client + creds
            if hasattr(self.executor, "batch_client") and self.executor.batch_client:
                await self.executor.batch_client.close()
            if hasattr(self.executor, "credentials") and self.executor.credentials:
                await self.executor.credentials.close()
        except Exception as e:
            raise WorkflowExecutionException(f"[AzureBatch] close failed: {e}") from e

    # -------------------------
    # Ensure pool/job exist (idempotent)
    # -------------------------
    async def _ensure_setup(self) -> None:
        if self._setup_done:
            return

        logging.info("[AzureBatch] Setting up (pool/job)...")
        try:
            pool_cfg = self.azure_cfg.config["pool"]
            os_image = pool_cfg["os_image"]

            await self.executor.create_pool(
                pool_id=pool_cfg["id"],
                vm_size=pool_cfg["vm_size"],
                node_count=pool_cfg["node_count"],
                publisher=os_image["publisher"],
                offer=os_image["offer"],
                sku=os_image["sku"],
            )

            job_cfg = self.azure_cfg.config["job"]
            await self.executor.submit_job(job_cfg["id"], job_cfg["pool_id"])

            self._setup_done = True
        except Exception as e:
            raise WorkflowExecutionException(f"[AzureBatch] setup failed: {e}") from e

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
        For StreamFlow:
        - internal FS commands -> no-op success
        - actual commands -> submit Azure Batch task
        """
        try:
            # Handle StreamFlow internal remote-path ops
            if self._is_internal_fs_command(command):
                return await self._handle_internal_fs_command(command)

            # Apply TLS policy (CA bundle or insecure)
            self._apply_tls_settings(environment)

            # Ensure pool/job exist
            await self._ensure_setup()

            # StreamFlow gives command tokens; Azure Batch expects a string commandLine
            # Common safe join: preserve quoting by using bash -lc for complex commands,
            # but here we just join tokens. If you need bash -lc, pass it from CWL.
            command_line = " ".join(command)

            task_cfg = self.azure_cfg.config["task"]
            await self.executor.submit_task(
                job_id=self.job_id,
                task_id=self.task_id,
                command_line=command_line,
                resource_files=task_cfg.get("resource_files", []),
            )

            # Optional: wait for completion if your executor supports it; otherwise return submitted
            # state = await self.executor.monitor_job(self.job_id)

            return (self.task_id, 0)

        except Exception as e:
            raise WorkflowExecutionException(f"[AzureBatch] run failed: {e}") from e

    # -------------------------
    # Optional: explicit status/teardown helpers
    # (StreamFlow doesn't necessarily call these, but you can use them)
    # -------------------------
    async def status(self, task_id: str, location: ExecutionLocation | None = None):
        try:
            state = await self.executor.monitor_job(self.job_id)
            return {"job_id": self.job_id, "task_id": task_id, "state": state}
        except Exception as e:
            raise WorkflowExecutionException(f"[AzureBatch] status failed: {e}") from e

    async def teardown(self, location: ExecutionLocation | None = None):
        logging.info("[AzureBatch] Tearing down environment...")
        try:
            await self.executor.delete_pool(self.azure_cfg.config["pool"]["id"])
        except Exception as e:
            raise WorkflowExecutionException(f"[AzureBatch] teardown failed: {e}") from e
