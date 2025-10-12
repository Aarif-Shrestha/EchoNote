import streamlit as st
import whisper
import ollama
import tempfile
import os
import subprocess
import json
import re  

#  Helper function for stricter greeting matching
def is_strict_greeting(text):
    greetings = ["hi", "hello", "hey", "good morning", "good afternoon", "good evening"]
    return any(re.fullmatch(rf"\b{greet}\b", text.strip().lower()) for greet in greetings)

# Load Whisper model
@st.cache_resource
def load_whisper_model():
    return whisper.load_model("base")

#  Check Phi-3  available
def is_model_available(model_name="phi3:mini"):
    try:
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
        return model_name in result.stdout
    except Exception:
        st.error(" Could not connect to Ollama. Is it running?")
        return False

# Transcribe audio
def transcribe_audio(audio_path):
    st.info(" Transcribing... please wait.")
    model = load_whisper_model()
    result = model.transcribe(audio_path)
    return result["text"]

# Ask a question via Ollama with conversational context 
def ask_phi3(transcript, question, chat_history, model_name="phi3:mini"):
    if not is_model_available(model_name):
        st.error(f" Model '{model_name}' not found in Ollama.\n\nRun:\n⁠  bash\nollama pull {model_name}  ⁠")
        return None

    with st.spinner(" Generating response with Phi-3..."):
        filtered_history = [
            c for c in chat_history
            if c["question"].lower() not in ["thanks", "thank you", "thank u"]
        ]

        # Build conversational context
        history_context = ""
        for chat in filtered_history:
            history_context += f"User: {chat['question']}\nAssistant: {chat['answer']}\n\n"

        prompt = f"""You are a helpful meeting assistant. Below is a transcript of a meeting:

{transcript}

Here is the conversation history for context:

{history_context}

Answer the following question **concisely**, in **no more than 5 lines**:
{question}
"""
        try:
            response = ollama.chat(
                model=model_name,
                messages=[{"role": "user", "content": prompt}]
            )
            return response["message"]["content"]
        except Exception as e:
            st.error(f" Error from Ollama: {e}")
            return None

# Save chat history
def load_chat_history():
    try:
        if os.path.exists("chat_history.json"):
            with open("chat_history.json", "r") as f:
                return json.load(f)
        return []
    except Exception as e:
        st.warning(f"⚠️ Could not load chat history: {e}")
        return []

def save_chat_history(history):
    try:
        with open("chat_history.json", "w") as f:
            json.dump(history, f)
    except Exception as e:
        st.error(f" Could not save chat history: {e}")

# Streamlit setup
st.set_page_config(page_title=" Offline Meeting Assistant", layout="centered")
st.markdown("<h1 style='text-align: center;'> Offline Meeting Assistant</h1>", unsafe_allow_html=True)
st.caption("Built with Whisper + Phi-3 (Ollama) — 100% Private & Free")

# Sidebar:type (txt,audio)
st.sidebar.header(" Upload Your Data")
input_type = st.sidebar.radio("Choose input type:", ["Transcript (.txt)", "Audio (.mp3, .wav, etc)"])

# Chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = load_chat_history()
if "selected_history" not in st.session_state:
    st.session_state.selected_history = None

# History show while clicking 
st.sidebar.header(" Chat History")
if st.session_state.chat_history:
    for i, chat in enumerate(st.session_state.chat_history):
        short_answer = chat['answer'][:60] + ("..." if len(chat['answer']) > 60 else "")
        if st.sidebar.button(short_answer, key=f"history_{i}"):
            st.session_state.selected_history = chat['answer']  
else:
    st.sidebar.info("No previous chat history.")

# Show only selected history in main chat 
if st.session_state.selected_history:
    st.markdown("---")
    st.subheader(" History")
    st.markdown(st.session_state.selected_history)
    st.markdown("---")

# Upload transcript
if input_type == "Transcript (.txt)":
    txt_file = st.sidebar.file_uploader("Upload transcript file", type=["txt"])
    if txt_file:
        transcript = txt_file.read().decode("utf-8")
        st.session_state["transcript"] = transcript
        st.success(" Transcript uploaded successfully.")
        st.text_area(" Transcript Preview", value=transcript, height=300)

# Upload and transcribe audio
if input_type == "Audio (.mp3, .wav, etc)":
    audio_file = st.sidebar.file_uploader("Upload audio file", type=["mp3", "wav", "m4a", "webm"])
    if audio_file:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(audio_file.name)[1]) as tmp:
            tmp.write(audio_file.read())
            audio_path = tmp.name

        if st.sidebar.button(" Transcribe Audio"):
            transcript = transcribe_audio(audio_path)
            st.session_state["transcript"] = transcript
            st.success(" Transcription complete!")
            st.text_area(" Transcript", value=transcript, height=300)
            try:
                os.unlink(audio_path)
            except Exception as e:
                st.warning(f"⚠️ Could not delete temporary file: {e}")

# Main chat area
if "transcript" in st.session_state:
    st.markdown("---")
    st.markdown("###  Ask Questions About the Meeting")

    # Clear history button
    if st.button("🗑️ Clear Chat History", key="clear_history"):
        if st.session_state.chat_history:
            st.session_state.chat_history = []
            save_chat_history([])
            st.session_state.selected_history = None
            st.success("Chat history cleared!")
            st.rerun()
        else:
            st.info("ℹ Chat history is already empty.")

    # Display full chat history
    if st.session_state.chat_history:
        for chat in st.session_state.chat_history:
            with st.container():
                st.markdown(f" You: {chat['question']}")
                st.markdown(f" Assistant: {chat['answer']}")
                st.markdown("---")

    # Chat input form
    with st.form(key="chat_form", clear_on_submit=True):
        col1, col2 = st.columns([6, 1])
        with col1:
            question = st.text_input("Type your question:", placeholder="e.g. What was the main goal?")
        with col2:
            send = st.form_submit_button("Send", use_container_width=True)

        if send and question.strip():
            user_input = question.strip().lower()

            # ✅ Improved greeting check
            if is_strict_greeting(user_input):
                answer = " Hello! How can I help you today?"
            else:
                answer = ask_phi3(st.session_state["transcript"], question, st.session_state.chat_history)

            if answer:
                # Save full answer in history
                st.session_state.chat_history.append({
                    "question": question,
                    "answer": answer
                })
                save_chat_history(st.session_state.chat_history)
                st.rerun()
