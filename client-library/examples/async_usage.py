"""
Async usage example of the VoiceFlow client library.
"""

import asyncio
from voiceflow import AsyncVoiceFlowClient

async def main():
    # Use async context manager for automatic cleanup
    async with AsyncVoiceFlowClient(base_url="http://localhost:8000") as client:
        
        # Check API health
        print("🔍 Checking API health...")
        is_healthy = await client.health_check()
        if is_healthy:
            print("✅ VoiceFlow API is healthy!")
        else:
            print("❌ VoiceFlow API is not responding")
            return
        
        # Example 1: Concurrent transcription and synthesis
        print("\n⚡ Running concurrent operations...")
        
        # Create tasks for concurrent execution
        tasks = []
        
        # Transcription task (if you have an audio file)
        try:
            audio_file = "path/to/your/audio.wav" 
            transcription_task = client.transcribe(audio_file, poll_timeout=60.0)
            tasks.append(("transcription", transcription_task))
        except FileNotFoundError:
            print("⚠️  Audio file not found - skipping transcription")
        
        # Synthesis task - demonstrate different output formats
        synthesis_task_url = client.synthesize_as_url(
            "This is an asynchronous test of VoiceFlow synthesis as URL.",
            poll_timeout=60.0
        )
        tasks.append(("synthesis_url", synthesis_task_url))
        
        synthesis_task_numpy = client.synthesize_as_numpy(
            "This is an asynchronous test of VoiceFlow synthesis as numpy array.",
            poll_timeout=60.0
        )
        tasks.append(("synthesis_numpy", synthesis_task_numpy))
        
        synthesis_task_file = client.synthesize_to_file(
            "This is an asynchronous test of VoiceFlow synthesis saved to file.",
            save_path="async_test_audio.wav",
            poll_timeout=60.0
        )
        tasks.append(("synthesis_file", synthesis_task_file))
        
        # Wait for all tasks to complete
        if tasks:
            results = await asyncio.gather(
                *[task for _, task in tasks],
                return_exceptions=True
            )
            
            # Process results
            for (task_type, _), result in zip(tasks, results):
                if isinstance(result, Exception):
                    print(f"❌ {task_type.title()} failed: {result}")
                else:
                    if task_type == "transcription":
                        print(f"📝 Transcription: {result.transcribed_text}")
                    elif task_type == "synthesis_url":
                        print(f"🎵 URL Synthesis completed!")
                        print(f"🔗 Audio URL: {result.audio_url}")
                    elif task_type == "synthesis_numpy":
                        print(f"🎵 Numpy Synthesis completed!")
                        print(f"📊 Audio data shape: {result.audio_data.shape}")
                    elif task_type == "synthesis_file":
                        print(f"🎵 File Synthesis completed!")
                        print(f"📁 Audio saved to: {result.saved_path}")
        
        # Example 2: Sequential async operations
        print("\n🔄 Running sequential operations...")
        
        try:
            # First, synthesize as URL
            result = await client.synthesize(
                "Sequential processing example with VoiceFlow as URL.",
                poll_timeout=60.0
            )
            print(f"✅ First synthesis (URL): {result.audio_url}")
            
            # Then synthesize as numpy array
            from voiceflow import AudioOutputFormat
            result2 = await client.synthesize(
                "This is the second synthesis as numpy array.",
                output_format=AudioOutputFormat.NUMPY,
                poll_timeout=60.0
            )
            print(f"✅ Second synthesis (Numpy): shape {result2.audio_data.shape}")
            
            # Finally, save to file
            result3 = await client.synthesize(
                "This is the third synthesis saved to file.",
                output_format=AudioOutputFormat.FILE,
                save_path="sequential_test.wav",
                poll_timeout=60.0
            )
            print(f"✅ Third synthesis (File): {result3.saved_path}")
            
        except Exception as e:
            print(f"❌ Sequential operations failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
