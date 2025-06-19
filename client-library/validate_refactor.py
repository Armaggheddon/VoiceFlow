#!/usr/bin/env python3
"""
Simple validation script for the refactored VoiceFlow client library.
This script tests the new synthesis output formats.
"""

import sys
import traceback
from pathlib import Path

try:
    # Test imports
    from voiceflow import (
        VoiceFlowClient, 
        AsyncVoiceFlowClient, 
        AudioOutputFormat,
        SynthesisResult
    )
    from voiceflow.utils import (
        extract_filename_from_url,
        audio_bytes_to_numpy,
        save_audio_bytes_to_file
    )
    import numpy as np
    print("✅ All imports successful")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

def test_utils():
    """Test utility functions."""
    print("\n🔧 Testing utility functions...")
    
    # Test filename extraction
    test_urls = [
        "http://example.com/audio/test.wav?param=value",
        "http://example.com/audio/test.wav",
        "http://example.com/audio/test",
        "http://example.com/api/v1/files/uuid-123/generated.wav?download=true"
    ]
    
    expected = ["test.wav", "test.wav", "test.wav", "generated.wav"]
    
    for url, expected_filename in zip(test_urls, expected):
        result = extract_filename_from_url(url)
        if result == expected_filename:
            print(f"  ✅ {url} -> {result}")
        else:
            print(f"  ❌ {url} -> {result} (expected {expected_filename})")
            return False
    
    print("✅ Utility functions work correctly")
    return True

def test_models():
    """Test model classes."""
    print("\n📊 Testing model classes...")
    
    # Test AudioOutputFormat enum
    assert AudioOutputFormat.URL == "url"
    assert AudioOutputFormat.NUMPY == "numpy"  
    assert AudioOutputFormat.FILE == "file"
    print("  ✅ AudioOutputFormat enum works")
    
    # Test SynthesisResult with different data
    audio_data = np.array([1, 2, 3, 4])
    save_path = Path("/test/audio.wav")
    
    result = SynthesisResult(
        task_id="test_task",
        status="SUCCESS",
        audio_url="http://example.com/audio.wav",
        audio_data=audio_data,
        saved_path=save_path
    )
    
    # Test convenience methods
    assert result.get_audio_url() == "http://example.com/audio.wav"
    assert np.array_equal(result.get_audio_data(), audio_data)
    assert result.get_saved_path() == save_path
    print("  ✅ SynthesisResult convenience methods work")
    
    print("✅ Model classes work correctly")
    return True

def test_client_interface():
    """Test client interface (without actual API calls)."""
    print("\n🔌 Testing client interface...")
    
    # Test synchronous client
    client = VoiceFlowClient()
    
    # Check that the synthesize method exists with the new signature
    assert hasattr(client, 'synthesize')
    assert hasattr(client, '_convert_to_numpy')
    assert hasattr(client, '_save_to_file')
    
    # Ensure old methods are removed
    assert not hasattr(client, 'synthesize_as_url')
    assert not hasattr(client, 'synthesize_as_numpy') 
    assert not hasattr(client, 'synthesize_to_file')
    print("  ✅ Synchronous client has single synthesize method only")
    
    client.close()
    
    # Test asynchronous client
    async_client = AsyncVoiceFlowClient()
    
    # Check that the synthesize method exists with the new signature
    assert hasattr(async_client, 'synthesize')
    assert hasattr(async_client, '_convert_to_numpy')
    assert hasattr(async_client, '_save_to_file')
    
    # Ensure old methods are removed
    assert not hasattr(async_client, 'synthesize_as_url')
    assert not hasattr(async_client, 'synthesize_as_numpy')
    assert not hasattr(async_client, 'synthesize_to_file')
    print("  ✅ Asynchronous client has single synthesize method only")
    
    # We can't easily test async_client.close() without asyncio setup
    
    print("✅ Client interfaces are correct")
    return True

def main():
    """Run all tests."""
    print("🧪 VoiceFlow Client Library Validation")
    print("=" * 50)
    
    success = True
    
    try:
        success &= test_utils()
        success &= test_models()
        success &= test_client_interface()
        
        if success:
            print("\n🎉 All validation tests passed!")
            print("\n📝 Next steps:")
            print("1. Install dependencies: pip install numpy")
            print("2. Start your VoiceFlow API server")
            print("3. Run examples: python examples/synthesis_formats_example.py")
            print("4. Run tests: python test_synthesis_formats.py")
            return 0
        else:
            print("\n❌ Some validation tests failed!")
            return 1
            
    except Exception as e:
        print(f"\n💥 Unexpected error during validation: {e}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
