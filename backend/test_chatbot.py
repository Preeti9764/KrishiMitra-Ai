#!/usr/bin/env python3
"""
Test script for KrishiMitra chatbot functionality
"""
import requests
import json

def test_chatbot():
    """Test the chatbot with various queries"""
    base_url = "http://localhost:8000"
    
    # Test cases
    test_cases = [
        {
            "message": "which soil type required for maize",
            "language": "en",
            "expected_topic": "faq"
        },
        {
            "message": "what soil is best for cotton",
            "language": "en", 
            "expected_topic": "faq"
        },
        {
            "message": "rice soil requirements",
            "language": "en",
            "expected_topic": "faq"
        },
        {
            "message": "how to grow tomatoes",
            "language": "en",
            "expected_topic": "openai_fallback"
        }
    ]
    
    print("Testing KrishiMitra Chatbot...")
    print("=" * 50)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case['message']}")
        print("-" * 30)
        
        try:
            response = requests.post(
                f"{base_url}/api/chat",
                json=test_case,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Status: SUCCESS")
                print(f"📝 Reply: {data.get('reply', 'No reply')[:100]}...")
                print(f"🏷️  Topic: {data.get('topic', 'Unknown')}")
                print(f"🌐 Language: {data.get('language', 'Unknown')}")
            else:
                print(f"❌ Status: FAILED ({response.status_code})")
                print(f"Error: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Connection Error: {e}")
    
    print("\n" + "=" * 50)
    print("Test completed!")

if __name__ == "__main__":
    test_chatbot()
