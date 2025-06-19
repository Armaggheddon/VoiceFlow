"""
Batch processing example for the VoiceFlow client library.
"""

import asyncio
import os
from pathlib import Path
from typing import List, Tuple
from voiceflow import AsyncVoiceFlowClient, VoiceFlowError

async def batch_transcribe_files(
    client: AsyncVoiceFlowClient,
    audio_files: List[str]
) -> List[Tuple[str, str, bool]]:
    """
    Transcribe multiple audio files concurrently.
    
    Returns:
        List of tuples: (filename, transcription, success)
    """
    print(f"🎙️ Starting batch transcription of {len(audio_files)} files...")
    
    # Create transcription tasks
    tasks = []
    for audio_file in audio_files:
        if os.path.exists(audio_file):
            task = client.transcribe(audio_file, poll_timeout=120.0)
            tasks.append((audio_file, task))
        else:
            print(f"⚠️  File not found: {audio_file}")
    
    if not tasks:
        print("❌ No valid audio files found")
        return []
    
    # Execute all transcription tasks concurrently
    results = []
    task_results = await asyncio.gather(
        *[task for _, task in tasks],
        return_exceptions=True
    )
    
    # Process results
    for (filename, _), result in zip(tasks, task_results):
        if isinstance(result, Exception):
            print(f"❌ {filename}: {result}")
            results.append((filename, "", False))
        else:
            transcription = result.transcribed_text or ""
            print(f"✅ {filename}: {transcription[:50]}...")
            results.append((filename, transcription, True))
    
    return results

async def batch_synthesize_texts(
    client: AsyncVoiceFlowClient,
    texts: List[str]
) -> List[Tuple[str, str, bool]]:
    """
    Synthesize multiple texts concurrently.
    
    Returns:
        List of tuples: (text, audio_url, success)
    """
    print(f"🔊 Starting batch synthesis of {len(texts)} texts...")
    
    # Create synthesis tasks
    tasks = []
    for i, text in enumerate(texts):
        if text.strip():
            task = client.synthesize(text, poll_timeout=120.0)
            tasks.append((f"text_{i+1}", text, task))
        else:
            print(f"⚠️  Empty text at index {i}")
    
    if not tasks:
        print("❌ No valid texts found")
        return []
    
    # Execute all synthesis tasks concurrently
    results = []
    task_results = await asyncio.gather(
        *[task for _, _, task in tasks],
        return_exceptions=True
    )
    
    # Process results
    for (text_id, original_text, _), result in zip(tasks, task_results):
        if isinstance(result, Exception):
            print(f"❌ {text_id}: {result}")
            results.append((original_text, "", False))
        else:
            audio_url = result.audio_url or ""
            print(f"✅ {text_id}: Generated audio")
            results.append((original_text, audio_url, True))
    
    return results

async def process_text_to_speech_pipeline(
    client: AsyncVoiceFlowClient,
    input_texts: List[str]
) -> None:
    """
    Process texts through the complete T2V pipeline and save results.
    """
    print("🔄 Starting text-to-speech pipeline...")
    
    # Batch synthesize all texts
    synthesis_results = await batch_synthesize_texts(client, input_texts)
    
    # Save results to file
    output_file = "synthesis_results.txt"
    with open(output_file, "w") as f:
        f.write("VoiceFlow Batch Synthesis Results\n")
        f.write("=" * 50 + "\n\n")
        
        for i, (text, audio_url, success) in enumerate(synthesis_results, 1):
            f.write(f"Text {i}:\n")
            f.write(f"Content: {text}\n")
            f.write(f"Status: {'✅ Success' if success else '❌ Failed'}\n")
            if success and audio_url:
                f.write(f"Audio URL: {audio_url}\n")
            f.write("\n" + "-" * 30 + "\n\n")
    
    print(f"📄 Results saved to {output_file}")

async def main():
    """Main batch processing demonstration."""
    
    async with AsyncVoiceFlowClient(base_url="http://localhost:8000") as client:
        
        # Check API health first
        print("🔍 Checking API health...")
        if not await client.health_check():
            print("❌ API is not healthy - aborting batch processing")
            return
        print("✅ API is healthy - proceeding with batch processing\n")
        
        # Example 1: Batch transcription
        print("=" * 60)
        print("EXAMPLE 1: BATCH TRANSCRIPTION")
        print("=" * 60)
        
        # List of audio files (replace with actual file paths)
        audio_files = [
            "path/to/audio1.wav",
            "path/to/audio2.wav", 
            "path/to/audio3.wav"
        ]
        
        # Note: Since we don't have actual audio files, we'll skip this
        print("⚠️  Skipping batch transcription (no audio files available)")
        print("   To test this, replace the audio_files list with real file paths\n")
        
        # Example 2: Batch synthesis
        print("=" * 60)
        print("EXAMPLE 2: BATCH SYNTHESIS")
        print("=" * 60)
        
        texts_to_synthesize = [
            "Welcome to the VoiceFlow batch processing example.",
            "This is the second text being synthesized concurrently.",
            "Batch processing allows efficient handling of multiple requests.",
            "The async client enables concurrent operations for better performance.",
            "This concludes our batch synthesis demonstration."
        ]
        
        try:
            synthesis_results = await batch_synthesize_texts(client, texts_to_synthesize)
            
            # Summary
            successful = sum(1 for _, _, success in synthesis_results if success)
            print(f"\n📊 Batch synthesis complete:")
            print(f"   Total: {len(synthesis_results)}")
            print(f"   Successful: {successful}")
            print(f"   Failed: {len(synthesis_results) - successful}")
            
        except Exception as e:
            print(f"❌ Batch synthesis failed: {e}")
        
        # Example 3: Complete pipeline
        print("\n" + "=" * 60)
        print("EXAMPLE 3: COMPLETE PIPELINE PROCESSING")
        print("=" * 60)
        
        pipeline_texts = [
            "Pipeline processing example one.",
            "Pipeline processing example two.",
            "Pipeline processing example three."
        ]
        
        try:
            await process_text_to_speech_pipeline(client, pipeline_texts)
        except Exception as e:
            print(f"❌ Pipeline processing failed: {e}")

def create_sample_audio_files():
    """
    Helper function to create sample audio files for testing.
    This is just a placeholder - you would use actual audio files.
    """
    print("💡 To test batch transcription:")
    print("   1. Create some audio files (WAV format)")
    print("   2. Update the audio_files list in main() with actual file paths")
    print("   3. Run this script again")

if __name__ == "__main__":
    print("🚀 VoiceFlow Batch Processing Example")
    print("=" * 60)
    
    # Show how to create sample files
    create_sample_audio_files()
    print()
    
    # Run the main batch processing
    asyncio.run(main())
