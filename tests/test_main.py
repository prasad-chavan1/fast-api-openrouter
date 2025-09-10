"""
Unit tests for main FastAPI application
"""
import pytest
from unittest.mock import patch, Mock, AsyncMock
from fastapi.testclient import TestClient

from main import app, validate_environment, ConfigurationError
from openrouter_client import OpenRouterError


class TestValidateEnvironment:
    """Test cases for validate_environment function"""
    
    @patch('main.load_dotenv')
    @patch.dict('os.environ', {
        'OPENROUTER_API_KEY': 'test-api-key',
        'SITE_URL': 'https://example.com',
        'SITE_NAME': 'Test Site',
        'ENVIRONMENT': 'production'
    })
    def test_validate_environment_success_all_vars(self, mock_load_dotenv):
        """Test successful validation with all environment variables"""
        config = validate_environment()
        
        assert config == {
            'openrouter_api_key': 'test-api-key',
            'site_url': 'https://example.com',
            'site_name': 'Test Site',
            'environment': 'production'
        }
    
    @patch('main.load_dotenv')
    @patch.dict('os.environ', {'OPENROUTER_API_KEY': 'test-key'}, clear=True)
    def test_validate_environment_success_minimal_vars(self, mock_load_dotenv):
        """Test successful validation with minimal required variables"""
        config = validate_environment()
        
        assert config == {
            'openrouter_api_key': 'test-key',
            'site_url': None,
            'site_name': None,
            'environment': 'development'  # default value
        }
    
    @patch('main.load_dotenv')
    @patch.dict('os.environ', {}, clear=True)
    def test_validate_environment_missing_api_key(self, mock_load_dotenv):
        """Test validation failure when API key is missing"""
        with pytest.raises(ConfigurationError, match="OPENROUTER_API_KEY environment variable is required"):
            validate_environment()
    
    @patch('main.load_dotenv')
    @patch.dict('os.environ', {'OPENROUTER_API_KEY': ''}, clear=True)
    def test_validate_environment_empty_api_key(self, mock_load_dotenv):
        """Test validation failure when API key is empty"""
        with pytest.raises(ConfigurationError, match="OPENROUTER_API_KEY environment variable is required"):
            validate_environment()


class TestFastAPIEndpoints:
    """Test cases for FastAPI endpoints"""
    
    def setup_method(self):
        """Set up test client with mocked configuration"""
        self.client = TestClient(app)
        
        # Mock the app state configuration
        app.state.config = {
            'openrouter_api_key': 'test-key',
            'site_url': 'https://example.com',
            'site_name': 'Test Site',
            'environment': 'test'
        }
    
    def test_root_endpoint(self):
        """Test root endpoint returns correct response"""
        response = self.client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["message"] == "FastAPI OpenRouter Proxy is running"
        assert data["status"] == "healthy"
        assert data["environment"] == "test"
    
    def test_health_check_endpoint(self):
        """Test health check endpoint returns detailed status"""
        response = self.client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert data["service"] == "FastAPI OpenRouter Proxy"
        assert data["version"] == "0.1.0"
        assert data["environment"] == "test"
        assert data["openrouter_configured"] is True
        assert data["site_configured"] is True
    
    def test_health_check_minimal_config(self):
        """Test health check with minimal configuration"""
        # Mock minimal configuration
        app.state.config = {
            'openrouter_api_key': 'test-key',
            'site_url': None,
            'site_name': None,
            'environment': 'development'
        }
        
        response = self.client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["openrouter_configured"] is True
        assert data["site_configured"] is False
        assert data["environment"] == "development"
    
    def test_health_check_no_config(self):
        """Test health check when no configuration is available"""
        # Remove configuration
        if hasattr(app.state, 'config'):
            delattr(app.state, 'config')
        
        response = self.client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["environment"] == "unknown"
        assert data["openrouter_configured"] is False
        assert data["site_configured"] is False


class TestChatEndpoint:
    """Test cases for chat endpoint"""
    
    def setup_method(self):
        """Set up test client with mocked configuration"""
        self.client = TestClient(app)
        
        # Mock the app state configuration
        app.state.config = {
            'openrouter_api_key': 'test-key',
            'site_url': 'https://example.com',
            'site_name': 'Test Site',
            'environment': 'test'
        }
    
    @patch('main.call_openrouter')
    def test_successful_chat_request(self, mock_call_openrouter):
        """Test successful chat request"""
        mock_call_openrouter.return_value = "Hello! How can I help you today?"
        
        response = self.client.post("/chat", json={
            "message": "Hello",
            "model": "test-model"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["response"] == "Hello! How can I help you today?"
        assert data["status"] == "success"
        assert data["model"] == "test-model"
        
        # Verify OpenRouter was called with correct parameters
        mock_call_openrouter.assert_called_once_with(
            message="Hello",
            api_key="test-key",
            model="test-model",
            site_url="https://example.com",
            site_name="Test Site"
        )
    
    @patch('main.call_openrouter')
    def test_chat_request_with_default_model(self, mock_call_openrouter):
        """Test chat request using default model"""
        mock_call_openrouter.return_value = "Response with default model"
        
        response = self.client.post("/chat", json={
            "message": "Test message"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["response"] == "Response with default model"
        assert data["model"] == "cognitivecomputations/dolphin-mistral-24b-venice-edition:free"
        
        # Verify default model was used
        mock_call_openrouter.assert_called_once_with(
            message="Test message",
            api_key="test-key",
            model="cognitivecomputations/dolphin-mistral-24b-venice-edition:free",
            site_url="https://example.com",
            site_name="Test Site"
        )
    
    def test_chat_request_missing_message(self):
        """Test chat request with missing message"""
        response = self.client.post("/chat", json={
            "model": "test-model"
        })
        
        assert response.status_code == 422  # Pydantic validation error
    
    def test_chat_request_empty_message(self):
        """Test chat request with empty message"""
        response = self.client.post("/chat", json={
            "message": "",
            "model": "test-model"
        })
        
        assert response.status_code == 422  # Pydantic validation error
    
    def test_chat_request_invalid_json(self):
        """Test chat request with invalid JSON"""
        response = self.client.post("/chat", data="invalid json")
        
        assert response.status_code == 422
    
    @patch('main.call_openrouter')
    def test_chat_request_validation_error(self, mock_call_openrouter):
        """Test chat request with validation error from OpenRouter client"""
        mock_call_openrouter.side_effect = ValueError("Message cannot be empty")
        
        response = self.client.post("/chat", json={
            "message": "Test message",
            "model": "test-model"
        })
        
        assert response.status_code == 400
        data = response.json()
        
        assert "Invalid request" in data["detail"]["error"]
        assert data["detail"]["status"] == "error"
        assert data["detail"]["code"] == 400
    
    @patch('main.call_openrouter')
    def test_chat_request_openrouter_unauthorized_error(self, mock_call_openrouter):
        """Test chat request with OpenRouter unauthorized error"""
        mock_call_openrouter.side_effect = OpenRouterError("Invalid API key or unauthorized access")
        
        response = self.client.post("/chat", json={
            "message": "Test message",
            "model": "test-model"
        })
        
        assert response.status_code == 400
        data = response.json()
        
        assert "OpenRouter API error" in data["detail"]["error"]
        assert "unauthorized" in data["detail"]["error"].lower()
        assert data["detail"]["status"] == "error"
        assert data["detail"]["code"] == 400
    
    @patch('main.call_openrouter')
    def test_chat_request_openrouter_server_error(self, mock_call_openrouter):
        """Test chat request with OpenRouter server error"""
        mock_call_openrouter.side_effect = OpenRouterError("Rate limit exceeded")
        
        response = self.client.post("/chat", json={
            "message": "Test message",
            "model": "test-model"
        })
        
        assert response.status_code == 502
        data = response.json()
        
        assert "OpenRouter API error" in data["detail"]["error"]
        assert "Rate limit exceeded" in data["detail"]["error"]
        assert data["detail"]["status"] == "error"
        assert data["detail"]["code"] == 502
    
    @patch('main.call_openrouter')
    def test_chat_request_unexpected_error(self, mock_call_openrouter):
        """Test chat request with unexpected error"""
        mock_call_openrouter.side_effect = Exception("Unexpected error")
        
        response = self.client.post("/chat", json={
            "message": "Test message",
            "model": "test-model"
        })
        
        assert response.status_code == 500
        data = response.json()
        
        assert "Internal server error" in data["detail"]["error"]
        assert data["detail"]["status"] == "error"
        assert data["detail"]["code"] == 500
    
    def test_chat_request_no_configuration(self):
        """Test chat request when app configuration is missing"""
        # Remove configuration
        if hasattr(app.state, 'config'):
            delattr(app.state, 'config')
        
        response = self.client.post("/chat", json={
            "message": "Test message",
            "model": "test-model"
        })
        
        assert response.status_code == 500
        data = response.json()
        
        assert "Application configuration not available" in data["detail"]["error"]
        assert data["detail"]["status"] == "error"
        assert data["detail"]["code"] == 500
    
    def test_chat_request_no_api_key(self):
        """Test chat request when API key is not configured"""
        # Mock configuration without API key
        app.state.config = {
            'openrouter_api_key': None,
            'site_url': 'https://example.com',
            'site_name': 'Test Site',
            'environment': 'test'
        }
        
        response = self.client.post("/chat", json={
            "message": "Test message",
            "model": "test-model"
        })
        
        assert response.status_code == 500
        data = response.json()
        
        assert "OpenRouter API key not configured" in data["detail"]["error"]
        assert data["detail"]["status"] == "error"
        assert data["detail"]["code"] == 500