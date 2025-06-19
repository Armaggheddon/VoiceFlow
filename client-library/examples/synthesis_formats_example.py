"""
Example showing different synthesis output formats.
"""

import asyncio
from pathlib import Path

from voiceflow import VoiceFlowClient, AsyncVoiceFlowClient, AudioOutputFormat


def sync_synthesis_examples():
    """Demonstrate synchronous synthesis with different output formats."""
    print("🔊 Synchronous Synthesis Examples")
    print("=" * 50)
    
    client = VoiceFlowClient(base_url="http://localhost:8000")
    text = "Hello, this is a test of the VoiceFlow text-to-speech synthesis."
    
    try:
        # Example 1: Get audio as URL (default behavior)
        print("\n1️⃣ Synthesize as URL:")
        result = client.synthesize(text)
        if result.audio_url:
            print(f"✅ Audio URL: {result.audio_url}")
        
        # Example 2: Get audio as numpy array
        print("\n2️⃣ Synthesize as Numpy Array:")
        result = client.synthesize(text, output_format=AudioOutputFormat.NUMPY)
        if result.audio_data is not None:
            print(f"✅ Audio data shape: {result.audio_data.shape}")
            print(f"✅ Audio data type: {result.audio_data.dtype}")
            print(f"✅ Audio data min/max: {result.audio_data.min()}/{result.audio_data.max()}")
        
        # Example 3: Save audio to file (auto-generated filename)
        print("\n3️⃣ Synthesize and save to file (auto filename):")
        result = client.synthesize(text, output_format=AudioOutputFormat.FILE)
        if result.saved_path:
            print(f"✅ Audio saved to: {result.saved_path}")
            print(f"✅ File exists: {result.saved_path.exists()}")
        
        # Example 4: Save audio to specific file path
        print("\n4️⃣ Synthesize and save to specific path:")
        save_path = Path("my_custom_audio.wav")
        result = client.synthesize(text, output_format=AudioOutputFormat.FILE, save_path=save_path)
        if result.saved_path:
            print(f"✅ Audio saved to: {result.saved_path}")
            print(f"✅ File exists: {result.saved_path.exists()}")
        
        # Example 5: Using different output formats
        print("\n5️⃣ Using different output formats:")
        
        # URL format
        result_url = client.synthesize(text, output_format=AudioOutputFormat.URL)
        print(f"✅ URL format: {result_url.audio_url}")
        
        # Numpy format
        result_numpy = client.synthesize(text, output_format=AudioOutputFormat.NUMPY)
        print(f"✅ Numpy format shape: {result_numpy.audio_data.shape}")
        
        # File format
        result_file = client.synthesize(text, output_format=AudioOutputFormat.FILE, save_path="general_method.wav")
        print(f"✅ File format saved to: {result_file.saved_path}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        client.close()


async def async_synthesis_examples():
    """Demonstrate asynchronous synthesis with different output formats."""
    print("\n\n🔊 Asynchronous Synthesis Examples")
    print("=" * 50)
    
    async with AsyncVoiceFlowClient(base_url="http://localhost:8000") as client:
        text = "Hello, this is an async test of the VoiceFlow text-to-speech synthesis."
        
        try:
            # Example 1: Get audio as URL (default behavior)
            print("\n1️⃣ Async synthesize as URL:")
            result = await client.synthesize(text)
            if result.audio_url:
                print(f"✅ Audio URL: {result.audio_url}")
            
            # Example 2: Get audio as numpy array
            print("\n2️⃣ Async synthesize as Numpy Array:")
            result = await client.synthesize(text, output_format=AudioOutputFormat.NUMPY)
            if result.audio_data is not None:
                print(f"✅ Audio data shape: {result.audio_data.shape}")
                print(f"✅ Audio data type: {result.audio_data.dtype}")
            
            # Example 3: Save audio to file (auto-generated filename)
            print("\n3️⃣ Async synthesize and save to file (auto filename):")
            result = await client.synthesize(text, output_format=AudioOutputFormat.FILE)
            if result.saved_path:
                print(f"✅ Audio saved to: {result.saved_path}")
                print(f"✅ File exists: {result.saved_path.exists()}")
            
            # Example 4: Save audio to specific file path
            print("\n4️⃣ Async synthesize and save to specific path:")
            save_path = Path("async_custom_audio.wav")
            result = await client.synthesize(text, output_format=AudioOutputFormat.FILE, save_path=save_path)
            if result.saved_path:
                print(f"✅ Audio saved to: {result.saved_path}")
                print(f"✅ File exists: {result.saved_path.exists()}")
            
            # Example 5: Using different output formats
            print("\n5️⃣ Using async different output formats:")
            
            # URL format
            result_url = await client.synthesize(text, output_format=AudioOutputFormat.URL)
            print(f"✅ URL format: {result_url.audio_url}")
            
            # Numpy format
            result_numpy = await client.synthesize(text, output_format=AudioOutputFormat.NUMPY)
            print(f"✅ Numpy format shape: {result_numpy.audio_data.shape}")
            
            # File format
            result_file = await client.synthesize(text, output_format=AudioOutputFormat.FILE, save_path="async_general_method.wav")
            print(f"✅ File format saved to: {result_file.saved_path}")
            
        except Exception as e:
            print(f"❌ Error: {e}")


def demonstrate_result_methods():
    """Demonstrate the convenience methods on SynthesisResult."""
    print("\n\n📊 SynthesisResult Convenience Methods")
    print("=" * 50)
    
    client = VoiceFlowClient(base_url="http://localhost:8000")
    text = "Testing result convenience methods."
    
    try:
        # Get a result with numpy data
        result = client.synthesize(text, output_format=AudioOutputFormat.NUMPY)
        
        print("\n📋 Available methods on SynthesisResult:")
        print(f"• get_audio_url(): {result.get_audio_url()}")
        print(f"• get_audio_data() shape: {result.get_audio_data().shape if result.get_audio_data() is not None else None}")
        print(f"• get_saved_path(): {result.get_saved_path()}")
        
        # Get a result with saved file
        result_file = client.synthesize(text, output_format=AudioOutputFormat.FILE, save_path="convenience_test.wav")
        print(f"• get_saved_path() for file result: {result_file.get_saved_path()}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        client.close()


if __name__ == "__main__":
    print("🎵 VoiceFlow Synthesis Formats Example")
    print("This example demonstrates different ways to receive synthesized audio")
    
    # Run synchronous examples
    sync_synthesis_examples()
    
    # Run asynchronous examples
    asyncio.run(async_synthesis_examples())
    
    # Demonstrate result methods
    demonstrate_result_methods()
    
    print("\n✨ Examples completed!")
    print("\nNote: Make sure the VoiceFlow API server is running at http://localhost:8000")
