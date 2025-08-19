#!/usr/bin/env python3
import requests
import json

def test_chatbot_8001():
    """Test the chatbot on port 8001"""
    base_url = "http://localhost:8001"
    
    print("Testing KrishiMitra Chatbot on port 8001...")
    print("=" * 50)
    
    # Test health endpoint
    try:
        health_response = requests.get(f"{base_url}/health", timeout=5)
        print(f"Health Check: {health_response.status_code} - {health_response.text}")
    except Exception as e:
        print(f"Health Check Failed: {e}")
        return
    
    # Test chatbot
    test_message = "which soil type required for maize"
    
    try:
        response = requests.post(
            f"{base_url}/api/chat",
            json={"message": test_message, "language": "en"},
            timeout=10
        )
        
        print(f"\nChatbot Test:")
        print(f"Query: {test_message}")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Reply: {data.get('reply', 'No reply')}")
            print(f"Topic: {data.get('topic', 'Unknown')}")
            print(f"Language: {data.get('language', 'Unknown')}")
        else:
            print(f"Error Response: {response.text}")
            
    except Exception as e:
        print(f"Chatbot Test Failed: {e}")

if __name__ == "__main__":
    test_chatbot_8001()
