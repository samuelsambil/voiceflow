# 🎙️ VoiceFlow

AI-powered voice assistant with Microsoft's VibeVoice TTS, Faster-Whisper STT, and Qwen AI that helps you organize your thoughts and plan your day

## Features

- 💬 Chat Mode - Text conversations
- 🎤 Voice Mode - Speak and listen to AI responses
- 🔀 Hybrid Mode - Both text and voice
- 🏋️ Multiple Personalities - Coach, Friend, Executive
- 🎵 4 Voice Options - Emma, James, Sophia, Alex
- 🌅 Daily Briefings
- 🧠 Thought Organization
- 🔥 Streaks & Badges System

## Tech Stack

- **Frontend:** HTML/CSS/JavaScript
- **Backend:** FastAPI
- **AI Models:**
  - Chat: Qwen 2.5 0.5B
  - TTS: Microsoft VibeVoice-Realtime-0.5B
  - STT: Faster-Whisper

## Quick Start

### Option 1: Google Colab (Easiest)

1. Open the Colab notebook
2. Run all cells
3. Get your ngrok URL
4. Open `frontend/index.html` and update the API_URL
5. Open the HTML file in your browser

### Option 2: Deploy to Hugging Face Spaces

See deployment instructions below.

## Deployment

Coming soon: Full deployment guide for Hugging Face Spaces.

## License

MIT License - Free to use and modify!
```

7. **Create `.gitignore`** in the main folder:
```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
*.egg-info/

# Models
*.bin
*.onnx
*.pth

# Audio
*.wav
*.mp3

# Environment
.env
.env.local

# OS
.DS_Store
Thumbs.db