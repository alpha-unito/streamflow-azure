from streamflow.ext.plugin import StreamFlowPlugin
from azure_streamflow.connector import AzureStreamFlowConnector


class AzureStreamFlowPlugin(StreamFlowPlugin):
    def register(self) -> None:
        self.register_connector("eu.across.azure_batch", AzureStreamFlowConnector)
