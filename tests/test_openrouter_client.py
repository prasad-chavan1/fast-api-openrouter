"""
Unit tests for OpenRouter client
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from openrouter_client import call_openrouter, OpenRouterError, get_openrouter_client_config


class TestCallOpenRouter:
    """Test cases for call_openrouter function"""
    
    @pytest.mark.asyncio
    async def test_successful_api_call(self):
        """Test successful OpenRouter API call"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = "Hello! How can I help you?"
        
        with patch('openrouter_client.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client
            
            result = await call_openrouter(
                message="Hello",
                api_key="test-key",
                model="test-model"
            )
            
            assert result == "Hello! How can I help you?"
            
            # Verify OpenAI client was configured correctly
            mock_openai.assert_called_once_with(
                base_url="https://openrouter.ai/api/v1",
                api_key="test-key"
            )
            
            # Verify API call was made with correct parameters
            mock_client.chat.completions.create.assert_called_once_with(
                extra_headers={},
                model="test-model",
                messages=[{"role": "user", "content": "Hello"}]
            )
    
    @pytest.mark.asyncio
    async def test_api_call_with_site_headers(self):
        """Test API call with site URL and name headers"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = "Response with headers"
        
        with patch('openrouter_client.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client
            
            result = await call_openrouter(
                message="Test message",
                api_key="test-key",
                model="test-model",
                site_url="https://example.com",
                site_name="Test Site"
            )
            
            assert result == "Response with headers"
            
            # Verify extra headers were included
            mock_client.chat.completions.create.assert_called_once_with(
                extra_headers={
                    "HTTP-Referer": "https://example.com",
                    "X-Title": "Test Site"
                },
                model="test-model",
                messages=[{"role": "user", "content": "Test message"}]
            )
    
    @pytest.mark.asyncio
    async def test_message_whitespace_trimming(self):
        """Test that message whitespace is trimmed"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = "Trimmed response"
        
        with patch('openrouter_client.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client
            
            await call_openrouter(
                message="  Test message  ",
                api_key="test-key",
                model="test-model"
            )
            
            # Verify message was trimmed
            call_args = mock_client.chat.completions.create.call_args
            messages = call_args[1]['messages']
            assert messages[0]['content'] == "Test message"
    
    @pytest.mark.asyncio
    async def test_empty_message_validation(self):
        """Test validation for empty message"""
        with pytest.raises(ValueError, match="Message cannot be empty"):
            await call_openrouter(
                message="",
                api_key="test-key",
                model="test-model"
            )
    
    @pytest.mark.asyncio
    async def test_whitespace_only_message_validation(self):
        """Test validation for whitespace-only message"""
        with pytest.raises(ValueError, match="Message cannot be empty"):
            await call_openrouter(
                message="   ",
                api_key="test-key",
                model="test-model"
            )
    
    @pytest.mark.asyncio
    async def test_missing_api_key_validation(self):
        """Test validation for missing API key"""
        with pytest.raises(ValueError, match="API key is required"):
            await call_openrouter(
                message="Test message",
                api_key="",
                model="test-model"
            )
    
    @pytest.mark.asyncio
    async def test_missing_model_validation(self):
        """Test validation for missing model"""
        with pytest.raises(ValueError, match="Model is required"):
            await call_openrouter(
                message="Test message",
                api_key="test-key",
                model=""
            )
    
    @pytest.mark.asyncio
    async def test_no_response_choices_error(self):
        """Test error handling when no response choices"""
        mock_response = Mock()
        mock_response.choices = []
        
        with patch('openrouter_client.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client
            
            with pytest.raises(OpenRouterError, match="No response received"):
                await call_openrouter(
                    message="Test message",
                    api_key="test-key",
                    model="test-model"
                )
    
    @pytest.mark.asyncio
    async def test_empty_response_content_error(self):
        """Test error handling when response content is empty"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = None
        
        with patch('openrouter_client.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client
            
            with pytest.raises(OpenRouterError, match="Empty response received"):
                await call_openrouter(
                    message="Test message",
                    api_key="test-key",
                    model="test-model"
                )
    
    @pytest.mark.asyncio
    async def test_unauthorized_error_handling(self):
        """Test handling of 401 unauthorized errors"""
        with patch('openrouter_client.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_client.chat.completions.create.side_effect = Exception("401 Unauthorized")
            mock_openai.return_value = mock_client
            
            with pytest.raises(OpenRouterError, match="Invalid API key or unauthorized access"):
                await call_openrouter(
                    message="Test message",
                    api_key="invalid-key",
                    model="test-model"
                )
    
    @pytest.mark.asyncio
    async def test_rate_limit_error_handling(self):
        """Test handling of rate limit errors"""
        with patch('openrouter_client.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_client.chat.completions.create.side_effect = Exception("429 Rate limit exceeded")
            mock_openai.return_value = mock_client
            
            with pytest.raises(OpenRouterError, match="Rate limit exceeded"):
                await call_openrouter(
                    message="Test message",
                    api_key="test-key",
                    model="test-model"
                )
    
    @pytest.mark.asyncio
    async def test_model_not_found_error_handling(self):
        """Test handling of model not found errors"""
        with patch('openrouter_client.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_client.chat.completions.create.side_effect = Exception("404 Model not found")
            mock_openai.return_value = mock_client
            
            with pytest.raises(OpenRouterError, match="Model 'invalid-model' not found"):
                await call_openrouter(
                    message="Test message",
                    api_key="test-key",
                    model="invalid-model"
                )
    
    @pytest.mark.asyncio
    async def test_bad_request_error_handling(self):
        """Test handling of bad request errors"""
        with patch('openrouter_client.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_client.chat.completions.create.side_effect = Exception("400 Bad Request")
            mock_openai.return_value = mock_client
            
            with pytest.raises(OpenRouterError, match="Invalid request format"):
                await call_openrouter(
                    message="Test message",
                    api_key="test-key",
                    model="test-model"
                )
    
    @pytest.mark.asyncio
    async def test_generic_error_handling(self):
        """Test handling of generic errors"""
        with patch('openrouter_client.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_client.chat.completions.create.side_effect = Exception("Unknown error")
            mock_openai.return_value = mock_client
            
            with pytest.raises(OpenRouterError, match="OpenRouter API error: Unknown error"):
                await call_openrouter(
                    message="Test message",
                    api_key="test-key",
                    model="test-model"
                )


class TestGetOpenRouterClientConfig:
    """Test cases for get_openrouter_client_config function"""
    
    @patch.dict('os.environ', {
        'OPENROUTER_API_KEY': 'test-api-key',
        'SITE_URL': 'https://example.com',
        'SITE_NAME': 'Test Site'
    })
    def test_get_config_with_all_env_vars(self):
        """Test getting config when all environment variables are set"""
        config = get_openrouter_client_config()
        
        assert config == {
            'api_key': 'test-api-key',
            'site_url': 'https://example.com',
            'site_name': 'Test Site'
        }
    
    @patch.dict('os.environ', {'OPENROUTER_API_KEY': 'test-key'}, clear=True)
    def test_get_config_with_minimal_env_vars(self):
        """Test getting config with only required environment variable"""
        config = get_openrouter_client_config()
        
        assert config == {
            'api_key': 'test-key',
            'site_url': None,
            'site_name': None
        }
    
    @patch.dict('os.environ', {}, clear=True)
    def test_get_config_with_no_env_vars(self):
        """Test getting config when no environment variables are set"""
        config = get_openrouter_client_config()
        
        assert config == {
            'api_key': None,
            'site_url': None,
            'site_name': None
        }