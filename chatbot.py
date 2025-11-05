"""
Ollama Chatbot Integration for Echo Note
Handles meeting transcript Q&A using Ollama's Gemma 2B model

PERFORMANCE OPTIMIZATIONS:
- Smart context extraction (6000 chars max, sampling for summaries)
- Ultra-short prompts for faster processing
- Quick answers for simple queries (skip AI)
- 120s timeout for long transcripts
- Efficient Q&A format
"""

import subprocess
import re


def is_strict_greeting(text):
    """
    Check if text is a simple greeting
    
    Args:
        text (str): User input text
        
    Returns:
        bool: True if text matches a greeting pattern
    """
    greetings = ["hi", "hello", "hey", "good morning", "good afternoon", "good evening"]
    return any(re.fullmatch(rf"\b{greet}\b", text.strip().lower()) for greet in greetings)


def is_model_available(model_name="gemma:2b"):
    """
    Check if Ollama model exists and is available
    
    Args:
        model_name (str): Name of the Ollama model to check
        
    Returns:
        bool: True if model is available
    """
    try:
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=5)
        return model_name in result.stdout
    except subprocess.TimeoutExpired:
        print("⚠️ Ollama list command timed out")
        return False
    except Exception as e:
        print(f"❌ Could not connect to Ollama: {e}")
        return False


def ask_ollama(transcript, question, chat_history=None, model_name="gemma:2b"):
    """
    Ask Ollama a question with meeting transcript context
    
    Args:
        transcript (str): Meeting transcript text
        question (str): User's question
        chat_history (list): Previous conversation history [{'question': str, 'answer': str}]
        model_name (str): Ollama model to use
        
    Returns:
        dict: {'answer': str} on success, {'error': str} on failure
    """
    if chat_history is None:
        chat_history = []
    
    # Check if model is available
    if not is_model_available(model_name):
        return {
            'error': f"Model '{model_name}' not found in Ollama. Please run: ollama pull {model_name}"
        }
    
    # Save original transcript for "show transcript" command
    original_transcript = transcript
    question_lower = question.lower()
    
    print(f"🔍 Question received: '{question}'")
    print(f"📄 Original transcript length: {len(original_transcript)} chars")
    
    # Quick answers for simple queries (skip AI processing) - BEFORE truncation
    # Check if user is asking to see the full transcript
    show_transcript_keywords = ["show transcript", "display transcript", "show me the transcript", 
                                "display the transcript", "view transcript", "see transcript",
                                "full transcript", "entire transcript", "whole transcript",
                                "read transcript", "give me transcript", "get transcript",
                                "transcript please", "show full"]
    if any(keyword in question_lower for keyword in show_transcript_keywords):
        print(f"✅ Quick answer: Returning full transcript ({len(original_transcript)} chars)")
        return {'answer': f"Here is the full meeting transcript:\n\n{original_transcript}"}
    
    # Quick answer for "who attended" or "who was there"
    if any(phrase in question_lower for phrase in ["who attended", "who was there", "who spoke", "list of speakers"]):
        # Extract speaker numbers from transcript
        import re
        speakers = re.findall(r'Speaker (\d+):', original_transcript)
        if speakers:
            unique_speakers = sorted(set(speakers))
            return {'answer': f"There were {len(unique_speakers)} speakers in this meeting: Speaker {', Speaker '.join(unique_speakers)}."}
    
    # Now do smart context extraction for AI processing
    MAX_TRANSCRIPT_LENGTH = 6000  # Reduced for faster processing
    original_length = len(transcript)
    
    # For summaries, use more context; for specific questions, less is fine
    is_summary = any(word in question_lower for word in ["summary", "summarize", "summarise", "overview"])
    
    if is_summary:
        # For summaries, take beginning, middle, and end
        if len(transcript) > MAX_TRANSCRIPT_LENGTH:
            third = MAX_TRANSCRIPT_LENGTH // 3
            beginning = transcript[:third]
            middle_start = len(transcript) // 2 - third // 2
            middle = transcript[middle_start:middle_start + third]
            end = transcript[-third:]
            transcript = beginning + "\n[...]\n" + middle + "\n[...]\n" + end
            print(f"📝 Using smart sampling: {original_length} → {len(transcript)} chars")
    else:
        # For specific questions, just use first part (most relevant info usually at start)
        if len(transcript) > MAX_TRANSCRIPT_LENGTH:
            transcript = transcript[:MAX_TRANSCRIPT_LENGTH]
            print(f"📝 Truncated to {MAX_TRANSCRIPT_LENGTH} chars for faster processing")
    
    # Build conversational context from history
    history_context = ""
    if chat_history:
        for chat in chat_history:
            history_context += f"User: {chat['question']}\nAssistant: {chat['answer']}\n\n"
    
    # Build ultra-efficient prompts
    if is_summary:
        # Minimal prompt for summary
        prompt = f"""Transcript: {transcript}

Task: Write a 150-word paragraph summary covering: main topics, decisions, action items."""
        system_msg = "Be concise. Paragraph format only."
    else:
        # Ultra-short prompt for Q&A
        prompt = f"""Transcript: {transcript}

Q: {question}
A:"""
        system_msg = "Answer in 1-2 sentences based on transcript only."
    
    try:
        # Call Ollama via subprocess
        command = [
            "ollama", "run", model_name,
            f"{system_msg}\n\n{prompt}"
        ]
        
        print(f"🤖 Calling Ollama model: {model_name}")
        # Increase timeout for long transcripts (120 seconds)
        result = subprocess.run(command, capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            answer = result.stdout.strip()
            print(f"✅ Ollama response received ({len(answer)} chars)")
            return {'answer': answer}
        else:
            error_msg = result.stderr.strip() if result.stderr else "Unknown error"
            print(f"❌ Ollama error: {error_msg}")
            return {'error': f"Ollama error: {error_msg}"}
            
    except subprocess.TimeoutExpired:
        print("⏱️ Ollama request timed out")
        return {'error': 'Request timed out. The model might be processing a complex query. Please try again.'}
    except FileNotFoundError:
        print("❌ Ollama not found in system PATH")
        return {'error': 'Ollama is not installed or not in system PATH. Please install Ollama from https://ollama.com'}
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return {'error': f'Error from Ollama: {str(e)}'}


def get_greeting_response():
    """
    Get a standard greeting response
    
    Returns:
        str: Greeting message
    """
    return "Hello! How can I help you today?"


# Available models (you can expand this list)
SUPPORTED_MODELS = {
    'gemma:2b': 'Gemma 2B - Fast and efficient',
    'llama2': 'Llama 2 - More capable but slower',
    'mistral': 'Mistral - Balanced performance',
}


def list_available_models():
    """
    List all available Ollama models on the system
    
    Returns:
        list: Available model names
    """
    try:
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            # Parse the output to extract model names
            lines = result.stdout.strip().split('\n')
            if len(lines) > 1:  # Skip header
                models = [line.split()[0] for line in lines[1:] if line.strip()]
                return models
        return []
    except Exception as e:
        print(f"❌ Could not list models: {e}")
        return []
