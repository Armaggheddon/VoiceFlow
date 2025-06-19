"""
Basic usage example of the VoiceFlow client library.
"""

from voiceflow import VoiceFlowClient

def main():
    # Initialize the client
    client = VoiceFlowClient(base_url="http://localhost:8000")
    
    try:
        # Check if the API is healthy
        print("🔍 Checking API health...")
        if client.health_check():
            print("✅ VoiceFlow API is healthy!")
        else:
            print("❌ VoiceFlow API is not responding")
            return
        
        # Example 1: Transcribe an audio file
        print("\n🎙️ Testing transcription...")
        try:
            # You would replace this with an actual audio file path
            audio_file = "path/to/your/audio.wav"
            result = client.transcribe(audio_file, poll_timeout=60.0)
            
            if result.transcribed_text:
                print(f"📝 Transcription: {result.transcribed_text}")
            else:
                print("❌ No transcription text received")
                
        except FileNotFoundError:
            print("⚠️  Audio file not found - skipping transcription test")
        except Exception as e:
            print(f"❌ Transcription failed: {e}")
        
        # Example 2: Synthesize text to speech
        print("\n🔊 Testing speech synthesis...")
        try:
            text = "Hello, this is a test of the VoiceFlow text-to-speech synthesis."
            
            # Option 1: Get URL (default behavior)
            print("\n📡 Getting audio as URL:")
            result = client.synthesize(text, poll_timeout=60.0)
            if result.audio_url:
                print(f"🎵 Audio generated successfully!")
                print(f"🔗 Audio URL: {result.audio_url}")
                print("💡 You can download this audio file using the URL")
            
            # Option 2: Get audio as numpy array
            print("\n🔢 Getting audio as numpy array:")
            from voiceflow import AudioOutputFormat
            result = client.synthesize(text, output_format=AudioOutputFormat.NUMPY, poll_timeout=60.0)
            if result.audio_data is not None:
                print(f"🎵 Audio generated successfully!")
                print(f"� Audio data shape: {result.audio_data.shape}")
                print(f"📊 Audio data type: {result.audio_data.dtype}")
                print("💡 You can now process the audio data directly")
            
            # Option 3: Save audio to file
            print("\n💾 Saving audio to file:")
            result = client.synthesize(text, output_format=AudioOutputFormat.FILE, save_path="my_audio.wav", poll_timeout=60.0)
            if result.saved_path:
                print(f"🎵 Audio generated successfully!")
                print(f"📁 Audio saved to: {result.saved_path}")
                print(f"✅ File exists: {result.saved_path.exists()}")
                print("💡 You can now play the audio file directly")
            else:
                print("❌ No saved path received")
                
        except Exception as e:
            print(f"❌ Synthesis failed: {e}")
    
    finally:
        # Always close the client
        client.close()
        print("\n🔒 Client closed")

if __name__ == "__main__":
    main()
