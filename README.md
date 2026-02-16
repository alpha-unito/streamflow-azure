# Azure StreamFlow Plugin

## Descrizione

**Azure StreamFlow Plugin** è un plugin per [StreamFlow](https://streamflow.di.unito.it/) che consente l’integrazione con i servizi **Azure Batch** e **Azure Blob Storage**.

Il plugin permette di:

- usare **Azure Batch** come backend di esecuzione per workflow StreamFlow
- gestire automaticamente **pool**, **job** e **task**
- supportare **autenticazione tramite certificato X.509**
- funzionare correttamente con **StreamFlow ≥ 0.2.0dev13**

Il plugin segue il **modello di esecuzione di StreamFlow**, dove:
- StreamFlow gestisce scheduling e CWL
- il connector Azure si occupa dell’interazione con Azure

---

## Componenti supportati

### Azure Batch Connector
- Creazione automatica dei **pool**
- Sottomissione dei **job**
- Esecuzione dei **task**
- Monitoraggio dello stato
- Cleanup opzionale delle risorse

### Azure Blob Connector
- Upload/download di file da Azure Blob Storage
- Supporto a **certificate authentication**
- Opzione per disabilitare temporaneamente la verifica TLS 

---

## Requisiti

- Python **3.10+** (consigliato)
- StreamFlow **0.2.0dev13**
- Azure SDK:
  - `azure-batch`
  - `azure-identity`
  - `azure-storage-blob`
- Account Azure con:
  - **Azure Batch**
  - **Azure Active Directory**
  - **Azure Blob Storage** (opzionale)

---

## Struttura del progetto


azure_streamflow_plugin/
├── azure_streamflow/
│   ├── __init__.py
│   ├── plugin.py
│   ├── executor.py
│   ├── version.py
│   ├── connector.py
│   ├── schemas/
|   |   └── azure_blob.json
│   │   └── azure_batch.json
│   └── config.py
├── setup.py
├── README.md
└── tests/
    ├── __init__.py
    └── test_azure_plugin.py


## Installazione

### Passo 1: Clona il Repository

Clona questo repository nel tuo ambiente locale:

```bash
git clone https://github.com/alpha-unito/streamflow-azure.git
cd azure-streamflow-plugin 
```

### Passo 2:  Installa le Dipendenze

``` Python
python -m venv venv
source venv/bin/activate  # Su Windows: venv\Scripts\activate
pip install .
```

### Esempio di Configurazione JSON

Crea un file di configurazione `streamflow.yml` con le seguenti informazioni:

```yml
version: v1.0

workflows:
  batch-example:
    type: cwl
    config:
      file: example.cwl
    bindings:
      - step: /
        target:
          deployment: azure-batch-model

deployments:
  azure-batch-model:
    type: eu.across.azure.batch
    config:
      batch_account_url: "https://<account>.<region>.batch.azure.com"

      auth:
        auth_mode: certificate
        tenant_id: "<tenant-id>"
        client_id: "<client-id>"
        certificate_path: "/path/to/cert.pem"

      pool:
        id: "mypool"
        vm_size: "STANDARD_D2_v2"
        node_count: 2
        os_image:
          publisher: "Canonical"
          offer: "UbuntuServer"
          sku: "20_04-lts"

      job:
        id: "myjob"
        pool_id: "mypool"

      task:
        id: "mytask"
```
### Autenticazione

| Modalità      | Descrizione                  |
| ------------- | ---------------------------- |
| `default`     | Usa `DefaultAzureCredential` |
| `certificate` | Usa certificato X.509        |
| `shared_key`  | Usa account key Azure Batch  |

### Certificate authentication 
```yml
auth:
  auth_mode: certificate
  tenant_id: "<tenant-id>"
  client_id: "<client-id>"
  certificate_path: "/path/to/certificate.pem"
```
### CWL di esempio

Crea un file example.cwl

```yml
cwlVersion: v1.2
class: CommandLineTool

baseCommand: ["bash", "-lc"]
arguments:
  - |
    echo "Hello from Azure Batch"
    echo '{}' > cwl.output.json

inputs: {}

outputs:
  result:
    type: File
    outputBinding:
      glob: cwl.output.json
```

### Esecuzione

Esegui il streamflow.yml

```bash
streamflow run streamflow.yml
```