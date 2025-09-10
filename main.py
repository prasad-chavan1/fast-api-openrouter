"""
FastAPI OpenRouter Proxy
Main application entry point with environment configuration
"""
import os
import sys
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from models import ChatRequest, ChatResponse, ErrorResponse
from openrouter_client import get_openrouter_client_config, call_openrouter, OpenRouterError


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)
from chat_manager import ChatManager


class ConfigurationError(Exception):
    """Raised when required configuration is missing or invalid"""
    pass


def validate_environment() -> dict:
    """
    Validate required environment variables and return configuration
    
    Returns:
        Dictionary with validated configuration
        
    Raises:
        ConfigurationError: If required environment variables are missing
    """
    # Load environment variables from .env file
    load_dotenv()
    
    config = get_openrouter_client_config()
    
    # Validate required configuration
    if not config["api_key"]:
        raise ConfigurationError(
            "OPENROUTER_API_KEY environment variable is required. "
            "Please set it in your .env file or environment."
        )
    
    # Optional configuration with defaults
    environment = os.getenv("ENVIRONMENT", "development")
    
    return {
        "openrouter_api_key": config["api_key"],
        "site_url": config["site_url"],
        "site_name": config["site_name"],
        "environment": environment
    }


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events
    """
    # Startup
    try:
        app.state.config = validate_environment()
        app.state.chat_manager = ChatManager(storage_dir="chat_logs", max_messages=5)
        print(f"✅ FastAPI OpenRouter Proxy starting in {app.state.config['environment']} mode")
        print("✅ Environment configuration validated successfully")
        print("✅ Chat manager initialized with conversation memory")
    except ConfigurationError as e:
        print(f"❌ Configuration Error: {e}")
        print("❌ Application startup failed")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error during startup: {e}")
        sys.exit(1)
    
    yield
    
    # Shutdown
    print("🔄 FastAPI OpenRouter Proxy shutting down...")


# Create FastAPI application with lifespan manager
app = FastAPI(
    title="FastAPI OpenRouter Proxy",
    description="A simple proxy API for OpenRouter AI conversations",
    version="0.1.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for frontend
app.mount("/static", StaticFiles(directory="Frontend"), name="static")

# Serve CSS and JS files directly
@app.get("/styles.css")
async def get_styles():
    return FileResponse("Frontend/styles.css", media_type="text/css")

@app.get("/script.js")
async def get_script():
    return FileResponse("Frontend/script.js", media_type="application/javascript")


# Custom exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors"""
    logger.warning(f"Validation error for {request.url}: {exc.errors()}")
    
    error_details = []
    for error in exc.errors():
        field = " -> ".join(str(loc) for loc in error["loc"])
        error_details.append(f"{field}: {error['msg']}")
    
    return JSONResponse(
        status_code=400,
        content=ErrorResponse(
            error=f"Validation failed: {'; '.join(error_details)}",
            code=400
        ).model_dump()
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with consistent error format"""
    logger.error(f"HTTP {exc.status_code} error for {request.url}: {exc.detail}")
    
    # If detail is already our ErrorResponse format, return it as-is
    if isinstance(exc.detail, dict) and "error" in exc.detail:
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.detail
        )
    
    # Otherwise, wrap in ErrorResponse format
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=str(exc.detail),
            code=exc.status_code
        ).model_dump()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    logger.error(f"Unexpected error for {request.url}: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal server error occurred",
            code=500
        ).model_dump()
    )


@app.get("/")
async def root():
    """Serve the frontend HTML"""
    return FileResponse("Frontend/index.html")

@app.get("/api/health")
async def health_check_api():
    """Health check endpoint for API"""
    logger.info("API Health check requested")
    return {
        "message": "FastAPI OpenRouter Proxy is running",
        "status": "healthy",
        "environment": getattr(app.state, 'config', {}).get('environment', 'unknown')
    }


@app.get("/health")
async def health_check():
    """Detailed health check endpoint"""
    logger.info("Detailed health check requested")
    config = getattr(app.state, 'config', {})
    
    return {
        "status": "healthy",
        "service": "FastAPI OpenRouter Proxy",
        "version": "0.1.0",
        "environment": config.get('environment', 'unknown'),
        "openrouter_configured": bool(config.get('openrouter_api_key')),
        "site_configured": bool(config.get('site_url') and config.get('site_name'))
    }


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Main chat endpoint that processes messages through OpenRouter API with conversation memory
    
    Args:
        request: ChatRequest containing message, optional chat_id, and optional model
        
    Returns:
        ChatResponse with AI response and chat session info
        
    Raises:
        HTTPException: For various error conditions (400, 500, 502)
    """
    try:
        # Get application configuration and chat manager
        config = getattr(app.state, 'config', {})
        chat_manager = getattr(app.state, 'chat_manager', None)
        
        if not config:
            raise HTTPException(
                status_code=500,
                detail=ErrorResponse(
                    error="Application configuration not available",
                    code=500
                ).model_dump()
            )
        
        if not chat_manager:
            raise HTTPException(
                status_code=500,
                detail=ErrorResponse(
                    error="Chat manager not available",
                    code=500
                ).model_dump()
            )
        
        api_key = config.get('openrouter_api_key')
        if not api_key:
            raise HTTPException(
                status_code=500,
                detail=ErrorResponse(
                    error="OpenRouter API key not configured",
                    code=500
                ).model_dump()
            )
        
        # Handle chat session
        chat_id = request.chat_id
        if not chat_id:
            # Create new session
            chat_id = chat_manager.create_session(request.model)
        
        # Get conversation history
        conversation_history = chat_manager.get_conversation_history(chat_id)
        
        # Add user message to session
        try:
            chat_manager.add_message(chat_id, "user", request.message)
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=ErrorResponse(
                    error=f"Invalid chat session: {str(e)}",
                    code=400
                ).model_dump()
            )
        
        # Call OpenRouter API with conversation history
        try:
            ai_response = await call_openrouter(
                message=request.message,
                api_key=api_key,
                model=request.model,
                conversation_history=conversation_history,
                site_url=config.get('site_url'),
                site_name=config.get('site_name')
            )
            
            # Add AI response to session
            session = chat_manager.add_message(chat_id, "assistant", ai_response)
            
            # Return successful response
            return ChatResponse(
                response=ai_response,
                chat_id=chat_id,
                model=request.model,
                message_count=len(session.messages)
            )
            
        except ValueError as e:
            # Handle validation errors (400)
            raise HTTPException(
                status_code=400,
                detail=ErrorResponse(
                    error=f"Invalid request: {str(e)}",
                    code=400
                ).model_dump()
            )
            
        except OpenRouterError as e:
            # Handle OpenRouter API errors (502)
            error_message = str(e)
            
            # Determine if it's a client error (400) or server error (502)
            if any(keyword in error_message.lower() for keyword in ['invalid', 'unauthorized', 'bad request']):
                status_code = 400
            else:
                status_code = 502
                
            raise HTTPException(
                status_code=status_code,
                detail=ErrorResponse(
                    error=f"OpenRouter API error: {error_message}",
                    code=status_code
                ).model_dump()
            )
            
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
        
    except Exception as e:
        # Handle unexpected errors (500)
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error=f"Internal server error: {str(e)}",
                code=500
            ).model_dump()
        )


@app.get("/chat/{chat_id}")
async def get_chat_session(chat_id: str):
    """
    Get information about a specific chat session
    
    Args:
        chat_id: Chat session ID
        
    Returns:
        Chat session information
    """
    chat_manager = getattr(app.state, 'chat_manager', None)
    
    if not chat_manager:
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="Chat manager not available",
                code=500
            ).model_dump()
        )
    
    session_info = chat_manager.get_session_info(chat_id)
    if not session_info:
        raise HTTPException(
            status_code=404,
            detail=ErrorResponse(
                error=f"Chat session {chat_id} not found",
                code=404
            ).model_dump()
        )
    
    return session_info


@app.get("/chat/{chat_id}/messages")
async def get_chat_messages(chat_id: str):
    """
    Get all messages from a specific chat session
    
    Args:
        chat_id: Chat session ID
        
    Returns:
        List of messages in the chat session
    """
    chat_manager = getattr(app.state, 'chat_manager', None)
    
    if not chat_manager:
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="Chat manager not available",
                code=500
            ).model_dump()
        )
    
    session = chat_manager.get_session(chat_id)
    if not session:
        raise HTTPException(
            status_code=404,
            detail=ErrorResponse(
                error=f"Chat session {chat_id} not found",
                code=404
            ).model_dump()
        )
    
    # Return messages in a format suitable for the frontend
    messages = []
    for msg in session.messages:
        messages.append({
            "role": msg.role,
            "content": msg.content,
            "timestamp": msg.timestamp.isoformat()
        })
    
    return {
        "chat_id": chat_id,
        "messages": messages,
        "total_count": len(messages)
    }


@app.get("/chats")
async def list_chat_sessions():
    """
    List all available chat sessions
    
    Returns:
        List of chat session IDs
    """
    chat_manager = getattr(app.state, 'chat_manager', None)
    
    if not chat_manager:
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="Chat manager not available",
                code=500
            ).model_dump()
        )
    
    sessions = chat_manager.list_sessions()
    return {"sessions": sessions, "count": len(sessions)}


if __name__ == "__main__":
    import uvicorn
    
    # Load environment for development
    load_dotenv()
    
    # Get configuration for development server
    try:
        config = validate_environment()
        environment = config.get('environment', 'development')
        
        # Configure development server
        reload = environment == 'development'
        log_level = "debug" if environment == 'development' else "info"
        
        print(f"🚀 Starting FastAPI OpenRouter Proxy in {environment} mode")
        
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8000,
            reload=reload,
            log_level=log_level
        )
        
    except ConfigurationError as e:
        print(f"❌ Configuration Error: {e}")
        print("❌ Please check your .env file and try again")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)