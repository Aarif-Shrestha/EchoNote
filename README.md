# 🎙️ Echo Note

AI-powered meeting transcription and chatbot assistant using PyTorch ASR and Ollama.

## ✨ Features

- 🎵 **Audio Transcription** - Upload audio files and get AI-generated transcripts
- 🎥 **Live Meeting Recording** - Paste meeting URLs (Zoom/Meet/Teams) and let Echo Note Bot join and transcribe automatically
- 🤖 **AI Chatbot** - Ask questions about your meeting transcripts using Ollama (Gemma 2B)
- 🔐 **JWT Authentication** - Secure user accounts with 24-hour token expiry
- 📝 **Meeting Management** - Organize and access all your transcripts
- 🔍 **Duplicate Detection** - Prevents redundant transcriptions using file hashing


## Link to model (make sure to put it inside the models folder):
    https://drive.google.com/file/d/1KMtQ-ruvNoCU5OlGZpqQ-M43yb7dQ7EV/view?usp=sharing


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

### Initialize data folder (important for first-time clones)

This project stores small JSON files under the `data/` directory. Some clones may not include the `data/` directory (it's commonly gitignored). Before running the app for the first time, create default data files by running:

```powershell
python setup_data.py
```

That script will create `data/users.json`, `data/transcripts.json`, `data/audios.json`, and `data/bot_meetings.json` with safe empty defaults if they don't exist. It will NOT overwrite existing files.

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

## Large model files (important)

This project uses pre-trained model weights that are too large to include in the repository. To avoid pushing large files to GitHub, please do not commit model binaries (for example `*.pth`, `*.pt`, `*.bin`, `*.ckpt`, `*.safetensors`).

What we did in this repo
- The `models/` directory is present but large model files are gitignored via `.gitignore`.
- A small placeholder file `models/.gitkeep` is tracked so the folder exists after cloning.

How to add the model locally
1. Download the model file from this Drive link (replace the placeholder with the real URL):

	https://drive.google.com/file/d/1KMtQ-ruvNoCU5OlGZpqQ-M43yb7dQ7EV/view?usp=sharing

2. Place the downloaded file into the `models/` folder in the project root. Example:

```text
echo-note/models/whisper_base.pth
```

3. Do NOT `git add` or commit the model file. It's ignored by `.gitignore`.

If you accidentally added a large model file and Git rejects your push (or GitHub blocks it for being >100MB), remove it from the index with the following commands locally and then push:

```powershell
# stop tracking the file but keep it locally
git rm --cached models/whisper_base.pth
git commit -m "Remove large model file from repository"
git push origin main
```

If the large file was already committed in previous commits and needs to be removed from history, use a history-cleaning tool such as `git filter-repo` or `bfg` and follow GitHub's guidance: https://docs.github.com/en/repositories/working-with-files/managing-large-files/removing-files-from-a-repositorys-history

Alternative: Use Git LFS
- If you prefer to store large model files in the repository, consider using Git LFS (Large File Storage). See: https://git-lfs.github.com/ and GitHub docs on enabling LFS for your repo.

Questions?
If you'd like, I can run the local `git rm --cached` step for you now (it will create a commit that removes the file from the index but keeps it on disk). Say "yes, remove the committed model" and I'll run the commands here.
