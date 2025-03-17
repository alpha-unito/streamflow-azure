from unittest.mock import patch, MagicMock
import pytest
from azure_batch_streamflow.executor import AzureBatchExecutor
from azure_batch_streamflow.config import AzureBatchConfig


@pytest.fixture
def mock_config():
    # Mock di una configurazione valida per Azure Batch
    return AzureBatchConfig({
        "batch_account_url": "https://test-batch-account.region.batch.azure.com",
        "client_id": "fake-client-id",
        "client_secret": "fake-client-secret",
        "tenant_id": "fake-tenant-id"
    })


# Mock both ServicePrincipalCredentials and BatchServiceClient
@patch('azure_batch_streamflow.executor.BatchServiceClient', autospec=True)
@patch('azure_batch_streamflow.executor.ServicePrincipalCredentials', autospec=True)
def test_create_pool(mock_credentials, mock_batch_client_class, mock_config):
    # Mock dell'oggetto ServicePrincipalCredentials
    mock_credentials_instance = MagicMock()
    mock_credentials.return_value = mock_credentials_instance

    # Simulazione del comportamento del metodo `signed_session`
    mock_session = MagicMock()
    mock_credentials_instance.signed_session.return_value = mock_session

    # Mock del BatchServiceClient
    mock_batch_client_instance = MagicMock()
    mock_batch_client_class.return_value = mock_batch_client_instance

    # Creare un mock per il metodo pool.add
    mock_pool_add = MagicMock()
    mock_batch_client_instance.pool = MagicMock()
    mock_batch_client_instance.pool.add = mock_pool_add

    # Inizializzare l'executor passando il mock della configurazione
    mock_executor = AzureBatchExecutor(mock_config)

    # Simulare la creazione del pool
    pool_id = "testpool"
    mock_executor.create_pool(pool_id, "STANDARD_A1_v2", 2, "Canonical", "UbuntuServer", "18.04-LTS")

    # Verifica che il pool sia stato creato correttamente

    mock_pool_add.assert_called_once_with({
        'id': pool_id,
        'vm_size': "STANDARD_A1_v2",
        'virtual_machine_configuration': {
            'image_reference': {
                'publisher': "Canonical",
                'offer': "UbuntuServer",
                'sku': "18.04-LTS"
            },
            'node_agent_sku_id': 'batch.node.ubuntu 18.04'
        },
        'target_dedicated_nodes': 2
    })

    # Verifica che la sessione firmata sia stata utilizzata
    #mock_credentials_instance.signed_session.assert_called_once()


## Mock both ServicePrincipalCredentials and BatchServiceClient
@patch('azure_batch_streamflow.executor.BatchServiceClient', autospec=True)
@patch('azure_batch_streamflow.executor.ServicePrincipalCredentials', autospec=True)
def test_submit_job(mock_credentials, mock_batch_client_class, mock_config):
    # Mock dell'oggetto ServicePrincipalCredentials
    mock_credentials_instance = MagicMock()
    mock_credentials.return_value = mock_credentials_instance

    # Mock del BatchServiceClient
    mock_batch_client_instance = MagicMock()
    mock_batch_client_class.return_value = mock_batch_client_instance

    # Creare un mock per il metodo job.add
    mock_job_add = MagicMock()
    mock_batch_client_instance.job = MagicMock()
    mock_batch_client_instance.job.add = mock_job_add

    # Inizializzare l'executor passando il mock della configurazione
    mock_executor = AzureBatchExecutor(mock_config)

    # Simulare l'invio del job
    job_id = "testjob"
    pool_id = "testpool"
    mock_executor.submit_job(job_id, pool_id)

    # Verifica che il job sia stato inviato correttamente
    mock_job_add.assert_called_once_with({
        'id': job_id,
        'pool_info': {
            'pool_id': pool_id
        }
    })


## Mock both ServicePrincipalCredentials and BatchServiceClient
@patch('azure_batch_streamflow.executor.BatchServiceClient', autospec=True)
@patch('azure_batch_streamflow.executor.ServicePrincipalCredentials', autospec=True)
def test_submit_task(mock_credentials, mock_batch_client_class, mock_config):
    # Mock dell'oggetto ServicePrincipalCredentials
    mock_credentials_instance = MagicMock()
    mock_credentials.return_value = mock_credentials_instance

    # Mock del BatchServiceClient
    mock_batch_client_instance = MagicMock()
    mock_batch_client_class.return_value = mock_batch_client_instance

    # Creare un mock per il metodo task.add
    mock_task_add = MagicMock()
    mock_batch_client_instance.task = MagicMock()
    mock_batch_client_instance.task.add = mock_task_add

    # Inizializzare l'executor passando il mock della configurazione
    mock_executor = AzureBatchExecutor(mock_config)

    # Simulare l'invio del task
    job_id = "testjob"
    task_id = "testtask"
    command_line = "/bin/bash -c 'echo Hello, World!'"
    mock_executor.submit_task(job_id, task_id, command_line)

    # Verifica che il task sia stato inviato correttamente
    mock_task_add.assert_called_once_with(job_id, {
        'id': task_id,
        'command_line': command_line
    })


## Mock both ServicePrincipalCredentials and BatchServiceClient
@patch('azure_batch_streamflow.executor.BatchServiceClient', autospec=True)
@patch('azure_batch_streamflow.executor.ServicePrincipalCredentials', autospec=True)
def test_monitor_job(mock_credentials, mock_batch_client_class, mock_config):
    # Mock dell'oggetto ServicePrincipalCredentials
    mock_credentials_instance = MagicMock()
    mock_credentials.return_value = mock_credentials_instance

    # Mock del BatchServiceClient
    mock_batch_client_instance = MagicMock()
    mock_batch_client_class.return_value = mock_batch_client_instance

    # Creare un mock per il metodo job.get
    mock_job_get = MagicMock()
    mock_job = MagicMock()
    mock_job.state = "completed"
    mock_batch_client_instance.job = MagicMock()
    mock_batch_client_instance.job.get = MagicMock(return_value=mock_job)

    # Inizializzare l'executor passando il mock della configurazione
    mock_executor = AzureBatchExecutor(mock_config)

    # Simulare il monitoraggio del job
    job_id = "testjob"
    job_state = mock_executor.monitor_job(job_id)

    # Verifica che lo stato del job sia corretto
    assert job_state == "completed"

    # Verifica che il metodo job.get sia stato chiamato correttamente
    mock_batch_client_instance.job.get.assert_called_once_with(job_id)


# Mock both ServicePrincipalCredentials and BatchServiceClient
@patch('azure_batch_streamflow.executor.BatchServiceClient', autospec=True)
@patch('azure_batch_streamflow.executor.ServicePrincipalCredentials', autospec=True)
def test_delete_pool(mock_credentials, mock_batch_client_class, mock_config):
    # Mock dell'oggetto ServicePrincipalCredentials
    mock_credentials_instance = MagicMock()
    mock_credentials.return_value = mock_credentials_instance

    # Mock del BatchServiceClient
    mock_batch_client_instance = MagicMock()
    mock_batch_client_class.return_value = mock_batch_client_instance

    # Creare un mock per il metodo pool.delete
    mock_batch_client_instance.pool = MagicMock()
    mock_batch_client_instance.pool.delete = MagicMock()

    # Inizializzare l'executor passando il mock della configurazione
    mock_executor = AzureBatchExecutor(mock_config)

    # Eseguire il metodo di eliminazione del pool
    pool_id = "testpool"
    mock_executor.delete_pool(pool_id)

    # Verifica che il pool sia stato eliminato correttamente
    mock_batch_client_instance.pool.delete.assert_called_once_with(pool_id)