// Global Variables
let currentChatId = null;
let isTyping = false;
let chatSessions = [];

// API Configuration
const API_BASE_URL = 'http://localhost:8000';
const AI_MODEL = 'cognitivecomputations/dolphin-mistral-24b-venice-edition:free';

// DOM Elements
const elements = {
    sidebar: document.getElementById('sidebar'),
    sidebarToggle: document.getElementById('sidebarToggle'),
    newChatBtn: document.getElementById('newChatBtn'),
    chatSessions: document.getElementById('chatSessions'),
    sessionsLoading: document.getElementById('sessionsLoading'),
    welcomeScreen: document.getElementById('welcomeScreen'),
    messages: document.getElementById('messages'),
    messageInput: document.getElementById('messageInput'),
    sendBtn: document.getElementById('sendBtn'),
    typingIndicator: document.getElementById('typingIndicator'),
    charCount: document.getElementById('charCount'),
    chatTitle: document.getElementById('chatTitle'),
    chatSubtitle: document.getElementById('chatSubtitle'),
    clearChatBtn: document.getElementById('clearChatBtn'),
    emojiBtn: document.getElementById('emojiBtn'),
    emojiPicker: document.getElementById('emojiPicker'),
    loadingOverlay: document.getElementById('loadingOverlay'),
    toastContainer: document.getElementById('toastContainer')
};

// Initialize App
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    setupEventListeners();
    loadChatSessions();
});

function initializeApp() {
    // Auto-resize textarea
    elements.messageInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = Math.min(this.scrollHeight, 120) + 'px';
        
        // Update character count
        const count = this.value.length;
        elements.charCount.textContent = `${count}/2000`;
        
        // Enable/disable send button
        elements.sendBtn.disabled = count === 0 || isTyping;
    });

    // Handle Enter key
    elements.messageInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
}

function setupEventListeners() {
    // Sidebar toggle
    elements.sidebarToggle.addEventListener('click', toggleSidebar);
    
    // New chat button
    elements.newChatBtn.addEventListener('click', startNewChat);
    
    // Send button
    elements.sendBtn.addEventListener('click', sendMessage);
    
    // Clear chat button
    elements.clearChatBtn.addEventListener('click', clearCurrentChat);
    
    // Emoji button
    elements.emojiBtn.addEventListener('click', toggleEmojiPicker);
    
    // Emoji picker
    document.querySelectorAll('.emoji').forEach(emoji => {
        emoji.addEventListener('click', function() {
            insertEmoji(this.dataset.emoji);
        });
    });
    
    // Close emoji picker when clicking outside
    document.addEventListener('click', function(e) {
        if (!elements.emojiBtn.contains(e.target) && !elements.emojiPicker.contains(e.target)) {
            elements.emojiPicker.style.display = 'none';
        }
    });
    
    // Close sidebar on mobile when clicking outside
    document.addEventListener('click', function(e) {
        if (window.innerWidth <= 768 && 
            !elements.sidebar.contains(e.target) && 
            !elements.sidebarToggle.contains(e.target) &&
            elements.sidebar.classList.contains('open')) {
            elements.sidebar.classList.remove('open');
        }
    });
}

// Chat Session Management
async function loadChatSessions() {
    try {
        showSessionsLoading(true);
        const response = await fetch(`${API_BASE_URL}/chats`);
        const data = await response.json();
        
        chatSessions = data.sessions || [];
        renderChatSessions();
        
    } catch (error) {
        console.error('Error loading chat sessions:', error);
        showToast('Failed to load chat sessions', 'error');
    } finally {
        showSessionsLoading(false);
    }
}

function renderChatSessions() {
    const container = elements.chatSessions;
    
    if (chatSessions.length === 0) {
        container.innerHTML = `
            <div class="no-sessions">
                <i class="fas fa-comments" style="font-size: 32px; color: #a0aec0; margin-bottom: 12px;"></i>
                <p style="color: #a0aec0; text-align: center; font-size: 14px;">No chat sessions yet.<br>Start a new conversation!</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = '';
    
    chatSessions.forEach(async (sessionId) => {
        try {
            const response = await fetch(`${API_BASE_URL}/chat/${sessionId}`);
            const sessionInfo = await response.json();
            
            const sessionElement = createSessionElement(sessionInfo);
            container.appendChild(sessionElement);
        } catch (error) {
            console.error(`Error loading session ${sessionId}:`, error);
        }
    });
}

function createSessionElement(sessionInfo) {
    const div = document.createElement('div');
    div.className = 'session-item';
    div.dataset.chatId = sessionInfo.chat_id;
    
    if (sessionInfo.chat_id === currentChatId) {
        div.classList.add('active');
    }
    
    const title = generateSessionTitle(sessionInfo);
    const time = formatTime(sessionInfo.updated_at);
    
    div.innerHTML = `
        <div class="session-title">${title}</div>
        <div class="session-preview">${sessionInfo.message_count} messages</div>
        <div class="session-time">${time}</div>
    `;
    
    div.addEventListener('click', () => loadChatSession(sessionInfo.chat_id));
    
    return div;
}

function generateSessionTitle(sessionInfo) {
    // Generate a title based on chat_id or message count
    const shortId = sessionInfo.chat_id.split('-')[0];
    return `Chat ${shortId}`;
}

function formatTime(timestamp) {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now - date;
    
    if (diff < 60000) return 'Just now';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
    return date.toLocaleDateString();
}

async function loadChatSession(chatId) {
    try {
        currentChatId = chatId;
        updateActiveSession();
        
        // Clear current messages
        elements.messages.innerHTML = '';
        elements.welcomeScreen.style.display = 'none';
        
        // Load session messages (you might want to implement this endpoint)
        // For now, we'll just set the active session
        updateChatTitle(`Chat ${chatId.split('-')[0]}`);
        
    } catch (error) {
        console.error('Error loading chat session:', error);
        showToast('Failed to load chat session', 'error');
    }
}

function updateActiveSession() {
    document.querySelectorAll('.session-item').forEach(item => {
        item.classList.remove('active');
        if (item.dataset.chatId === currentChatId) {
            item.classList.add('active');
        }
    });
}

function startNewChat() {
    currentChatId = null;
    elements.messages.innerHTML = '';
    elements.welcomeScreen.style.display = 'flex';
    updateChatTitle('🤖 AI Assistant');
    updateActiveSession();
    
    // Add animation
    elements.welcomeScreen.style.animation = 'none';
    setTimeout(() => {
        elements.welcomeScreen.style.animation = 'fadeInUp 0.5s ease-out';
    }, 10);
}

function clearCurrentChat() {
    if (currentChatId) {
        elements.messages.innerHTML = '';
        showToast('Chat cleared', 'success');
    }
}

// Message Handling
async function sendMessage() {
    const message = elements.messageInput.value.trim();
    if (!message || isTyping) return;
    
    // Clear input
    elements.messageInput.value = '';
    elements.messageInput.style.height = 'auto';
    elements.charCount.textContent = '0/2000';
    elements.sendBtn.disabled = true;
    
    // Hide welcome screen
    elements.welcomeScreen.style.display = 'none';
    
    // Add user message to UI
    addMessageToUI('user', message);
    
    // Show typing indicator
    showTypingIndicator(true);
    
    try {
        // Prepare request
        const requestBody = {
            message: message,
            model: AI_MODEL
        };
        
        if (currentChatId) {
            requestBody.chat_id = currentChatId;
        }
        
        // Send to API
        const response = await fetch(`${API_BASE_URL}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestBody)
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Update current chat ID if it's a new chat
            if (!currentChatId) {
                currentChatId = data.chat_id;
                updateChatTitle(`Chat ${data.chat_id.split('-')[0]}`);
                loadChatSessions(); // Refresh sessions list
            }
            
            // Add AI response to UI
            setTimeout(() => {
                showTypingIndicator(false);
                addMessageToUI('assistant', data.response);
            }, 1000); // Simulate thinking time
            
        } else {
            throw new Error(data.error || 'Failed to send message');
        }
        
    } catch (error) {
        console.error('Error sending message:', error);
        showTypingIndicator(false);
        showToast(error.message || 'Failed to send message', 'error');
    } finally {
        elements.sendBtn.disabled = false;
    }
}

function addMessageToUI(role, content) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    
    const avatar = role === 'user' ? 
        '<i class="fas fa-user"></i>' : 
        '<i class="fas fa-robot"></i>';
    
    const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    
    messageDiv.innerHTML = `
        <div class="message-avatar">${avatar}</div>
        <div class="message-content">
            <div class="message-bubble">${formatMessage(content)}</div>
            <div class="message-time">${time}</div>
        </div>
    `;
    
    elements.messages.appendChild(messageDiv);
    
    // Scroll to bottom with smooth animation
    setTimeout(() => {
        messageDiv.scrollIntoView({ behavior: 'smooth', block: 'end' });
    }, 100);
}

function formatMessage(content) {
    // Basic formatting for better display
    return content
        .replace(/\n/g, '<br>')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/`(.*?)`/g, '<code>$1</code>');
}

function showTypingIndicator(show) {
    isTyping = show;
    elements.typingIndicator.style.display = show ? 'flex' : 'none';
    elements.sendBtn.disabled = show || elements.messageInput.value.trim() === '';
    
    if (show) {
        setTimeout(() => {
            elements.typingIndicator.scrollIntoView({ behavior: 'smooth', block: 'end' });
        }, 100);
    }
}

// UI Helpers
function toggleSidebar() {
    elements.sidebar.classList.toggle('open');
}

function updateChatTitle(title) {
    elements.chatTitle.textContent = title;
}

function showSessionsLoading(show) {
    elements.sessionsLoading.style.display = show ? 'flex' : 'none';
}

function toggleEmojiPicker() {
    const isVisible = elements.emojiPicker.style.display === 'block';
    elements.emojiPicker.style.display = isVisible ? 'none' : 'block';
}

function insertEmoji(emoji) {
    const input = elements.messageInput;
    const start = input.selectionStart;
    const end = input.selectionEnd;
    const text = input.value;
    
    input.value = text.substring(0, start) + emoji + text.substring(end);
    input.focus();
    input.setSelectionRange(start + emoji.length, start + emoji.length);
    
    // Trigger input event to update character count
    input.dispatchEvent(new Event('input'));
    
    elements.emojiPicker.style.display = 'none';
}

function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <div style="display: flex; align-items: center; gap: 8px;">
            <i class="fas fa-${type === 'error' ? 'exclamation-circle' : type === 'success' ? 'check-circle' : 'info-circle'}"></i>
            <span>${message}</span>
        </div>
    `;
    
    elements.toastContainer.appendChild(toast);
    
    // Auto remove after 3 seconds
    setTimeout(() => {
        toast.style.animation = 'slideInRight 0.3s ease-out reverse';
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300);
    }, 3000);
}

function showLoadingOverlay(show) {
    elements.loadingOverlay.style.display = show ? 'flex' : 'none';
}

// Utility Functions
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Handle window resize
window.addEventListener('resize', debounce(() => {
    if (window.innerWidth > 768) {
        elements.sidebar.classList.remove('open');
    }
}, 250));

// Handle online/offline status
window.addEventListener('online', () => {
    showToast('Connection restored', 'success');
});

window.addEventListener('offline', () => {
    showToast('Connection lost', 'error');
});

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
    // Ctrl/Cmd + Enter to send message
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        sendMessage();
    }
    
    // Escape to close emoji picker
    if (e.key === 'Escape') {
        elements.emojiPicker.style.display = 'none';
    }
});

// Initialize tooltips and other enhancements
document.addEventListener('DOMContentLoaded', () => {
    // Add smooth scrolling to all internal links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });
});

// Export functions for testing (if needed)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        sendMessage,
        addMessageToUI,
        formatMessage,
        showToast
    };
}