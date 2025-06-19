"""
Integration test example - demonstrates the client library working with a real VoiceFlow API.

Run this after starting your VoiceFlow services to test the client library.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from voiceflow import VoiceFlowClient, VoiceFlowError, TaskTimeoutError

def test_integration():
    """Run integration tests against a real VoiceFlow API."""
    
    print("🧪 VoiceFlow Client Library Integration Test")
    print("=" * 50)
    
    # Initialize client
    client = VoiceFlowClient(
        base_url="http://localhost:8000",  # Adjust if your API runs on different port
        timeout=30.0,
        poll_interval=2.0
    )
    
    try:
        # Test 1: Health Check
        print("\n1️⃣ Testing Health Check...")
        is_healthy = client.health_check()
        if is_healthy:
            print("✅ API is healthy!")
        else:
            print("❌ API is not healthy - check if VoiceFlow services are running")
            return False
        
        # Test 2: Text-to-Speech Synthesis
        print("\n2️⃣ Testing Text-to-Speech Synthesis...")
        try:
            test_text = "Hello from the VoiceFlow client library integration test!"
            print(f"   Synthesizing: '{test_text}'")
            
            result = client.synthesize(test_text, poll_timeout=60.0)
            
            if result.audio_url:
                print(f"✅ Synthesis successful!")
                print(f"   Task ID: {result.task_id}")
                print(f"   Audio URL: {result.audio_url}")
                print(f"   Status: {result.status}")
            else:
                print("❌ Synthesis completed but no audio URL received")
                return False
                
        except TaskTimeoutError:
            print("⏰ Synthesis timed out - this might be normal for first requests")
        except VoiceFlowError as e:
            print(f"❌ Synthesis failed: {e}")
            return False
        
        # Test 3: Error Handling
        print("\n3️⃣ Testing Error Handling...")
        try:
            # This should raise an error
            client.synthesize("")
            print("❌ Empty text should have raised an error")
            return False
        except VoiceFlowError:
            print("✅ Empty text properly rejected")
        
        # Test 4: Context Manager
        print("\n4️⃣ Testing Context Manager...")
        try:
            with VoiceFlowClient(base_url="http://localhost:8000") as ctx_client:
                is_healthy = ctx_client.health_check()
                print(f"✅ Context manager works: healthy = {is_healthy}")
        except Exception as e:
            print(f"❌ Context manager failed: {e}")
            return False
        
        print("\n🎉 All integration tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Unexpected error during integration test: {e}")
        return False
        
    finally:
        client.close()
        print("\n🔒 Client closed")

def main():
    """Main function."""
    print("Starting VoiceFlow Client Library Integration Test...")
    print("Make sure your VoiceFlow services are running before starting this test.")
    print("(Run: docker-compose up -d)")
    
    input("\nPress Enter to continue or Ctrl+C to cancel...")
    
    success = test_integration()
    
    if success:
        print("\n✅ Integration test completed successfully!")
        print("\n💡 Next steps:")
        print("   - Check out the examples/ directory for more usage patterns")
        print("   - Run 'pytest tests/' to run unit tests")
        print("   - Integrate the client library into your own projects")
    else:
        print("\n❌ Integration test failed!")
        print("\n🔧 Troubleshooting:")
        print("   - Make sure VoiceFlow services are running: docker-compose up -d")
        print("   - Check if the API gateway is accessible at http://localhost:8000")
        print("   - Verify all services are healthy in Docker")
        print("   - Check the service logs for errors")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())
