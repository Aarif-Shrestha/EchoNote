from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
import uuid
import os
import json
import jwt
import datetime
import hashlib

# Add ffmpeg to PATH for Whisper (Windows fix)
ffmpeg_paths = [
    r"C:\ffmpeg\bin",
    os.path.expanduser(r"~\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.0-full_build\bin"),
    r"C:\ProgramData\chocolatey\bin",
    os.path.expanduser(r"~\scoop\shims")
]
for ffmpeg_path in ffmpeg_paths:
    if os.path.exists(ffmpeg_path) and ffmpeg_path not in os.environ["PATH"]:
        os.environ["PATH"] = ffmpeg_path + os.pathsep + os.environ["PATH"]
        print(f"✅ Added {ffmpeg_path} to PATH")
        break
from asr_model import ASRTranscriber
from chatbot import is_strict_greeting, ask_ollama, get_greeting_response
from meetingbaas_integration import create_meeting_bot, get_bot_status, get_transcript
from dotenv import load_dotenv
from auto_fetch import start_auto_fetch

# Load environment variables
load_dotenv()

# Path to React build folder
REACT_BUILD_DIR = os.path.join(os.path.dirname(__file__), 'dist')

# Data storage paths
USERS_FILE = os.path.join(os.path.dirname(__file__), 'data', 'users.json')
AUDIOS_FILE = os.path.join(os.path.dirname(__file__), 'data', 'audios.json')
TRANSCRIPTS_FILE = os.path.join(os.path.dirname(__file__), 'data', 'transcripts.json')
UPLOADS_DIR = os.path.join(os.path.dirname(__file__), 'uploads')
# Note: Whisper loads its own model, no custom path needed

# Allowed audio file extensions
ALLOWED_EXTENSIONS = {'mp3', 'wav', 'ogg', 'm4a', 'flac', 'aac', 'webm'}

# JWT Secret Key (change this to a random secret key in production)
SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-change-this-in-production')

# Initialize Flask app
app = Flask(__name__, static_folder=REACT_BUILD_DIR, static_url_path='/')
app.config['SECRET_KEY'] = SECRET_KEY
CORS(app)

# Ensure uploads directory exists
os.makedirs(UPLOADS_DIR, exist_ok=True)

# Initialize ASR transcriber (lazy loading)
transcriber = None

def get_transcriber():
    """Lazy load the ASR transcriber"""
    global transcriber
    if transcriber is None:
        try:
            print("🔄 Loading Whisper ASR model...")
            transcriber = ASRTranscriber()  # Whisper loads its own model
        except Exception as e:
            print(f"❌ Failed to load ASR model: {str(e)}")
            import traceback
            traceback.print_exc()
            transcriber = None
    return transcriber


def calculate_file_hash(file_path):
    """Calculate MD5 hash of a file"""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def find_duplicate_audio(current_user_id, file_hash):
    """Check if user already has this audio file (by hash)"""
    audios = load_audios()
    user_audios = audios.get(current_user_id, {})
    
    for meeting_id, meeting_info in user_audios.items():
        if meeting_info.get('file_hash') == file_hash:
            return meeting_id  # Return the existing meeting_id
    return None


def load_users():
    """Load users from JSON file"""
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r') as f:
                content = f.read().strip()
                if content:
                    return json.loads(content)
        except (json.JSONDecodeError, ValueError):
            pass
    return {}


def save_users(users):
    """Save users to JSON file. Ensure data directory exists before writing."""
    os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, indent=2, ensure_ascii=False)


def load_audios():
    """Load audio metadata from JSON file"""
    if os.path.exists(AUDIOS_FILE):
        try:
            with open(AUDIOS_FILE, 'r') as f:
                content = f.read().strip()
                if content:
                    return json.loads(content)
        except (json.JSONDecodeError, ValueError):
            pass
    return {}


def save_audios(audios):
    """Save audio metadata to JSON file. Ensure data directory exists before writing."""
    os.makedirs(os.path.dirname(AUDIOS_FILE), exist_ok=True)
    with open(AUDIOS_FILE, 'w', encoding='utf-8') as f:
        json.dump(audios, f, indent=2, ensure_ascii=False)


def load_transcripts():
    """Load transcripts from JSON file"""
    if os.path.exists(TRANSCRIPTS_FILE):
        try:
            with open(TRANSCRIPTS_FILE, 'r') as f:
                content = f.read().strip()
                if content:
                    return json.loads(content)
        except (json.JSONDecodeError, ValueError):
            pass
    return {}


def save_transcripts(transcripts):
    """Save transcripts to JSON file. Ensure data directory exists before writing."""
    os.makedirs(os.path.dirname(TRANSCRIPTS_FILE), exist_ok=True)
    with open(TRANSCRIPTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(transcripts, f, indent=2, ensure_ascii=False)


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def token_required(f):
    """Decorator to protect routes with JWT authentication"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Check if token is in headers
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(' ')[1]  # Bearer <token>
            except IndexError:
                return jsonify({'error': 'Invalid token format'}), 401
        
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        try:
            # Decode token
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user_id = data['user_id']
            current_username = data['username']
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        
        return f(current_user_id, current_username, *args, **kwargs)
    
    return decorated


@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    # Validate input
    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400
    
    if len(username.strip()) == 0 or len(password.strip()) == 0:
        return jsonify({'error': 'Username and password cannot be empty'}), 400
    
    # Load existing users
    users = load_users()
    
    # Check if user already exists
    if username in users:
        return jsonify({'error': 'User already exists'}), 409
    
    # Create new user
    user_id = str(uuid.uuid4())
    users[username] = {
        'id': user_id,
        'username': username,
        'password_hash': generate_password_hash(password)
    }
    
    # Save to file
    save_users(users)
    
    # Create user's upload directory
    user_upload_dir = os.path.join(UPLOADS_DIR, user_id)
    os.makedirs(user_upload_dir, exist_ok=True)
    
    return jsonify({
        'message': 'User created successfully',
        'redirect': '/login'  # Frontend should redirect to login page
    }), 201


@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        # Validate input
        if not username or not password:
            return jsonify({'error': 'Username and password required'}), 400
        
        # Load users
        users = load_users()
        
        # Check if username exists
        if username not in users:
            return jsonify({'error': 'Username does not exist'}), 404
        
        user = users[username]
        
        # Check password
        if not check_password_hash(user['password_hash'], password):
            return jsonify({'error': 'Wrong password'}), 401
        
        # Load user's audio files
        audios = load_audios()
        user_audios = audios.get(user['id'], {})
        
        # Generate JWT token (expires in 24 hours)
        token = jwt.encode({
            'user_id': user['id'],
            'username': user['username'],
            'exp': datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=24)
        }, app.config['SECRET_KEY'], algorithm='HS256')

        # PyJWT v1 returned bytes; ensure token is a string
        if isinstance(token, bytes):
            try:
                token = token.decode('utf-8')
            except Exception:
                # fallback: convert to str
                token = str(token)

        return jsonify({
            'message': 'Login successful',
            'token': token,
            'user': {
                'id': user['id'],
                'username': user['username'],
                'audio_files': user_audios
            },
            'redirect': '/home'  # Frontend should redirect to home page
        }), 200

    except Exception as e:
        # Log stacktrace server-side and return a JSON error so frontend doesn't show a generic "Network error"
        print(f"❌ Login error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500


@app.route('/api/verify_token', methods=['GET'])
@token_required
def verify_token(current_user_id, current_username):
    """Verify if token is valid and return user info"""
    # Load user's audio files
    audios = load_audios()
    user_audios = audios.get(current_user_id, {})
    
    return jsonify({
        'valid': True,
        'user': {
            'id': current_user_id,
            'username': current_username,
            'audio_files': user_audios
        }
    }), 200


@app.route('/api/upload_audio', methods=['POST'])
@token_required
def upload_audio(current_user_id, current_username):
    """Upload audio file and generate transcript - requires JWT authentication"""
    # Check if file is present
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    meeting_name = request.form.get('meeting_name', 'Untitled Meeting')
    
    # Check if file is selected
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Validate file type
    if not allowed_file(file.filename):
        return jsonify({'error': f'Invalid file type. Allowed: {", ".join(ALLOWED_EXTENSIONS)}'}), 400
    
    # Secure the filename
    filename = secure_filename(file.filename)
    
    # Add timestamp to filename to avoid conflicts
    import time
    timestamp = int(time.time())
    name, ext = os.path.splitext(filename)
    unique_filename = f"{name}_{timestamp}{ext}"
    
    # Create user directory if it doesn't exist
    user_upload_dir = os.path.join(UPLOADS_DIR, current_user_id)
    os.makedirs(user_upload_dir, exist_ok=True)
    
    # Save file temporarily to calculate hash
    temp_file_path = os.path.join(user_upload_dir, unique_filename)
    file.save(temp_file_path)
    
    # Calculate file hash to check for duplicates
    file_hash = calculate_file_hash(temp_file_path)
    
    # Check if this exact file already exists for this user
    existing_meeting_id = find_duplicate_audio(current_user_id, file_hash)
    
    if existing_meeting_id:
        # Delete the newly uploaded duplicate file
        os.remove(temp_file_path)
        
        # Get existing transcript
        transcripts = load_transcripts()
        existing_transcript_data = transcripts.get(current_user_id, {}).get(existing_meeting_id, {})
        # Handle both old format (string) and new format (dict with 'transcript' key)
        if isinstance(existing_transcript_data, dict):
            existing_transcript = existing_transcript_data.get('transcript', "No transcript available")
        else:
            existing_transcript = existing_transcript_data if existing_transcript_data else "No transcript available"
        
        # Get existing meeting info
        audios = load_audios()
        existing_meeting = audios.get(current_user_id, {}).get(existing_meeting_id, {})
        
        print(f"⚠️ Duplicate file detected for user {current_username}. Using existing transcript.")
        
        return jsonify({
            'message': 'This audio file already exists. Showing existing transcript.',
            'transcript': existing_transcript,
            'meeting_id': existing_meeting_id,
            'meeting_name': existing_meeting.get('meeting_name', 'Untitled Meeting'),
            'is_duplicate': True
        }), 200
    
    # Not a duplicate - proceed with transcription
    file_path = temp_file_path
    meeting_id = str(uuid.uuid4())
    
    # Generate transcript
    transcript = "Transcript generation in progress..."
    try:
        asr = get_transcriber()
        print(f"🔍 ASR instance: {asr}")
        if asr:
            print(f"🔍 ASR model loaded: {asr.asr_model is not None}")
        if asr and asr.asr_model:
            print(f"🎤 Transcribing audio for user {current_username}...")
            transcript = asr.transcribe(file_path)
            print(f"✅ Transcription complete! Length: {len(transcript)}")
        else:
            transcript = "Transcription service unavailable. Model not loaded."
            print("⚠️ ASR model not available")
    except Exception as e:
        transcript = f"Error during transcription: {str(e)}"
        print(f"❌ Transcription error: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Save transcript with username for easy identification
    transcripts = load_transcripts()
    if current_user_id not in transcripts:
        transcripts[current_user_id] = {}
    transcripts[current_user_id][meeting_id] = {
        'username': current_username,  # Added username for easy identification
        'transcript': transcript,
        'meeting_name': meeting_name
    }
    save_transcripts(transcripts)
    
    # Update audio metadata with file hash and username
    audios = load_audios()
    if current_user_id not in audios:
        audios[current_user_id] = {}
    
    audios[current_user_id][meeting_id] = {
        'username': current_username,  # Added username for easy identification
        'meeting_name': meeting_name,
        'filename': unique_filename,
        'upload_date': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'file_hash': file_hash  # Store hash to detect future duplicates
    }
    save_audios(audios)
    
    return jsonify({
        'message': 'Audio uploaded and transcribed successfully',
        'meeting_id': meeting_id,
        'meeting_name': meeting_name,
        'filename': unique_filename,
        'transcript': transcript
    }), 201


@app.route('/api/user_audios', methods=['GET'])
@token_required
def get_user_audios(current_user_id, current_username):
    """Get list of audio files for authenticated user"""
    audios = load_audios()
    user_audios = audios.get(current_user_id, {})
    return jsonify({'audio_files': user_audios}), 200


@app.route('/api/user_meetings', methods=['GET'])
@token_required
def get_user_meetings(current_user_id, current_username):
    """Get all meetings with transcripts for authenticated user"""
    audios = load_audios()
    transcripts = load_transcripts()
    
    user_meetings = audios.get(current_user_id, {})
    user_transcripts = transcripts.get(current_user_id, {})
    
    meetings = []
    for meeting_id, meeting_info in user_meetings.items():
        # Handle both old format (string) and new format (dict)
        transcript_data = user_transcripts.get(meeting_id, {})
        if isinstance(transcript_data, dict):
            transcript = transcript_data.get('transcript', 'No transcript available')
        else:
            transcript = transcript_data if transcript_data else 'No transcript available'
        
        meetings.append({
            'meeting_id': meeting_id,
            'meeting_name': meeting_info.get('meeting_name', 'Untitled Meeting'),
            'filename': meeting_info.get('filename', ''),
            'upload_date': meeting_info.get('upload_date', ''),
            'transcript': transcript
        })
    
    return jsonify({'meetings': meetings}), 200


@app.route('/api/meeting/<meeting_id>', methods=['GET'])
@token_required
def get_meeting(current_user_id, current_username, meeting_id):
    """Get specific meeting details with transcript"""
    audios = load_audios()
    transcripts = load_transcripts()
    
    user_meetings = audios.get(current_user_id, {})
    user_transcripts = transcripts.get(current_user_id, {})
    
    if meeting_id not in user_meetings:
        return jsonify({'error': 'Meeting not found'}), 404
    
    meeting_info = user_meetings[meeting_id]
    
    # Handle both old format (string) and new format (dict)
    transcript_data = user_transcripts.get(meeting_id, {})
    if isinstance(transcript_data, dict):
        transcript = transcript_data.get('transcript', 'No transcript available')
    else:
        transcript = transcript_data if transcript_data else 'No transcript available'
    
    return jsonify({
        'meeting_id': meeting_id,
        'meeting_name': meeting_info.get('meeting_name', 'Untitled Meeting'),
        'filename': meeting_info.get('filename', ''),
        'upload_date': meeting_info.get('upload_date', ''),
        'transcript': transcript
    }), 200


@app.route('/api/audio/<filename>', methods=['GET'])
@token_required
def serve_audio(current_user_id, current_username, filename):
    """Serve audio file for authenticated user"""
    user_upload_dir = os.path.join(UPLOADS_DIR, current_user_id)
    
    # Check if file exists in user's directory
    file_path = os.path.join(user_upload_dir, filename)
    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 404
    
    return send_from_directory(user_upload_dir, filename)


@app.route('/api/chat', methods=['POST'])
@token_required
def chat_with_ollama(current_user_id, current_username):
    """Chat endpoint for Ollama integration"""
    data = request.get_json()
    transcript = data.get('transcript', '')
    question = data.get('question', '')
    chat_history = data.get('chat_history', [])
    model_name = data.get('model_name', 'gemma:2b')
    
    if not transcript:
        return jsonify({'error': 'No transcript provided'}), 400
    
    if not question:
        return jsonify({'error': 'No question provided'}), 400
    
    # Check for greetings
    if is_strict_greeting(question):
        return jsonify({'answer': get_greeting_response()}), 200
    
    # Ask Ollama (imported from chatbot.py)
    response = ask_ollama(transcript, question, chat_history, model_name)
    
    if 'error' in response:
        return jsonify(response), 500
    
    return jsonify(response), 200


# ============= RECALL.AI MEETING BOT ENDPOINTS =============

# Storage for bot_id to user mapping
BOT_MEETINGS_FILE = os.path.join(os.path.dirname(__file__), 'data', 'bot_meetings.json')

def load_bot_meetings():
    """Load bot meetings mapping"""
    if os.path.exists(BOT_MEETINGS_FILE):
        try:
            with open(BOT_MEETINGS_FILE, 'r') as f:
                content = f.read().strip()
                if content:
                    return json.loads(content)
        except (json.JSONDecodeError, ValueError):
            pass
    return {}

def save_bot_meetings(bot_meetings):
    """Save bot meetings mapping. Ensure data directory exists before writing."""
    os.makedirs(os.path.dirname(BOT_MEETINGS_FILE), exist_ok=True)
    with open(BOT_MEETINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(bot_meetings, f, indent=2, ensure_ascii=False)


@app.route('/api/record_meeting', methods=['POST'])
@token_required
def record_meeting(current_user_id, current_username):
    """Start MeetingBaas bot to join and record a meeting"""
    data = request.get_json()
    meeting_url = data.get('meeting_url', '').strip()
    meeting_name = data.get('meeting_name', 'Recorded Meeting')
    
    if not meeting_url:
        return jsonify({'error': 'Meeting URL is required'}), 400
    
    # Validate meeting URL format
    if not any(platform in meeting_url.lower() for platform in ['zoom.us', 'meet.google.com', 'teams.microsoft.com']):
        return jsonify({'error': 'Invalid meeting URL. Must be Zoom, Google Meet, or Microsoft Teams'}), 400
    
    # Create MeetingBaas bot
    result = create_meeting_bot(meeting_url, meeting_name="Echo Note Bot")
    
    if not result['success']:
        return jsonify({'error': result.get('message', 'Failed to create bot')}), 500
    
    # Store bot_id with user info
    bot_meetings = load_bot_meetings()
    bot_id = result['bot_id']
    bot_meetings[bot_id] = {
        'user_id': current_user_id,
        'username': current_username,
        'meeting_name': meeting_name,
        'meeting_url': meeting_url,
        'created_at': datetime.datetime.now(datetime.timezone.utc).isoformat()
    }
    save_bot_meetings(bot_meetings)
    
    return jsonify({
        'message': result['message'],
        'bot_id': bot_id,
        'meeting_name': meeting_name
    }), 200


@app.route('/api/bot_status/<bot_id>', methods=['GET'])
@token_required
def bot_status(current_user_id, current_username, bot_id):
    """Get status of a MeetingBaas bot"""
    # Verify this bot belongs to the current user
    bot_meetings = load_bot_meetings()
    bot_info = bot_meetings.get(bot_id)
    
    if not bot_info or bot_info['user_id'] != current_user_id:
        return jsonify({'error': 'Bot not found or access denied'}), 404
    
    # Get bot status from MeetingBaas
    result = get_bot_status(bot_id)
    
    if not result['success']:
        return jsonify({'error': 'Failed to get bot status'}), 500
    
    return jsonify({
        'bot_id': bot_id,
        'status': result['status'],
        'meeting_name': bot_info['meeting_name']
    }), 200


@app.route('/api/meetingbaas/webhook', methods=['POST'])
def meetingbaas_webhook():
    """
    Webhook endpoint for MeetingBaas to send bot status updates
    This endpoint does NOT require authentication (webhooks come from MeetingBaas)
    """
    try:
        data = request.get_json()
        print(f"\n{'='*60}")
        print(f"📨 MeetingBaas Webhook Received!")
        print(f"{'='*60}")
        print(f"Data: {json.dumps(data, indent=2)}")
        
        # Extract bot information
        bot_id = data.get('bot_id') or data.get('id')
        status = data.get('status')
        event_type = data.get('event') or data.get('event_type')
        
        print(f"\n🤖 Bot ID: {bot_id}")
        print(f"📊 Status: {status}")
        print(f"🎯 Event: {event_type}")
        
        # If bot recording is done, fetch and save transcript
        if status in ['done', 'completed', 'finished'] or event_type in ['bot.completed', 'recording.completed']:
            print(f"\n✅ Bot recording completed! Fetching transcript...")
            
            # Find which user this bot belongs to
            bot_meetings = load_bot_meetings()
            bot_info = bot_meetings.get(bot_id)
            
            if bot_info:
                user_id = bot_info['user_id']
                
                # Get transcript from MeetingBaas
                transcript_result = get_transcript(bot_id)
                
                if transcript_result['success']:
                    # Save transcript
                    transcripts = load_transcripts()
                    
                    if user_id not in transcripts:
                        transcripts[user_id] = {}
                    
                    transcripts[user_id][bot_id] = {
                        'transcript': transcript_result['transcript'],
                        'meeting_name': bot_info['meeting_name'],
                        'created_at': datetime.datetime.now().isoformat(),
                        'source': 'meetingbaas_webhook',
                        'speakers': transcript_result.get('speakers', [])
                    }
                    
                    save_transcripts(transcripts)
                    
                    print(f"✅ Transcript saved successfully!")
                    print(f"   User: {user_id}")
                    print(f"   Speakers: {', '.join(transcript_result.get('speakers', []))}")
                else:
                    print(f"❌ Failed to get transcript: {transcript_result.get('message')}")
            else:
                print(f"⚠️ Bot ID not found in bot_meetings.json")
        
        print(f"{'='*60}\n")
        
        # Always return 200 OK to acknowledge webhook receipt
        return jsonify({'success': True, 'message': 'Webhook received'}), 200
        
    except Exception as e:
        print(f"❌ Webhook error: {str(e)}")
        import traceback
        traceback.print_exc()
        # Still return 200 to prevent webhook retries
        return jsonify({'success': False, 'error': str(e)}), 200


@app.route('/api/fetch_transcript/<bot_id>', methods=['POST'])
@token_required
def fetch_transcript_manual(current_user_id, current_username, bot_id):
    """Manually fetch and save transcript from MeetingBaas (for when webhooks fail)"""
    # Verify this bot belongs to the current user
    bot_meetings = load_bot_meetings()
    bot_info = bot_meetings.get(bot_id)
    
    if not bot_info or bot_info['user_id'] != current_user_id:
        return jsonify({'error': 'Bot not found or access denied'}), 404
    
    # Get transcript from MeetingBaas
    result = get_transcript(bot_id)
    
    if not result['success']:
        return jsonify({'error': result.get('message', 'Failed to get transcript')}), 500
    
    # Save transcript to transcripts.json
    transcripts = load_transcripts()
    
    if current_user_id not in transcripts:
        transcripts[current_user_id] = {}
    
    transcripts[current_user_id][bot_id] = {
        'transcript': result['transcript'],
        'meeting_name': bot_info['meeting_name'],
        'created_at': datetime.datetime.now().isoformat(),
        'source': 'meetingbaas_manual',
        'speakers': result.get('speakers', [])
    }
    
    save_transcripts(transcripts)
    
    return jsonify({
        'success': True,
        'bot_id': bot_id,
        'transcript': result['transcript'],
        'speakers': result.get('speakers', []),
        'message': 'Transcript fetched and saved successfully'
    }), 200


# ============= END MEETINGBAAS ENDPOINTS =============


# Serve React static files and index.html for frontend routes
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_react(path):
    if path.startswith('api/'):
        return jsonify({'error': 'API route not found'}), 404
    
    # If dist folder doesn't exist, show backend status
    if not os.path.exists(REACT_BUILD_DIR):
        if path == '':
            return jsonify({
                'message': 'EchoNote backend is running!',
                'status': 'healthy',
                'endpoints': {
                    'signup': '/api/signup',
                    'login': '/api/login',
                    'upload_audio': '/api/upload_audio',
                    'record_meeting': '/api/record_meeting',
                    'chat': '/api/chat'
                }
            }), 200
        else:
            return jsonify({'error': 'Frontend not built. Build React app and deploy dist folder.'}), 404
    
    # Serve React files if dist exists
    file_path = os.path.join(REACT_BUILD_DIR, path)
    if path != "" and os.path.exists(file_path):
        return send_from_directory(REACT_BUILD_DIR, path)
    else:
        return send_from_directory(REACT_BUILD_DIR, 'index.html')


if __name__ == '__main__':
    # Start automatic transcript fetcher (polls every 30 seconds)
    start_auto_fetch()
    
    # Get port from environment (Render sets PORT env var)
    port = int(os.getenv('PORT', 5000))
    
    # Run with debug but disable reloader to prevent restart issues with model loading
    # Bind to 0.0.0.0 for Render (required for external access)
    app.run(host='0.0.0.0', port=port, debug=True, use_reloader=False)
