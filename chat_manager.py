"""
Chat session manager for handling conversation history and file storage
"""
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from models import ChatSession, ChatMessage


class ChatManager:
    """Manages chat sessions with conversation history and file persistence"""
    
    def __init__(self, storage_dir: str = "chat_logs", max_messages: int = 5):
        """
        Initialize chat manager
        
        Args:
            storage_dir: Directory to store chat log files
            max_messages: Maximum number of message pairs to keep in memory (default: 5)
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        self.max_messages = max_messages
        self.active_sessions: Dict[str, ChatSession] = {}
    
    def create_session(self, model: str) -> str:
        """
        Create a new chat session
        
        Args:
            model: AI model to use for this session
            
        Returns:
            New chat session ID
        """
        chat_id = str(uuid.uuid4())
        session = ChatSession(
            chat_id=chat_id,
            model=model,
            messages=[]
        )
        self.active_sessions[chat_id] = session
        return chat_id
    
    def get_session(self, chat_id: str) -> Optional[ChatSession]:
        """
        Get existing chat session
        
        Args:
            chat_id: Chat session ID
            
        Returns:
            ChatSession if exists, None otherwise
        """
        if chat_id in self.active_sessions:
            return self.active_sessions[chat_id]
        
        # Try to load from file if not in memory
        return self._load_session_from_file(chat_id)
    
    def add_message(self, chat_id: str, role: str, content: str) -> ChatSession:
        """
        Add a message to the chat session
        
        Args:
            chat_id: Chat session ID
            role: Message role (user/assistant)
            content: Message content
            
        Returns:
            Updated ChatSession
        """
        session = self.get_session(chat_id)
        if not session:
            raise ValueError(f"Chat session {chat_id} not found")
        
        # Add new message
        message = ChatMessage(role=role, content=content)
        session.messages.append(message)
        session.updated_at = datetime.now()
        
        # Keep only the last max_messages pairs (user + assistant = 1 pair)
        # So we keep max_messages * 2 total messages
        max_total_messages = self.max_messages * 2
        if len(session.messages) > max_total_messages:
            session.messages = session.messages[-max_total_messages:]
        
        # Update active session
        self.active_sessions[chat_id] = session
        
        # Save to file
        self._save_session_to_file(session)
        
        return session
    
    def get_conversation_history(self, chat_id: str) -> List[Dict[str, str]]:
        """
        Get conversation history formatted for OpenRouter API
        
        Args:
            chat_id: Chat session ID
            
        Returns:
            List of messages formatted for OpenAI/OpenRouter API
        """
        session = self.get_session(chat_id)
        if not session:
            return []
        
        return [
            {"role": msg.role, "content": msg.content}
            for msg in session.messages
        ]
    
    def _save_session_to_file(self, session: ChatSession):
        """Save chat session to JSON file"""
        file_path = self.storage_dir / f"{session.chat_id}.json"
        
        # Convert to dict for JSON serialization
        session_data = {
            "chat_id": session.chat_id,
            "model": session.model,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
            "messages": [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat()
                }
                for msg in session.messages
            ]
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)
    
    def _load_session_from_file(self, chat_id: str) -> Optional[ChatSession]:
        """Load chat session from JSON file"""
        file_path = self.storage_dir / f"{chat_id}.json"
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            # Convert back to ChatSession model
            messages = [
                ChatMessage(
                    role=msg["role"],
                    content=msg["content"],
                    timestamp=datetime.fromisoformat(msg["timestamp"])
                )
                for msg in session_data["messages"]
            ]
            
            session = ChatSession(
                chat_id=session_data["chat_id"],
                model=session_data["model"],
                created_at=datetime.fromisoformat(session_data["created_at"]),
                updated_at=datetime.fromisoformat(session_data["updated_at"]),
                messages=messages
            )
            
            # Add to active sessions
            self.active_sessions[chat_id] = session
            return session
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"Error loading session {chat_id}: {e}")
            return None
    
    def list_sessions(self) -> List[str]:
        """List all available chat session IDs"""
        session_files = list(self.storage_dir.glob("*.json"))
        return [f.stem for f in session_files]
    
    def get_session_info(self, chat_id: str) -> Optional[Dict]:
        """Get basic info about a chat session"""
        session = self.get_session(chat_id)
        if not session:
            return None
        
        return {
            "chat_id": session.chat_id,
            "model": session.model,
            "message_count": len(session.messages),
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat()
        }