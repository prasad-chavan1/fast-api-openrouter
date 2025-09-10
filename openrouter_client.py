"""
OpenRouter API client implementation using OpenAI library
"""
import os
from typing import Optional
from openai import OpenAI


class OpenRouterError(Exception):
    """Custom exception for OpenRouter API errors"""
    pass


async def call_openrouter(
    message: str, 
    api_key: str, 
    model: str = "cognitivecomputations/dolphin-mistral-24b-venice-edition:free",
    conversation_history: Optional[list] = None,
    site_url: Optional[str] = None,
    site_name: Optional[str] = None
) -> str:
    """
    Call OpenRouter API using OpenAI client library
    
    Args:
        message: The user message to send to the AI model
        api_key: OpenRouter API key
        model: The AI model to use
        conversation_history: Optional list of previous messages for context
        site_url: Optional site URL for OpenRouter rankings
        site_name: Optional site name for OpenRouter rankings
        
    Returns:
        The AI model's response as a string
        
    Raises:
        OpenRouterError: If the API call fails
        ValueError: If required parameters are missing or invalid
    """
    if not message or not message.strip():
        raise ValueError("Message cannot be empty")
    
    if not api_key:
        raise ValueError("API key is required")
    
    if not model:
        raise ValueError("Model is required")
    
    try:
        # Configure OpenAI client for OpenRouter
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )
        
        # Prepare extra headers for OpenRouter rankings (optional)
        extra_headers = {}
        if site_url:
            extra_headers["HTTP-Referer"] = site_url
        if site_name:
            extra_headers["X-Title"] = site_name
        
        # Prepare messages with conversation history
        messages = []
        
        # Add conversation history if provided
        if conversation_history:
            messages.extend(conversation_history)
        
        # Add current user message
        messages.append({
            "role": "user",
            "content": message.strip()
        })
        
        # Make the API call
        completion = client.chat.completions.create(
            extra_headers=extra_headers,
            model=model,
            messages=messages
        )
        
        # Extract the response content
        if not completion.choices or not completion.choices[0].message:
            raise OpenRouterError("No response received from OpenRouter API")
        
        response_content = completion.choices[0].message.content
        if not response_content:
            raise OpenRouterError("Empty response received from OpenRouter API")
        
        return response_content
        
    except Exception as e:
        if isinstance(e, (ValueError, OpenRouterError)):
            raise
        
        # Handle OpenAI/OpenRouter specific errors
        error_message = str(e)
        if "401" in error_message or "unauthorized" in error_message.lower():
            raise OpenRouterError("Invalid API key or unauthorized access")
        elif "429" in error_message or "rate limit" in error_message.lower():
            raise OpenRouterError("Rate limit exceeded")
        elif "404" in error_message or "not found" in error_message.lower():
            raise OpenRouterError(f"Model '{model}' not found or not available")
        elif "400" in error_message or "bad request" in error_message.lower():
            raise OpenRouterError("Invalid request format or parameters")
        else:
            raise OpenRouterError(f"OpenRouter API error: {error_message}")


def get_openrouter_client_config() -> dict:
    """
    Get OpenRouter client configuration from environment variables
    
    Returns:
        Dictionary with client configuration
    """
    return {
        "api_key": os.getenv("OPENROUTER_API_KEY"),
        "site_url": os.getenv("SITE_URL"),
        "site_name": os.getenv("SITE_NAME")
    }