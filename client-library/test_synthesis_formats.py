"""
Test the new synthesis output formats functionality.
"""

import pytest
import numpy as np
from pathlib import Path
from unittest.mock import Mock, patch, mock_open

from voiceflow.models import SynthesisResult, TaskStatus, AudioOutputFormat
from voiceflow.utils import (
    extract_filename_from_url,
    audio_bytes_to_numpy,
    save_audio_bytes_to_file
)


class TestUtils:
    """Test utility functions."""
    
    def test_extract_filename_from_url(self):
        """Test filename extraction from URL."""
        # Test with query parameters
        url = "http://example.com/audio/test_file.wav?param=value"
        assert extract_filename_from_url(url) == "test_file.wav"
        
        # Test without query parameters
        url = "http://example.com/audio/test_file.wav"
        assert extract_filename_from_url(url) == "test_file.wav"
        
        # Test with no extension
        url = "http://example.com/audio/test_file"
        assert extract_filename_from_url(url) == "test_file.wav"
        
        # Test with complex path
        url = "http://example.com/api/v1/audio/files/uuid-123/audio.wav?download=true&format=wav"
        assert extract_filename_from_url(url) == "audio.wav"
    
    @patch('wave.open')
    def test_audio_bytes_to_numpy(self, mock_wave_open):
        """Test audio bytes to numpy conversion."""
        # Mock wave file
        mock_wave = Mock()
        mock_wave.getnframes.return_value = 1000
        mock_wave.getsampwidth.return_value = 2  # 16-bit
        mock_wave.getnchannels.return_value = 1  # Mono
        mock_wave.readframes.return_value = b'\x00\x01' * 1000  # Mock audio data
        mock_wave_open.return_value.__enter__.return_value = mock_wave
        
        audio_bytes = b"fake_wav_data"
        result = audio_bytes_to_numpy(audio_bytes)
        
        assert isinstance(result, np.ndarray)
        assert result.dtype == np.int16
        assert len(result) == 1000
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('pathlib.Path.mkdir')
    def test_save_audio_bytes_to_file(self, mock_mkdir, mock_file):
        """Test saving audio bytes to file."""
        audio_bytes = b"fake_audio_data"
        file_path = Path("/test/path/audio.wav")
        
        save_audio_bytes_to_file(audio_bytes, file_path)
        
        # Check that parent directories were created
        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
        
        # Check that file was written
        mock_file.assert_called_once_with(file_path, 'wb')
        mock_file().write.assert_called_once_with(audio_bytes)


class TestModels:
    """Test model classes."""
    
    def test_synthesis_result_methods(self):
        """Test SynthesisResult convenience methods."""
        audio_data = np.array([1, 2, 3, 4])
        save_path = Path("/test/audio.wav")
        
        result = SynthesisResult(
            task_id="test_task",
            status=TaskStatus.SUCCESS,
            audio_url="http://example.com/audio.wav",
            audio_data=audio_data,
            saved_path=save_path
        )
        
        assert result.get_audio_url() == "http://example.com/audio.wav"
        assert np.array_equal(result.get_audio_data(), audio_data)
        assert result.get_saved_path() == save_path
    
    def test_audio_output_format_enum(self):
        """Test AudioOutputFormat enum."""
        assert AudioOutputFormat.URL == "url"
        assert AudioOutputFormat.NUMPY == "numpy"
        assert AudioOutputFormat.FILE == "file"


class TestClientIntegration:
    """Test client integration with new synthesis formats."""
    
    @patch('voiceflow.client.download_audio_as_bytes')
    @patch('voiceflow.client.audio_bytes_to_numpy')
    def test_sync_client_numpy_conversion(self, mock_numpy_convert, mock_download):
        """Test synchronous client numpy conversion."""
        from voiceflow.client import VoiceFlowClient
        
        # Mock dependencies
        mock_download.return_value = b"fake_audio_bytes"
        mock_numpy_convert.return_value = np.array([1, 2, 3])
        
        client = VoiceFlowClient()
        
        # Create a mock result
        original_result = SynthesisResult(
            task_id="test_task",
            status=TaskStatus.SUCCESS,
            audio_url="http://example.com/audio.wav"
        )
        
        # Test conversion
        converted_result = client._convert_to_numpy(original_result)
        
        assert converted_result.audio_url == "http://example.com/audio.wav"
        assert np.array_equal(converted_result.audio_data, np.array([1, 2, 3]))
        
        # Verify mocks were called
        mock_download.assert_called_once_with("http://example.com/audio.wav", timeout=30.0)
        mock_numpy_convert.assert_called_once_with(b"fake_audio_bytes")
    
    @patch('voiceflow.client.download_audio_as_bytes')
    @patch('voiceflow.client.save_audio_bytes_to_file')
    @patch('voiceflow.client.extract_filename_from_url')
    def test_sync_client_file_saving(self, mock_extract_filename, mock_save_file, mock_download):
        """Test synchronous client file saving."""
        from voiceflow.client import VoiceFlowClient
        
        # Mock dependencies
        mock_download.return_value = b"fake_audio_bytes"
        mock_extract_filename.return_value = "extracted_audio.wav"
        
        client = VoiceFlowClient()
        
        # Create a mock result
        original_result = SynthesisResult(
            task_id="test_task",
            status=TaskStatus.SUCCESS,
            audio_url="http://example.com/audio/file.wav?param=value"
        )
        
        # Test file saving with auto-generated path
        saved_result = client._save_to_file(original_result, None)
        
        assert saved_result.audio_url == "http://example.com/audio/file.wav?param=value"
        assert saved_result.saved_path == Path.cwd() / "extracted_audio.wav"
        
        # Verify mocks were called
        mock_download.assert_called_once_with("http://example.com/audio/file.wav?param=value", timeout=30.0)
        mock_extract_filename.assert_called_once_with("http://example.com/audio/file.wav?param=value")
        mock_save_file.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])
