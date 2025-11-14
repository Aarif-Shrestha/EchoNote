"""
Automatic transcript fetcher for MeetingBaas - polls every 30 seconds
Fetches transcripts directly via API - NO downloads needed!
"""

import time
import threading
import os
import uuid
import datetime
from meetingbaas_integration import check_if_transcript_ready, get_transcript
from dotenv import load_dotenv
import json

load_dotenv()

# File paths
BOT_MEETINGS_FILE = os.path.join(os.path.dirname(__file__), 'data', 'bot_meetings.json')
AUDIOS_FILE = os.path.join(os.path.dirname(__file__), 'data', 'audios.json')
TRANSCRIPTS_FILE = os.path.join(os.path.dirname(__file__), 'data', 'transcripts.json')

def load_json(filepath):
    """Load JSON file safely"""
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r') as f:
                content = f.read().strip()
                if content:
                    return json.loads(content)
        except (json.JSONDecodeError, ValueError):
            pass
    return {}


def save_json(filepath, data):
    """Save JSON file safely"""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)


def check_transcripts():
    """
    Poll MeetingBaas for completed bots and fetch transcripts
    NO audio downloads - gets transcript directly via API!
    """
    bot_meetings = load_json(BOT_MEETINGS_FILE)
    transcripts = load_json(TRANSCRIPTS_FILE)
    audios = load_json(AUDIOS_FILE)
    
    updated = False
    
    for bot_id, bot_info in list(bot_meetings.items()):
        # Check if transcript exists and is not empty
        meeting_id = bot_info.get('meeting_id')
        user_id = bot_info.get('user_id')
        transcript_exists = False
        
        if meeting_id and user_id:
            existing_transcript = transcripts.get(user_id, {}).get(meeting_id, {}).get('transcript', '')
            transcript_exists = existing_transcript and len(existing_transcript.strip()) > 50
        
        # Skip if already fetched AND transcript exists with content
        if bot_info.get('transcript_fetched') and transcript_exists:
            continue
        
        # Check if bot is done and transcript is ready
        if not check_if_transcript_ready(bot_id):
            continue
        
        print(f"✅ Meeting ended for bot {bot_id}. Fetching transcript...")
        
        # Get transcript directly from MeetingBaas API (no downloads!)
        transcript_result = get_transcript(bot_id)
        
        if transcript_result['success']:
            user_id = bot_info['user_id']
            username = bot_info['username']
            meeting_name = bot_info['meeting_name']
            meeting_id = str(uuid.uuid4())
            
            transcript_text = transcript_result['transcript']
            speakers = transcript_result.get('speakers', [])
            
            # Save transcript
            if user_id not in transcripts:
                transcripts[user_id] = {}
            
            transcripts[user_id][meeting_id] = {
                'username': username,
                'transcript': transcript_text,
                'meeting_name': meeting_name,
                'source': 'meetingbaas_auto',
                'bot_id': bot_id,
                'speakers': speakers,
                'fetched_at': datetime.datetime.utcnow().isoformat()
            }
            
            # Save audio metadata
            if user_id not in audios:
                audios[user_id] = {}
            
            audios[user_id][meeting_id] = {
                'username': username,
                'meeting_name': meeting_name,
                'filename': f'meetingbaas_{bot_id}.txt',
                'upload_date': datetime.datetime.utcnow().isoformat(),
                'source': 'meetingbaas_auto',
                'bot_id': bot_id
            }
            
            # Mark as fetched
            bot_info['transcript_fetched'] = True
            bot_info['meeting_id'] = meeting_id
            bot_meetings[bot_id] = bot_info
            
            updated = True
            print(f"💾 Saved transcript for {username}: {meeting_name}")
            print(f"📝 Transcript length: {len(transcript_text)} characters")
            if speakers:
                print(f"👥 Speakers detected: {', '.join(speakers)}")
        else:
            print(f"⚠️ Could not fetch transcript for bot {bot_id}: {transcript_result.get('message')}")
    
    if updated:
        save_json(TRANSCRIPTS_FILE, transcripts)
        save_json(AUDIOS_FILE, audios)
        save_json(BOT_MEETINGS_FILE, bot_meetings)

def auto_fetch_loop():
    """Background thread that polls every 30 seconds"""
    print("🤖 MeetingBaas auto-fetch started! Checking every 30 seconds...")
    
    while True:
        try:
            check_transcripts()
        except Exception as e:
            print(f"❌ Auto-fetch error: {e}")
        
        time.sleep(30)


def start_auto_fetch():
    """Start the auto-fetch background thread"""
    thread = threading.Thread(target=auto_fetch_loop, daemon=True)
    thread.start()
    print("✅ Automatic transcript fetcher running (MeetingBaas)!")
