"""
MeetingBaas API Integration
Handles bot creation, status checking, and transcript retrieval
"""

import requests
import os
from dotenv import load_dotenv
from datetime import datetime
import uuid

load_dotenv()

MEETINGBAAS_API_KEY = os.getenv('MEETINGBAAS_API_KEY')
MEETINGBAAS_API_BASE = 'https://api.meetingbaas.com'


def create_meeting_bot(meeting_url, meeting_name="Echo Note Bot"):
    """
    Create a MeetingBaas bot to join a meeting
    
    Args:
        meeting_url: URL of the Zoom/Google Meet/Teams meeting
        meeting_name: Custom name for the bot
    
    Returns:
        dict: {'success': bool, 'bot_id': str, 'message': str}
    """
    if not MEETINGBAAS_API_KEY:
        return {
            'success': False,
            'message': 'MeetingBaas API key not configured'
        }
    
    headers = {
        'Content-Type': 'application/json',
        'x-meeting-baas-api-key': MEETINGBAAS_API_KEY
    }
    
    # Generate unique deduplication key to allow multiple bots per meeting
    dedup_key = f"echo-note-{uuid.uuid4()}"
    
    payload = {
        'meeting_url': meeting_url,
        'bot_name': meeting_name,
        'deduplication_key': dedup_key,  # Unique key allows multiple bots per meeting
        'recording_mode': 'speaker_view',
        'speech_to_text': 'Default',  # Simple string format - uses MeetingBaas default transcription
        'automatic_leave': {
            'waiting_room_timeout': 600  # 10 minutes
        }
        # Note: webhook_url removed - uses default webhook from MeetingBaas dashboard
    }
    
    try:
        print(f"🔄 Creating MeetingBaas bot for: {meeting_url}")
        response = requests.post(
            f'{MEETINGBAAS_API_BASE}/bots',
            json=payload,
            headers=headers,
            timeout=30
        )
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code in [200, 201]:
            data = response.json()
            print(f"📄 Full Response: {data}")
            
            bot_id = data.get('id') or data.get('bot_id')
            bot_status = data.get('status', 'unknown')
            
            print(f"✅ Bot created successfully!")
            print(f"   Bot ID: {bot_id}")
            print(f"   Status: {bot_status}")
            
            return {
                'success': True,
                'bot_id': bot_id,
                'message': 'Bot created and joining meeting',
                'data': data
            }
        else:
            error_msg = response.text
            print(f"❌ Error: {error_msg}")
            return {
                'success': False,
                'message': f'Failed to create bot: {error_msg}'
            }
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return {
            'success': False,
            'message': f'Error creating bot: {str(e)}'
        }


def get_bot_status(bot_id):
    """
    Get the status of a MeetingBaas bot
    
    Args:
        bot_id: The bot ID returned from create_meeting_bot
    
    Returns:
        dict: {'success': bool, 'status': str, 'data': dict}
    """
    if not MEETINGBAAS_API_KEY:
        return {'success': False, 'message': 'API key not configured'}
    
    headers = {
        'Content-Type': 'application/json',
        'x-meeting-baas-api-key': MEETINGBAAS_API_KEY
    }
    
    try:
        response = requests.get(
            f'{MEETINGBAAS_API_BASE}/bots/meeting_data',
            params={'bot_id': bot_id},
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            bot_data = data.get('bot_data', {}).get('bot', {})
            
            # Determine status from bot data
            if bot_data.get('ended_at'):
                status = 'done'
            elif bot_data.get('bot_joined_at'):
                status = 'in_call'
            else:
                status = 'joining'
            
            print(f"📡 Bot {bot_id} status: {status}")
            if bot_data.get('meeting_url'):
                print(f"   Meeting: {bot_data.get('meeting_url')}")
            
            return {
                'success': True,
                'status': status,
                'data': data
            }
        else:
            return {
                'success': False,
                'message': f'Failed to get bot status: {response.text}'
            }
            
    except Exception as e:
        return {
            'success': False,
            'message': f'Error getting bot status: {str(e)}'
        }


def get_transcript(bot_id):
    """
    Get the transcript from a completed MeetingBaas bot
    
    Args:
        bot_id: The bot ID
    
    Returns:
        dict: {'success': bool, 'transcript': str, 'speakers': list}
    """
    if not MEETINGBAAS_API_KEY:
        return {'success': False, 'message': 'API key not configured'}
    
    headers = {
        'Content-Type': 'application/json',
        'x-meeting-baas-api-key': MEETINGBAAS_API_KEY
    }
    
    try:
        # Get meeting data with transcript
        response = requests.get(
            f'{MEETINGBAAS_API_BASE}/bots/meeting_data',
            params={'bot_id': bot_id},
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            transcripts = data.get('bot_data', {}).get('transcripts', [])
            
            if not transcripts:
                return {
                    'success': False,
                    'message': 'No transcript available yet'
                }
            
            # Build formatted transcript with speaker names and timestamps
            transcript_parts = []
            speakers = set()
            
            for segment in transcripts:
                speaker = segment.get('speaker', 'Unknown Speaker')
                speakers.add(speaker)
                
                # Get all words and combine them
                words = segment.get('words', [])
                text = ''.join([word.get('text', '') for word in words])
                
                # Add speaker label and text
                transcript_parts.append(f"{speaker}: {text.strip()}")
            
            full_transcript = '\n\n'.join(transcript_parts)
            
            print(f"✅ Retrieved transcript for bot {bot_id}")
            print(f"   Speakers: {', '.join(speakers)}")
            print(f"   Length: {len(full_transcript)} characters")
            
            return {
                'success': True,
                'transcript': full_transcript,
                'speakers': list(speakers),
                'raw_data': data
            }
        else:
            return {
                'success': False,
                'message': f'Failed to get transcript: {response.text}'
            }
            
    except Exception as e:
        return {
            'success': False,
            'message': f'Error getting transcript: {str(e)}'
        }


def check_if_transcript_ready(bot_id):
    """
    Check if bot has finished and transcript is ready
    
    Args:
        bot_id: The bot ID
    
    Returns:
        bool: True if transcript is ready, False otherwise
    """
    status_result = get_bot_status(bot_id)
    
    if not status_result['success']:
        return False
    
    # MeetingBaas statuses: 'joining', 'in_meeting', 'done', 'failed'
    status = status_result.get('status', '').lower()
    
    return status in ['done', 'completed', 'finished']
