# Azure Batch Streamflow Plugin

## Descrizione

**Azure Batch Streamflow Plugin** è un plugin per [Streamflow](https://streamflow.com) che consente di integrare i servizi di **Azure Batch**, una piattaforma di elaborazione di lavori batch su larga scala. Questo plugin consente di gestire pool di nodi di calcolo, inviare job e task, e monitorare l'esecuzione direttamente tramite l'interfaccia di Streamflow.

## Caratteristiche

- **Creazione e gestione di pool di calcolo** su Azure Batch.
- **Invio di job** su Azure Batch con supporto per task multipli.
- **Monitoraggio dei job** e recupero degli stati di esecuzione.
- **Eliminazione automatica dei pool** una volta completati i job (opzionale).
  
## Requisiti

- Python 3.7 o superiore
- [Azure SDK for Python](https://docs.microsoft.com/it-it/python/azure/)
- Un account Azure con i servizi di **Azure Batch** abilitati

## Struttura del Progetto
azure_batch_streamflow_plugin/
├── azure_batch_streamflow/
│   ├── __init__.py
│   ├── azure_batch_plugin.py
│   ├── executor.py
│   ├── schemas/
│   │   └── azure_batch.json
│   └── config.py
├── setup.py
├── README.md
└── tests/
    ├── __init__.py
    └── test_azure_batch_plugin.py


## Installazione

### Passo 1: Clona il Repository

Clona questo repository nel tuo ambiente locale:

```bash
git clone https://github.com/tuo-nome/azure-batch-streamflow-plugin.git
cd azure-batch-streamflow-plugin 
```

### Passo 2:  Installa le Dipendenze

``` Python
python -m venv venv
source venv/bin/activate  # Su Windows: venv\Scripts\activate
pip install .
```

### Esempio di Configurazione JSON

Crea un file di configurazione `azure_batch_config.json` con le seguenti informazioni:

```json
{
    "batch_account_url": "https://<your-batch-account>.<region>.batch.azure.com",
    "client_id": "<your-azure-client-id>",
    "client_secret": "<your-azure-client-secret>",
    "tenant_id": "<your-azure-tenant-id>",
    "pool": {
        "id": "mypool",
        "vm_size": "STANDARD_A1_v2",
        "node_count": 2,
        "os_image": {
            "publisher": "Canonical",
            "offer": "UbuntuServer",
            "sku": "18.04-LTS"
        }
    },
    "job": {
        "id": "myjob",
        "pool_id": "mypool"
    },
    "task": {
        "id": "mytask",
        "command_line": "/bin/bash -c 'echo Hello, World!'"
    }
}
```

### Creazione del Pool

``` Python
from azure_batch_streamflow_plugin.executor import AzureBatchExecutor
from azure_batch_streamflow_plugin.config import AzureBatchConfig

# Carica la configurazione
config = AzureBatchConfig({
    "batch_account_url": "https://<your-batch-account>.<region>.batch.azure.com",
    "client_id": "<your-client-id>",
    "client_secret": "<your-client-secret>",
    "tenant_id": "<your-tenant-id>"
})

executor = AzureBatchExecutor(config)

# Creazione del pool
executor.create_pool(
    pool_id="mypool",
    vm_size="STANDARD_A1_v2",
    node_count=2,
    publisher="Canonical",
    offer="UbuntuServer",
    sku="18.04-LTS"
)
```

###  Invio di un Job
``` Python
executor.submit_job(job_id="myjob", pool_id="mypool")
```

###  Invio di un Task
``` Python
executor.submit_task(
    job_id="myjob",
    task_id="mytask",
    command_line="/bin/bash -c 'echo Hello, World!'"
)
```

###  Monitoraggio di un Job
``` Python
status = executor.monitor_job(job_id="myjob")
print(f"Job status: {status}")
```

###  Eliminazione di un Pool
``` Python
executor.delete_pool(pool_id="mypool")
```

###  Test
``` Python
pytest tests/
```
