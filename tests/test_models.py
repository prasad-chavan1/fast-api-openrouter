"""
Unit tests for Pydantic models with chat session support
"""
import pytest
from datetime import datetime
from pydantic import ValidationError
from models import ChatRequest, ChatResponse, ErrorResponse, ChatMessage, ChatSession

# The actual model we use in our project
TEST_MODEL = "cognitivecomputations/dolphin-mistral-24b-venice-edition:free"


class TestChatRequest:
    """Test cases for ChatRequest model"""
    
    def test_valid_request_with_default_model(self):
        """Test valid request with default model"""
        request = ChatRequest(message="Hello, world!")
        assert request.message == "Hello, world!"
        assert request.model == TEST_MODEL
        assert request.chat_id is None
    
    def test_valid_request_with_custom_model(self):
        """Test valid request with custom model (but we prefer our default)"""
        request = ChatRequest(
            message="What is AI?", 
            model=TEST_MODEL  # Use our actual model
        )
        assert request.message == "What is AI?"
        assert request.model == TEST_MODEL
    
    def test_message_whitespace_trimming(self):
        """Test that message whitespace is trimmed"""
        request = ChatRequest(message="  Hello, world!  ")
        assert request.message == "Hello, world!"
    
    def test_empty_message_validation(self):
        """Test that empty message raises validation error"""
        with pytest.raises(ValidationError) as exc_info:
            ChatRequest(message="")
        
        errors = exc_info.value.errors()
        assert len(errors) == 1
        # Check for either the field validator error or the min_length error
        error_msg = str(errors[0]['msg'])
        assert ("Message cannot be empty" in error_msg or 
                "String should have at least 1 character" in error_msg)
    
    def test_whitespace_only_message_validation(self):
        """Test that whitespace-only message raises validation error"""
        with pytest.raises(ValidationError) as exc_info:
            ChatRequest(message="   ")
        
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert "Message cannot be empty" in str(errors[0]['msg'])
    
    def test_missing_message_validation(self):
        """Test that missing message raises validation error"""
        with pytest.raises(ValidationError) as exc_info:
            ChatRequest()
        
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]['type'] == 'missing'
    
    def test_serialization(self):
        """Test model serialization to dict"""
        request = ChatRequest(message="Test message", model="test-model")
        data = request.model_dump()
        
        assert data == {
            "message": "Test message",
            "model": "test-model"
        }


class TestChatResponse:
    """Test cases for ChatResponse model"""
    
    def test_valid_response(self):
        """Test valid response creation"""
        response = ChatResponse(
            response="Hello! How can I help you?",
            model="test-model"
        )
        assert response.response == "Hello! How can I help you?"
        assert response.status == "success"
        assert response.model == "test-model"
    
    def test_custom_status(self):
        """Test response with custom status"""
        response = ChatResponse(
            response="Test response",
            status="completed",
            model="test-model"
        )
        assert response.status == "completed"
    
    def test_missing_required_fields(self):
        """Test that missing required fields raise validation error"""
        with pytest.raises(ValidationError) as exc_info:
            ChatResponse()
        
        errors = exc_info.value.errors()
        assert len(errors) == 2  # response and model are required
        
        error_fields = [error['loc'][0] for error in errors]
        assert 'response' in error_fields
        assert 'model' in error_fields
    
    def test_serialization(self):
        """Test model serialization to dict"""
        response = ChatResponse(
            response="AI response",
            model="test-model"
        )
        data = response.model_dump()
        
        assert data == {
            "response": "AI response",
            "status": "success",
            "model": "test-model"
        }


class TestErrorResponse:
    """Test cases for ErrorResponse model"""
    
    def test_valid_error_response(self):
        """Test valid error response creation"""
        error = ErrorResponse(
            error="Something went wrong",
            code=500
        )
        assert error.error == "Something went wrong"
        assert error.status == "error"
        assert error.code == 500
    
    def test_custom_status(self):
        """Test error response with custom status"""
        error = ErrorResponse(
            error="Validation failed",
            status="validation_error",
            code=400
        )
        assert error.status == "validation_error"
    
    def test_missing_required_fields(self):
        """Test that missing required fields raise validation error"""
        with pytest.raises(ValidationError) as exc_info:
            ErrorResponse()
        
        errors = exc_info.value.errors()
        assert len(errors) == 2  # error and code are required
        
        error_fields = [error['loc'][0] for error in errors]
        assert 'error' in error_fields
        assert 'code' in error_fields
    
    def test_serialization(self):
        """Test model serialization to dict"""
        error = ErrorResponse(
            error="Test error",
            code=400
        )
        data = error.model_dump()
        
        assert data == {
            "error": "Test error",
            "status": "error",
            "code": 400
        }