# 🎙️ Echo Note

AI-powered meeting transcription and chatbot assistant using PyTorch ASR and Ollama.

## ✨ Features

- 🎵 **Audio Transcription** - Upload audio files and get AI-generated transcripts
- 🎥 **Live Meeting Recording** - Paste meeting URLs (Zoom/Meet/Teams) and let Echo Note Bot join and transcribe automatically
- 🤖 **AI Chatbot** - Ask questions about your meeting transcripts using Ollama (Gemma 2B)
- 🔐 **JWT Authentication** - Secure user accounts with 24-hour token expiry
- 📝 **Meeting Management** - Organize and access all your transcripts
- 🔍 **Duplicate Detection** - Prevents redundant transcriptions using file hashing

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- Node.js 18+
- Ollama (for chatbot features)
- Recall.ai API Key (for live meeting recording)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/echo-note.git
cd echo-note
```

2. **Install Python dependencies**
```bash
pip install -r requirements.txt
```

3. **Install Node dependencies**
```bash
npm install
```

4. **Install Ollama** (for chatbot)
- Download from: https://ollama.com
- Pull the Gemma 2B model:
```bash
ollama pull gemma:2b
```

5. **Configure Recall.ai** (for live meeting recording - optional)
- Sign up at [Recall.ai](https://www.recall.ai/)
- Get your API key
- Create a `.env` file and add:
```env
RECALL_API_KEY=your_api_key_here
SECRET_KEY=your-secret-key-change-in-production
```
- See [RECALL_SETUP.md](./RECALL_SETUP.md) for detailed setup

6. **Build the frontend**
```bash
npm run build
```

7. **Run the application**
```bash
python app.py
```

8. **Access the app**
Open http://localhost:5000 in your browser

## 📁 Project Structure

```
echo-note/
├── app.py              # Flask backend
├── asr_model.py       # ASR transcription logic
├── chatbot.py         # Ollama chatbot integration
├── recall_integration.py  # Recall.ai bot management
├── .env               # Environment variables (not in git)
├── models/            # ML models
├── data/              # User data (gitignored)
├── uploads/           # Audio files (gitignored)
├── src/               # React source code
├── public/            # Static assets
└── dist/              # Production build
```

## 🛠️ Tech Stack

### Backend
- **Flask** - Web framework
- **PyTorch** - ASR model
- **Ollama** - AI chatbot (Gemma 2B)
- **Recall.ai** - Live meeting bot integration
- **JWT** - Authentication
- **Librosa** - Audio processing

### Frontend
- **React** - UI framework
- **Vite** - Build tool
- **React Router** - Navigation

## 📖 Usage

### Option 1: Upload Audio Files
1. **Sign Up** - Create a new account
2. **Login** - Access your dashboard
3. **Upload Audio** - Go to Meetings → Upload audio file
4. **View Transcript** - See the AI-generated transcript
5. **Chat** - Ask the AI questions about your transcripts

### Option 2: Record Live Meetings (Recall.ai)
1. **Setup** - Follow [RECALL_SETUP.md](./RECALL_SETUP.md) to configure Recall.ai
2. **Login** - Access your dashboard
3. **Paste Meeting URL** - Go to Meetings → Enter Zoom/Meet/Teams URL
4. **Start Bot** - Echo Note Bot will join and record automatically
5. **Get Transcript** - Transcript appears after meeting ends
6. **Chat** - Ask AI questions about the recorded meeting

## 🔒 Security

- Passwords hashed with Werkzeug
- JWT tokens with 24-hour expiry
- Per-user data isolation
- MD5 file hashing for duplicate detection

## 📝 License

MIT License - see LICENSE file for details

## 👥 Contributors

Made with ❤️ by [Your Name]

## 🐛 Issues

Found a bug? [Open an issue](https://github.com/yourusername/echo-note/issues)
