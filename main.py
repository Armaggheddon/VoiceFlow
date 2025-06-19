#!/usr/bin/env python3
"""VoiceFlow API test suite for transcription and synthesis endpoints."""

import httpx
import time
import os
import tempfile
import wave
import numpy as np

# Configuration
API_BASE_URL = "http://localhost:8000"
TRANSCRIBE_URL = f"{API_BASE_URL}/v1/transcribe"
SYNTHESIZE_URL = f"{API_BASE_URL}/v1/synthesize"
RESULT_URL_TEMPLATE = f"{API_BASE_URL}/v1/tasks/{{task_id}}"

def create_test_audio():
    """Create a simple test audio file."""
    sample_rate = 44100
    duration = 2
    frequency = 440  # A4 note
    
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    audio_data = np.sin(2 * np.pi * frequency * t)
    audio_data = (audio_data * 32767).astype(np.int16)
    
    temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    with wave.open(temp_file.name, 'w') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_data.tobytes())
    
    return temp_file.name

def poll_for_result(task_id, timeout=60):
    """Poll for task result with timeout."""
    result_url = RESULT_URL_TEMPLATE.format(task_id=task_id)
    start_time = time.time()
    
    with httpx.Client(timeout=30.0) as client:
        while time.time() - start_time < timeout:
            try:
                response = client.get(result_url)
                response.raise_for_status()
                result = response.json()
                
                if result["status"] == "SUCCESS":
                    return result
                elif result["status"] == "FAILED":
                    raise Exception(f"Task failed: {result.get('error_message', 'Unknown error')}")
                
                time.sleep(3)
                
            except httpx.RequestError:
                time.sleep(3)
    
    raise TimeoutError(f"Task {task_id} timed out after {timeout} seconds")

def test_transcription():
    """Test the transcription endpoint."""
    print("\n=== Testing Transcription (V2T) ===")
    
    audio_file_path = create_test_audio()
    
    try:
        with httpx.Client(timeout=30.0) as client:
            with open(audio_file_path, "rb") as f:
                files = {"audio_file": ("test_audio.wav", f, "audio/wav")}
                response = client.post(TRANSCRIBE_URL, files=files)
                response.raise_for_status()
            
            task_data = response.json()
            task_id = task_data["task_id"]
            
            result = poll_for_result(task_id)
            print("✅ Transcription completed successfully!")
            print(f"Transcribed text: {result.get('transcribed_text', 'No text returned')}")
            return True
            
    except Exception as e:
        print(f"❌ Transcription test failed: {e}")
        return False
    finally:
        if os.path.exists(audio_file_path):
            os.unlink(audio_file_path)

def test_synthesis():
    """Test the synthesis endpoint."""
    print("\n=== Testing Synthesis (T2V) ===")
    
    test_text = "Hello, this is a test message for speech synthesis."
    
    try:
        with httpx.Client(timeout=30.0) as client:
            data = {"text": test_text}
            response = client.post(SYNTHESIZE_URL, data=data)
            response.raise_for_status()
            
            task_data = response.json()
            task_id = task_data["task_id"]
            
            result = poll_for_result(task_id)
            
            audio_url = result.get("audio_url")
            if audio_url:
                print("✅ Synthesis completed successfully!")
                print(f"Audio URL: {audio_url}")
                
                # Download synthesized audio
                audio_response = client.get(audio_url)
                audio_response.raise_for_status()
                
                output_file = f"/tmp/synthesized_{task_id}.wav"
                with open(output_file, "wb") as f:
                    f.write(audio_response.content)
                
                print(f"Synthesized audio saved to: {output_file}")
                return True
            else:
                print("❌ No audio URL in response")
                return False
            
    except Exception as e:
        print(f"❌ Synthesis test failed: {e}")
        return False

def test_health():
    """Test the health endpoint."""
    print("\n=== Testing Health Endpoint ===")
    
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(f"{API_BASE_URL}/health")
            response.raise_for_status()
            result = response.json()
            
            if result.get("status") == "ok":
                print("✅ Health check passed")
                return True
            else:
                print(f"❌ Unexpected health response: {result}")
                return False
                
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🎙️ VoiceFlow API Test Suite")
    print("=" * 50)
    
    tests = [
        ("Health Check", test_health),
        ("Transcription (V2T)", test_transcription),
        ("Synthesis (T2V)", test_synthesis)
    ]
    
    results = [(name, test_func()) for name, test_func in tests]
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print("=" * 50)
    
    passed = 0
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name:<20} {status}")
        if success:
            passed += 1
    
    print(f"\nTests passed: {passed}/{len(results)}")
    
    if passed == len(results):
        print("🎉 All tests passed! VoiceFlow API is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the API gateway and services.")
        return 1

if __name__ == "__main__":
    exit(main())
