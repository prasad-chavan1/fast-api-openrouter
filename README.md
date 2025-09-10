# AI Chat Application

A simple web application that lets you chat with AI using OpenRouter. It has a nice web interface and remembers your conversations.

## What This Does

- Chat with AI through a web browser
- Saves your conversations so you can come back to them later
- Uses OpenRouter to connect to different AI models
- Has a clean, modern web interface

## What You Need

- Python 3.8 or newer
- An OpenRouter API key (get one free at openrouter.ai)
- Internet connection

## How to Set It Up

### Step 1: Get the Code
Download or clone this project to your computer.

### Step 2: Install Python Dependencies

**Option A: Using pip (simple way)**
```bash
pip install -r requirements.txt
```

**Option B: Using uv (recommended)**
```bash
# Install uv first: https://docs.astral.sh/uv/getting-started/installation/
uv venv
uv pip install -r requirements.txt
```

### Step 3: Set Up Your API Key

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit the `.env` file and add your OpenRouter API key:
   ```
   OPENROUTER_API_KEY=your_api_key_here
   ```

## How to Run It

### Start the Server
```bash
python main.py
```

Or if using uv:
```bash
uv run python main.py
```

### Open in Browser
Go to: http://localhost:8000

That's it! You should see the chat interface.

## How to Use It

1. **Start Chatting**: Type a message and press Enter or click the send button
2. **New Conversations**: Click "New Chat" to start a fresh conversation
3. **Switch Conversations**: Click on any chat in the left sidebar to continue that conversation
4. **View History**: All your conversations are saved and you can switch between them anytime

## Testing

### Test the Whole Application
```bash
python test_project.py
```

### Run Individual Tests
```bash
pytest tests/ -v
```

### Test Just the API
Go to http://localhost:8000/docs to see the API documentation and test endpoints.

## Project Files

```
├── main.py              # Main server application
├── models.py            # Data structures for requests/responses  
├── openrouter_client.py # Handles communication with OpenRouter
├── chat_manager.py      # Manages conversation history
├── Frontend/            # Web interface files
│   └── index.html       # The chat web page
├── tests/               # Test files
├── chat_logs/           # Where conversations are saved
├── requirements.txt     # Python dependencies
├── .env                 # Your API key (create this)
└── .env.example         # Template for .env file
```

## Configuration

Edit the `.env` file to change settings:

- `OPENROUTER_API_KEY` - Your API key (required)
- `ENVIRONMENT` - Set to "production" for live use
- `SITE_URL` - Your website URL (optional)
- `SITE_NAME` - Your website name (optional)

## Troubleshooting

### Server Won't Start
- Check that you have Python 3.8+
- Make sure all dependencies are installed
- Verify your API key is set in the `.env` file

### Can't Connect to AI
- Check your internet connection
- Verify your OpenRouter API key is valid
- Look at the server logs for error messages

### Chat History Not Loading
- Check that the `chat_logs/` folder exists
- Make sure the server has permission to write files
- Try refreshing the web page

### Web Interface Not Working
- Make sure the server is running on port 8000
- Try opening http://localhost:8000 in a different browser
- Check the browser console for JavaScript errors

## Getting Help

1. Check the server logs in your terminal
2. Look at the browser console (F12) for errors
3. Try the API directly at http://localhost:8000/docs
4. Make sure your OpenRouter API key is working

## What AI Model It Uses

By default, it uses "Dolphin Mistral 24B" which is free and works well for most conversations. You can change this in the code if you want to use a different model.

## Stopping the Server

Press `Ctrl+C` in the terminal where the server is running.