"""
Ollama Chatbot Integration for Echo Note
Handles meeting transcript Q&A using Ollama's Gemma 2B model
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
    
    # Build conversational context from history
    history_context = ""
    if chat_history:
        for chat in chat_history:
            history_context += f"User: {chat['question']}\nAssistant: {chat['answer']}\n\n"
    
    # Check if user is asking to see the full transcript
    show_transcript_keywords = ["show transcript", "display transcript", "show me the transcript", 
                                "display the transcript", "view transcript", "see transcript",
                                "full transcript", "entire transcript", "whole transcript"]
    is_show_transcript = any(keyword in question.lower() for keyword in show_transcript_keywords)
    
    if is_show_transcript:
        return {'answer': f"Here is the full meeting transcript:\n\n{transcript}"}
    
    # Check if user is asking for a summary
    is_summary = any(word in question.lower() for word in ["summary", "summarize", "summarise", "overview"])
    
    # Build prompt based on question type
    if is_summary:
        prompt = f"""You are analyzing a meeting transcript. Here is the transcript:

--- BEGIN TRANSCRIPT ---
{transcript}
--- END TRANSCRIPT ---

Your task: Write a comprehensive summary of this meeting transcript in 2-3 well-structured paragraphs. Include the main topics discussed, key decisions made, and important action items.

CRITICAL FORMATTING RULES:
- Write ONLY in paragraph format
- DO NOT use bullet points (*, -, •)
- DO NOT use numbered lists (1., 2., 3.)
- DO NOT use asterisks or dashes for lists
- Write complete sentences in flowing paragraphs
- Keep it between 150-200 words

Example format:
"The meeting focused on several important topics. First, the team discussed... Sarah proposed... John raised concerns... The group agreed to... Next, the product launch... Finally, regarding hiring..."

Remember: PARAGRAPH FORMAT ONLY. NO BULLET POINTS OR LISTS OF ANY KIND."""
        system_msg = "You are a professional meeting summarizer. You MUST write in paragraph format only. Never use bullet points, asterisks, dashes, or any list formatting. Write flowing narrative text."
    else:
        prompt = f"""You are analyzing a meeting transcript. Here is the transcript:

--- BEGIN TRANSCRIPT ---
{transcript}
--- END TRANSCRIPT ---

User's question: {question}

Your task: Answer the user's question based ONLY on the information in the transcript above. If the transcript doesn't contain the answer, say "This information is not mentioned in the transcript." Keep your answer to 1-2 sentences maximum."""
        system_msg = "You are a meeting assistant. Answer questions based strictly on the provided transcript. Be concise and direct."
    
    try:
        # Call Ollama via subprocess
        command = [
            "ollama", "run", model_name,
            f"{system_msg}\n\n{prompt}"
        ]
        
        print(f"🤖 Calling Ollama model: {model_name}")
        result = subprocess.run(command, capture_output=True, text=True, timeout=60)
        
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
