import logging
import asyncio
import pytest
from unittest.mock import patch, MagicMock
from azure_streamflow.executor import AzureExecutor
from azure_streamflow.config import AzureConfig

@pytest.fixture
def mock_config():
    return AzureConfig({
        "batch_account_url": "https://test-batch-account.region.batch.azure.com",
        "client_id": "fake-client-id",
        "client_secret": "fake-client-secret",
        "tenant_id": "fake-tenant-id"
    })

@pytest.mark.asyncio
@patch('azure_streamflow.executor.BatchServiceClient', autospec=True)
@patch('azure_streamflow.executor.ServicePrincipalCredentials', autospec=True)
async def test_create_pool(mock_credentials, mock_batch_client_class, mock_config):
    mock_credentials_instance = MagicMock()
    mock_credentials.return_value = mock_credentials_instance

    mock_batch_client_instance = MagicMock()
    mock_batch_client_class.return_value = mock_batch_client_instance
    mock_batch_client_instance.pool = MagicMock()
    mock_batch_client_instance.pool.add = MagicMock()

    executor = AzureExecutor(mock_config)
    await executor.create_pool("testpool", "STANDARD_A1_v2", 2, "Canonical", "UbuntuServer", "18.04-LTS")

    mock_batch_client_instance.pool.add.assert_called_once()

@pytest.mark.asyncio
@patch('azure_streamflow.executor.BatchServiceClient', autospec=True)
@patch('azure_streamflow.executor.ServicePrincipalCredentials', autospec=True)
async def test_submit_job(mock_credentials, mock_batch_client_class, mock_config):
    mock_credentials_instance = MagicMock()
    mock_credentials.return_value = mock_credentials_instance

    mock_batch_client_instance = MagicMock()
    mock_batch_client_class.return_value = mock_batch_client_instance
    mock_batch_client_instance.job = MagicMock()
    mock_batch_client_instance.job.add = MagicMock()

    executor = AzureExecutor(mock_config)
    await executor.submit_job("testjob", "testpool")

    mock_batch_client_instance.job.add.assert_called_once()

@pytest.mark.asyncio
@patch('azure_streamflow.executor.BatchServiceClient', autospec=True)
@patch('azure_streamflow.executor.ServicePrincipalCredentials', autospec=True)
async def test_submit_task(mock_credentials, mock_batch_client_class, mock_config):
    mock_credentials_instance = MagicMock()
    mock_credentials.return_value = mock_credentials_instance

    mock_batch_client_instance = MagicMock()
    mock_batch_client_class.return_value = mock_batch_client_instance
    mock_batch_client_instance.task = MagicMock()
    mock_batch_client_instance.task.add = MagicMock()

    executor = AzureExecutor(mock_config)
    await executor.submit_task("testjob", "testtask", "/bin/bash -c 'echo Hello, World!'")

    mock_batch_client_instance.task.add.assert_called_once()

@pytest.mark.asyncio
@patch('azure_streamflow.executor.BatchServiceClient', autospec=True)
@patch('azure_streamflow.executor.ServicePrincipalCredentials', autospec=True)
async def test_monitor_job(mock_credentials, mock_batch_client_class, mock_config):
    mock_credentials_instance = MagicMock()
    mock_credentials.return_value = mock_credentials_instance

    mock_batch_client_instance = MagicMock()
    mock_batch_client_class.return_value = mock_batch_client_instance
    mock_job = MagicMock()
    mock_job.state = "completed"
    mock_batch_client_instance.job = MagicMock()
    mock_batch_client_instance.job.get = MagicMock(return_value=mock_job)

    executor = AzureExecutor(mock_config)
    job_state = await executor.monitor_job("testjob")

    assert job_state == "completed"
    mock_batch_client_instance.job.get.assert_called_once_with("testjob")

@pytest.mark.asyncio
@patch('azure_streamflow.executor.BatchServiceClient', autospec=True)
@patch('azure_streamflow.executor.ServicePrincipalCredentials', autospec=True)
async def test_delete_pool(mock_credentials, mock_batch_client_class, mock_config):
    mock_credentials_instance = MagicMock()
    mock_credentials.return_value = mock_credentials_instance

    mock_batch_client_instance = MagicMock()
    mock_batch_client_class.return_value = mock_batch_client_instance
    mock_batch_client_instance.pool = MagicMock()
    mock_batch_client_instance.pool.delete = MagicMock()

    executor = AzureExecutor(mock_config)
    await executor.delete_pool("testpool")

    mock_batch_client_instance.pool.delete.assert_called_once_with("testpool")