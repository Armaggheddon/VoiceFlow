"""
Error handling example for the VoiceFlow client library.
"""

from voiceflow import (
    VoiceFlowClient, 
    VoiceFlowError, 
    TaskTimeoutError, 
    APIError, 
    TaskStatus
)

def demonstrate_error_handling():
    """Demonstrate various error handling scenarios."""
    
    client = VoiceFlowClient(
        base_url="http://localhost:8000",
        timeout=10.0,
        poll_interval=1.0
    )
    
    try:
        print("🛡️ Demonstrating error handling scenarios...\n")
        
        # 1. Health check with error handling
        print("1️⃣ Testing health check...")
        try:
            is_healthy = client.health_check()
            if is_healthy:
                print("✅ API is healthy")
            else:
                print("⚠️  API health check returned false")
        except Exception as e:
            print(f"❌ Health check failed: {e}")
        
        # 2. Empty text synthesis (should raise VoiceFlowError)
        print("\n2️⃣ Testing empty text synthesis...")
        try:
            result = client.synthesize("")
            print("❌ This should not succeed")
        except VoiceFlowError as e:
            print(f"✅ Caught expected error: {e}")
        
        # 3. Invalid file transcription
        print("\n3️⃣ Testing invalid file transcription...")
        try:
            result = client.transcribe("nonexistent_file.wav")
            print("❌ This should not succeed")
        except FileNotFoundError as e:
            print(f"✅ Caught expected file error: {e}")
        except VoiceFlowError as e:
            print(f"✅ Caught VoiceFlow error: {e}")
        
        # 4. Timeout handling
        print("\n4️⃣ Testing timeout handling...")
        try:
            # Set a very short timeout to demonstrate timeout error
            result = client.synthesize(
                "This might timeout with a very short timeout",
                poll_timeout=0.1  # Very short timeout
            )
            print(f"✅ Synthesis completed: {result.task_id}")
        except TaskTimeoutError as e:
            print(f"✅ Caught expected timeout: {e}")
        except VoiceFlowError as e:
            print(f"✅ Caught VoiceFlow error: {e}")
        
        # 5. API Error handling (wrong base URL)
        print("\n5️⃣ Testing API error handling...")
        wrong_client = VoiceFlowClient(
            base_url="http://invalid-url:9999",
            timeout=5.0
        )
        try:
            is_healthy = wrong_client.health_check()
            print(f"Health check result: {is_healthy}")  # Should be False
            
            # Try to make a request that will fail
            result = wrong_client.synthesize("This will fail")
            print("❌ This should not succeed")
        except APIError as e:
            print(f"✅ Caught API error: {e} (Status: {e.status_code})")
        except VoiceFlowError as e:
            print(f"✅ Caught VoiceFlow error: {e}")
        finally:
            wrong_client.close()
        
        # 6. Manual task checking with error handling
        print("\n6️⃣ Testing manual task result checking...")
        try:
            # Try to get result of non-existent task
            result = client.get_task_result("invalid-task-id")
            print(f"Task result: {result}")
        except APIError as e:
            print(f"✅ Caught expected API error for invalid task: {e}")
        except VoiceFlowError as e:
            print(f"✅ Caught VoiceFlow error: {e}")
        
        # 7. Successful operation for comparison
        print("\n7️⃣ Testing successful operation...")
        try:
            result = client.synthesize("This should work fine.")
            print(f"✅ Synthesis successful!")
            print(f"   Task ID: {result.task_id}")
            print(f"   Status: {result.status}")
            if result.audio_url:
                print(f"   Audio URL: {result.audio_url}")
        except Exception as e:
            print(f"❌ Unexpected error in successful operation: {e}")
    
    finally:
        client.close()
        print("\n🔒 Client closed")

def demonstrate_result_checking():
    """Demonstrate how to check task results and handle different statuses."""
    
    print("\n📊 Demonstrating result status checking...")
    
    client = VoiceFlowClient(base_url="http://localhost:8000")
    
    try:
        # Submit a synthesis task
        text = "Testing result status checking"
        print(f"🔄 Submitting synthesis task: '{text}'")
        
        # Get task ID without waiting for completion
        task_id = client._submit_synthesis(text)
        print(f"📋 Task submitted with ID: {task_id}")
        
        # Manually check result with proper error handling
        max_attempts = 30
        attempt = 0
        
        while attempt < max_attempts:
            try:
                result = client.get_task_result(task_id)
                print(f"📊 Attempt {attempt + 1}: Status = {result.status}")
                
                if result.status == TaskStatus.SUCCESS:
                    print(f"✅ Task completed successfully!")
                    if hasattr(result, 'audio_url') and result.audio_url:
                        print(f"🔗 Audio URL: {result.audio_url}")
                    break
                elif result.status == TaskStatus.FAILED:
                    print(f"❌ Task failed: {result.error_message}")
                    break
                elif result.status == TaskStatus.PENDING:
                    print(f"⏳ Task still pending...")
                    import time
                    time.sleep(2)
                
                attempt += 1
                
            except APIError as e:
                print(f"❌ API error while checking task: {e}")
                break
            except VoiceFlowError as e:
                print(f"❌ VoiceFlow error while checking task: {e}")
                break
        
        if attempt >= max_attempts:
            print(f"⏰ Reached maximum attempts ({max_attempts})")
    
    finally:
        client.close()

if __name__ == "__main__":
    demonstrate_error_handling()
    demonstrate_result_checking()
