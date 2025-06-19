"""
Test suite for VoiceFlow client library.
"""

import pytest
import httpx
from unittest.mock import Mock, patch
from voiceflow import VoiceFlowClient, AsyncVoiceFlowClient, TaskStatus, VoiceFlowError, TaskTimeoutError


class TestVoiceFlowClient:
    """Tests for the synchronous VoiceFlow client."""
    
    def test_client_initialization(self):
        """Test client initialization with default and custom parameters."""
        # Default initialization
        client = VoiceFlowClient()
        assert client.base_url == "http://localhost:8000"
        assert client.timeout == 30.0
        assert client.poll_interval == 2.0
        client.close()
        
        # Custom initialization
        client = VoiceFlowClient(
            base_url="https://custom.api.com",
            timeout=60.0,
            poll_interval=1.0
        )
        assert client.base_url == "https://custom.api.com"
        assert client.timeout == 60.0
        assert client.poll_interval == 1.0
        client.close()
    
    def test_context_manager(self):
        """Test client as context manager."""
        with VoiceFlowClient() as client:
            assert client._client is not None
        # Client should be closed after context exit
    
    @patch('httpx.Client.get')
    def test_health_check_success(self, mock_get):
        """Test successful health check."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"status": "ok"}
        mock_get.return_value = mock_response
        
        client = VoiceFlowClient()
        assert client.health_check() is True
        client.close()
    
    @patch('httpx.Client.get')
    def test_health_check_failure(self, mock_get):
        """Test health check failure."""
        mock_get.side_effect = httpx.RequestError("Connection failed")
        
        client = VoiceFlowClient()
        assert client.health_check() is False
        client.close()
    
    def test_synthesize_empty_text(self):
        """Test synthesis with empty text raises error."""
        client = VoiceFlowClient()
        
        with pytest.raises(VoiceFlowError, match="Text cannot be empty"):
            client.synthesize("")
        
        with pytest.raises(VoiceFlowError, match="Text cannot be empty"):
            client.synthesize("   ")
        
        client.close()
    
    @patch('httpx.Client.post')
    def test_submit_synthesis_success(self, mock_post):
        """Test successful synthesis submission."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"task_id": "test-task-123"}
        mock_post.return_value = mock_response
        
        client = VoiceFlowClient()
        task_id = client._submit_synthesis("Hello world")
        assert task_id == "test-task-123"
        client.close()
    
    @patch('httpx.Client.get')
    def test_get_task_result_transcription(self, mock_get):
        """Test getting transcription task result."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "task_id": "test-task-123",
            "status": "SUCCESS",
            "transcribed_text": "Hello world"
        }
        mock_get.return_value = mock_response
        
        client = VoiceFlowClient()
        result = client.get_task_result("test-task-123")
        
        assert result.task_id == "test-task-123"
        assert result.status == TaskStatus.SUCCESS
        assert result.transcribed_text == "Hello world"
        client.close()
    
    @patch('httpx.Client.get')
    def test_get_task_result_synthesis(self, mock_get):
        """Test getting synthesis task result."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "task_id": "test-task-456",
            "status": "SUCCESS",
            "audio_url": "https://example.com/audio.wav"
        }
        mock_get.return_value = mock_response
        
        client = VoiceFlowClient()
        result = client.get_task_result("test-task-456")
        
        assert result.task_id == "test-task-456"
        assert result.status == TaskStatus.SUCCESS
        assert result.audio_url == "https://example.com/audio.wav"
        client.close()


@pytest.mark.asyncio
class TestAsyncVoiceFlowClient:
    """Tests for the asynchronous VoiceFlow client."""
    
    async def test_async_client_initialization(self):
        """Test async client initialization."""
        client = AsyncVoiceFlowClient()
        assert client.base_url == "http://localhost:8000"
        assert client.timeout == 30.0
        assert client.poll_interval == 2.0
        await client.close()
    
    async def test_async_context_manager(self):
        """Test async client as context manager."""
        async with AsyncVoiceFlowClient() as client:
            assert client._client is not None
        # Client should be closed after context exit
    
    @patch('httpx.AsyncClient.get')
    async def test_async_health_check_success(self, mock_get):
        """Test successful async health check."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"status": "ok"}
        mock_get.return_value = mock_response
        
        client = AsyncVoiceFlowClient()
        result = await client.health_check()
        assert result is True
        await client.close()
    
    @patch('httpx.AsyncClient.get')
    async def test_async_health_check_failure(self, mock_get):
        """Test async health check failure."""
        mock_get.side_effect = httpx.RequestError("Connection failed")
        
        client = AsyncVoiceFlowClient()
        result = await client.health_check()
        assert result is False
        await client.close()
    
    async def test_async_synthesize_empty_text(self):
        """Test async synthesis with empty text raises error."""
        client = AsyncVoiceFlowClient()
        
        with pytest.raises(VoiceFlowError, match="Text cannot be empty"):
            await client.synthesize("")
        
        await client.close()


class TestModels:
    """Test data models."""
    
    def test_task_status_enum(self):
        """Test TaskStatus enum values."""
        assert TaskStatus.PENDING == "PENDING"
        assert TaskStatus.SUCCESS == "SUCCESS" 
        assert TaskStatus.FAILED == "FAILED"
    
    def test_voiceflow_error(self):
        """Test VoiceFlowError exception."""
        error = VoiceFlowError("Test error")
        assert str(error) == "Test error"
    
    def test_task_timeout_error(self):
        """Test TaskTimeoutError exception."""
        error = TaskTimeoutError("Task timed out")
        assert str(error) == "Task timed out"
        assert isinstance(error, VoiceFlowError)


if __name__ == "__main__":
    pytest.main([__file__])
