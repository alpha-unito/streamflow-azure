from streamflow.ext.plugin import StreamFlowPlugin
from azure_streamflow.batch_connector import AzureBatchConnector
from azure_streamflow.blob_connector import AzureBlobConnector


class AzureStreamFlowPlugin(StreamFlowPlugin):
    def register(self) -> None:
        self.register_connector("eu.across.azure.batch", AzureBatchConnector)
        self.register_connector("eu.across.azure.blob", AzureBlobConnector)