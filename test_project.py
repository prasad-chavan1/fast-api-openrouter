#!/usr/bin/env python3
"""
Simple test script to verify the FastAPI OpenRouter project works correctly
Tests only with our actual OpenRouter model: cognitivecomputations/dolphin-mistral-24b-venice-edition:free
"""

from fastapi.testclient import TestClient
from main import app
from chat_manager import ChatManager

# Our actual OpenRouter model
TEST_MODEL = "cognitivecomputations/dolphin-mistral-24b-venice-edition:free"

def test_project():
    """Test the complete project functionality"""
    
    print("🧪 Testing FastAPI OpenRouter Proxy Project")
    print("=" * 50)
    
    # Set up the app with real configuration
    app.state.config = {
        'openrouter_api_key': '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',
        'site_url': 'http://localhost:8000',
        'site_name': 'FastAPI OpenRouter Proxy',
        'environment': 'test'
    }
    app.state.chat_manager = ChatManager()
    
    client = TestClient(app)
    
    # Test 1: Health Check
    print("1️⃣ Testing health endpoints...")
    health = client.get('/health')
    assert health.status_code == 200
    health_data = health.json()
    assert health_data['status'] == 'healthy'
    assert health_data['openrouter_configured'] is True
    print("   ✅ Health check passed")
    
    # Test 2: Chat with our actual model
    print("2️⃣ Testing chat with our OpenRouter model...")
    chat_response = client.post('/chat', json={
        'message': 'What is 3+3? Answer with just the number.',
        'model': TEST_MODEL
    })
    
    assert chat_response.status_code == 200
    chat_data = chat_response.json()
    
    assert chat_data['status'] == 'success'
    assert chat_data['model'] == TEST_MODEL
    assert 'chat_id' in chat_data
    assert chat_data['message_count'] == 2
    assert '6' in chat_data['response']  # Should contain the answer
    
    print(f"   ✅ Chat response: {chat_data['response'][:50]}...")
    print(f"   ✅ Model: {chat_data['model']}")
    print(f"   ✅ Chat ID: {chat_data['chat_id']}")
    
    # Test 3: Continue conversation
    print("3️⃣ Testing conversation continuity...")
    chat_id = chat_data['chat_id']
    
    follow_up = client.post('/chat', json={
        'message': 'What about 5+5?',
        'model': TEST_MODEL,
        'chat_id': chat_id
    })
    
    assert follow_up.status_code == 200
    follow_data = follow_up.json()
    
    assert follow_data['chat_id'] == chat_id
    assert follow_data['message_count'] == 4  # 2 pairs now
    assert '10' in follow_data['response']  # Should contain the answer
    
    print(f"   ✅ Follow-up response: {follow_data['response'][:50]}...")
    print(f"   ✅ Message count: {follow_data['message_count']}")
    
    # Test 4: Session management
    print("4️⃣ Testing session management...")
    sessions = client.get('/chats')
    assert sessions.status_code == 200
    sessions_data = sessions.json()
    
    assert chat_id in sessions_data['sessions']
    assert sessions_data['count'] >= 1
    
    print(f"   ✅ Found {sessions_data['count']} session(s)")
    
    # Test 5: Get session info
    session_info = client.get(f'/chat/{chat_id}')
    assert session_info.status_code == 200
    info_data = session_info.json()
    
    assert info_data['chat_id'] == chat_id
    assert info_data['model'] == TEST_MODEL
    assert info_data['message_count'] == 4
    
    print(f"   ✅ Session info retrieved successfully")
    
    print("\n🎉 ALL TESTS PASSED!")
    print("✅ FastAPI OpenRouter Proxy is working perfectly!")
    print(f"✅ Using model: {TEST_MODEL}")
    print("✅ Chat sessions and conversation memory working")
    print("✅ All endpoints responding correctly")
    print("\n🚀 Project is ready for production!")

if __name__ == "__main__":
    test_project()