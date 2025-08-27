import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from azure_streamflow.blob_connector import AzureBlobConnector


@pytest.mark.asyncio
@patch("azure_streamflow.blob_connector.DefaultAzureCredential")
@patch("azure_streamflow.blob_connector.BlobServiceClient")
async def test_blob_upload(mock_blob_service_client_class, mock_credential_class):
    mock_blob_service = MagicMock()
    mock_blob_service.close = AsyncMock()
    mock_blob_service_client_class.return_value = mock_blob_service
    mock_blob_client = MagicMock()
    mock_blob_client.upload_blob = AsyncMock()
    mock_blob_service.get_blob_client.return_value = mock_blob_client

    mock_credential_class.return_value.close = AsyncMock()

    config = {
        "blob_account_url": "https://dummy.blob.core.windows.net",
        "action": "upload",
        "container": "mycontainer",
        "blob_name": "myfile.txt",
        "local_path": "dummy_path.txt"
    }

    connector = AzureBlobConnector(config)

    with patch("aiofiles.open", new_callable=MagicMock) as mock_open:
        mock_open.return_value.__aenter__.return_value.read.return_value = b"testdata"

        await connector.setup()
        result = await connector.run("echo", None)
        await connector.close()

        assert result == "upload completed"
        mock_blob_service.get_blob_client.assert_called_once()
        mock_blob_client.upload_blob.assert_awaited_once()


@pytest.mark.asyncio
@patch("azure_streamflow.blob_connector.DefaultAzureCredential")
@patch("azure_streamflow.blob_connector.BlobServiceClient")
async def test_blob_download(mock_blob_service_client_class, mock_credential_class):
    mock_blob_service = MagicMock()
    mock_blob_service.close = AsyncMock()
    mock_blob_service_client_class.return_value = mock_blob_service
    mock_blob_client = MagicMock()
    mock_stream = MagicMock()
    mock_stream.readall = AsyncMock(return_value=b"testdata")
    mock_blob_client.download_blob = AsyncMock(return_value=mock_stream)
    mock_blob_service.get_blob_client.return_value = mock_blob_client

    mock_credential_class.return_value.close = AsyncMock()

    config = {
        "blob_account_url": "https://dummy.blob.core.windows.net",
        "action": "download",
        "container": "mycontainer",
        "blob_name": "myfile.txt",
        "local_path": "dummy_path.txt"
    }

    connector = AzureBlobConnector(config)

    with patch("aiofiles.open", new_callable=MagicMock) as mock_open:
        mock_open.return_value.__aenter__.return_value.write.return_value = None

        await connector.setup()
        result = await connector.run("echo", None)
        await connector.close()

        assert result == "download completed"
        mock_blob_service.get_blob_client.assert_called_once()
        mock_blob_client.download_blob.assert_awaited_once()
        mock_stream.readall.assert_awaited_once()
## AI Assistant
@pytest.mark.asyncio
@patch("azure_streamflow.blob_connector.DefaultAzureCredential")
@patch("azure_streamflow.blob_connector.BlobServiceClient")
async def test_read_returns_content(mock_blob_service_client_cls, mock_credential_cls):
    # Arrange
    config = {
        "blob_account_url": "https://example.blob.core.windows.net",
        "action": "read",
        "container": "my-container",
        "blob_name": "path/to/file.txt",
        # nessun local_path per read
    }

    # Mock credential
    mock_credential = MagicMock()
    mock_credential.close = AsyncMock()
    mock_credential_cls.return_value = mock_credential

    # Mock Blob client
    mock_stream = MagicMock()
    mock_stream.readall = AsyncMock(return_value=b"hello world")

    mock_blob_client = MagicMock()
    mock_blob_client.download_blob = AsyncMock(return_value=mock_stream)

    mock_bsc_instance = MagicMock()
    mock_bsc_instance.get_blob_client.return_value = mock_blob_client
    mock_bsc_instance.close = AsyncMock()
    mock_blob_service_client_cls.return_value = mock_bsc_instance

    connector = AzureBlobConnector(config)

    # Act
    await connector.setup()
    result = await connector.run(command="")
    await connector.close()

    # Assert
    assert result == "hello world"
    mock_bsc_instance.get_blob_client.assert_called_once_with(
        container="my-container", blob="path/to/file.txt"
    )
    mock_blob_client.download_blob.assert_awaited_once()
    mock_stream.readall.assert_awaited_once()
    mock_bsc_instance.close.assert_awaited_once()
    mock_credential.close.assert_awaited_once()


@pytest.mark.asyncio
@patch("azure_streamflow.blob_connector.DefaultAzureCredential")
@patch("azure_streamflow.blob_connector.BlobServiceClient")
async def test_read_uses_custom_encoding(mock_blob_service_client_cls, mock_credential_cls):
    # Arrange
    config = {
        "blob_account_url": "https://example.blob.core.windows.net",
        "action": "read",
        "container": "my-container",
        "blob_name": "file.txt",
        "encoding": "latin-1",
    }

    # Content "café" in latin-1
    data = "café".encode("latin-1")

    mock_credential = MagicMock()
    mock_credential.close = AsyncMock()
    mock_credential_cls.return_value = mock_credential

    mock_stream = MagicMock()
    mock_stream.readall = AsyncMock(return_value=data)

    mock_blob_client = MagicMock()
    mock_blob_client.download_blob = AsyncMock(return_value=mock_stream)

    mock_bsc_instance = MagicMock()
    mock_bsc_instance.get_blob_client.return_value = mock_blob_client
    mock_bsc_instance.close = AsyncMock()
    mock_blob_service_client_cls.return_value = mock_bsc_instance

    connector = AzureBlobConnector(config)

    # Act
    await connector.setup()
    result = await connector.run(command="")
    await connector.close()

    # Assert
    assert result == "café"
    mock_bsc_instance.get_blob_client.assert_called_once_with(
        container="my-container", blob="file.txt"
    )
    mock_blob_client.download_blob.assert_awaited_once()
    mock_stream.readall.assert_awaited_once()

@pytest.mark.asyncio
@patch("azure_streamflow.blob_connector.DefaultAzureCredential")
@patch("azure_streamflow.blob_connector.BlobServiceClient")
async def test_blob_download(mock_blob_service_client_class, mock_credential_class):
    mock_blob_service = MagicMock()
    mock_blob_service.close = AsyncMock()
    mock_blob_service_client_class.return_value = mock_blob_service
    mock_blob_client = MagicMock()
    mock_stream = MagicMock()
    mock_stream.readall = AsyncMock(return_value=b"testdata")
    mock_blob_client.download_blob = AsyncMock(return_value=mock_stream)
    mock_blob_service.get_blob_client.return_value = mock_blob_client

    mock_credential_class.return_value.close = AsyncMock()

    config = {
        "blob_account_url": "https://dummy.blob.core.windows.net",
        "action": "download",
        "container": "mycontainer",
        "blob_name": "myfile.txt",
        "local_path": "dummy_path.txt"
    }

    connector = AzureBlobConnector(config)

    with patch("aiofiles.open", new_callable=MagicMock) as mock_open:
        mock_open.return_value.__aenter__.return_value.write.return_value = None

        await connector.setup()
        result = await connector.run("echo", None)
        await connector.close()

        assert result == "download completed"
        mock_blob_service.get_blob_client.assert_called_once()
        mock_blob_client.download_blob.assert_awaited_once()
        mock_stream.readall.assert_awaited_once()

# Nuovi test per l'azione "read"
@pytest.mark.asyncio
@patch("azure_streamflow.blob_connector.DefaultAzureCredential")
@patch("azure_streamflow.blob_connector.BlobServiceClient")
async def test_blob_read_returns_content(mock_blob_service_client_class, mock_credential_class):
    # Arrange
    mock_blob_service = MagicMock()
    mock_blob_service.close = AsyncMock()
    mock_blob_service_client_class.return_value = mock_blob_service

    mock_stream = MagicMock()
    mock_stream.readall = AsyncMock(return_value=b"hello world")

    mock_blob_client = MagicMock()
    mock_blob_client.download_blob = AsyncMock(return_value=mock_stream)
    mock_blob_service.get_blob_client.return_value = mock_blob_client

    mock_credential_class.return_value.close = AsyncMock()

    config = {
        "blob_account_url": "https://dummy.blob.core.windows.net",
        "action": "read",
        "container": "mycontainer",
        "blob_name": "myfile.txt"
        # local_path non richiesto per read
    }

    connector = AzureBlobConnector(config)

    # Act
    await connector.setup()
    result = await connector.run("echo", None)
    await connector.close()

    # Assert
    assert result == "hello world"
    mock_blob_service.get_blob_client.assert_called_once_with(container="mycontainer", blob="myfile.txt")
    mock_blob_client.download_blob.assert_awaited_once()
    mock_stream.readall.assert_awaited_once()
    mock_blob_service.close.assert_awaited_once()
    mock_credential_class.return_value.close.assert_awaited_once()

@pytest.mark.asyncio
@patch("azure_streamflow.blob_connector.DefaultAzureCredential")
@patch("azure_streamflow.blob_connector.BlobServiceClient")
async def test_blob_read_uses_custom_encoding(mock_blob_service_client_class, mock_credential_class):
    # Arrange
    mock_blob_service = MagicMock()
    mock_blob_service.close = AsyncMock()
    mock_blob_service_client_class.return_value = mock_blob_service

    data = "café".encode("latin-1")
    mock_stream = MagicMock()
    mock_stream.readall = AsyncMock(return_value=data)

    mock_blob_client = MagicMock()
    mock_blob_client.download_blob = AsyncMock(return_value=mock_stream)
    mock_blob_service.get_blob_client.return_value = mock_blob_client

    mock_credential_class.return_value.close = AsyncMock()

    config = {
        "blob_account_url": "https://dummy.blob.core.windows.net",
        "action": "read",
        "container": "mycontainer",
        "blob_name": "myfile.txt",
        "encoding": "latin-1"
    }

    connector = AzureBlobConnector(config)

    # Act
    await connector.setup()
    result = await connector.run("echo", None)
    await connector.close()

    # Assert
    assert result == "café"
    mock_blob_service.get_blob_client.assert_called_once_with(container="mycontainer", blob="myfile.txt")
    mock_blob_client.download_blob.assert_awaited_once()
    mock_stream.readall.assert_awaited_once()


