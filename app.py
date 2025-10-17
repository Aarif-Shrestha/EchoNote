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
from asr_model import ASRTranscriber
from chatbot import is_strict_greeting, ask_ollama, get_greeting_response

# Path to React build folder
REACT_BUILD_DIR = os.path.join(os.path.dirname(__file__), 'dist')

# Data storage paths
USERS_FILE = os.path.join(os.path.dirname(__file__), 'data', 'users.json')
AUDIOS_FILE = os.path.join(os.path.dirname(__file__), 'data', 'audios.json')
TRANSCRIPTS_FILE = os.path.join(os.path.dirname(__file__), 'data', 'transcripts.json')
UPLOADS_DIR = os.path.join(os.path.dirname(__file__), 'uploads')
MODEL_PATH = os.path.join(os.path.dirname(__file__), 'models', 'baseline_asr_model.pth')

# Allowed audio file extensions
ALLOWED_EXTENSIONS = {'mp3', 'wav', 'ogg', 'm4a', 'flac', 'aac', 'webm'}

# JWT Secret Key (change this to a random secret key in production)
SECRET_KEY = 'your-secret-key-change-this-in-production'

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
            print("🔄 Loading ASR model...")
            transcriber = ASRTranscriber(MODEL_PATH)
        except Exception as e:
            print(f"❌ Failed to load ASR model: {str(e)}")
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
    """Save users to JSON file"""
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)


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
    """Save audio metadata to JSON file"""
    with open(AUDIOS_FILE, 'w') as f:
        json.dump(audios, f, indent=2)


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
    """Save transcripts to JSON file"""
    with open(TRANSCRIPTS_FILE, 'w') as f:
        json.dump(transcripts, f, indent=2)


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
        if asr and asr.model:
            print(f"🎤 Transcribing audio for user {current_username}...")
            transcript = asr.transcribe(file_path)
            print(f"✅ Transcription complete!")
        else:
            transcript = "Transcription service unavailable. Model not loaded."
            print("⚠️ ASR model not available")
    except Exception as e:
        transcript = f"Error during transcription: {str(e)}"
        print(f"❌ Transcription error: {str(e)}")
    
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


# Serve React static files and index.html for frontend routes
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_react(path):
    if path.startswith('api/'):
        return jsonify({'error': 'API route not found'}), 404
    file_path = os.path.join(REACT_BUILD_DIR, path)
    if path != "" and os.path.exists(file_path):
        return send_from_directory(REACT_BUILD_DIR, path)
    else:
        return send_from_directory(REACT_BUILD_DIR, 'index.html')


if __name__ == '__main__':
    app.run(debug=True)
