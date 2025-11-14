"""
Echo Note: Whisper + Speaker Diarization Model
"""
import torch
import librosa
import numpy as np
import whisper
import os

# Try to import speaker diarization - make it optional
try:
    from speechbrain.pretrained import EncoderClassifier
    from sklearn.cluster import AgglomerativeClustering
    DIARIZATION_AVAILABLE = True
except Exception as e:
    print(f"⚠️ Speaker diarization not available: {e}")
    DIARIZATION_AVAILABLE = False

# ------------------- CONFIG -------------------
SAMPLE_RATE = 16000

# ------------------- TRANSCRIPTION CLASS -------------------
class ASRTranscriber:
    def __init__(self, model_path=None, device=None):
        """
        Initialize Whisper + Speaker Diarization
        Note: model_path is kept for compatibility but Whisper loads its own models
        """
        self.device = device if device else torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.asr_model = None
        self.classifier = None
        
        self.load_model()
    
    def load_model(self):
        """Load Whisper and Speaker Diarization models"""
        try:
            print("Loading Whisper model...")
            self.asr_model = whisper.load_model("base")
            print("✅ Whisper model loaded.\n")
            
            # Load speaker classifier only if diarization is available
            if DIARIZATION_AVAILABLE:
                try:
                    print("Loading speaker diarization model...")
                    self.classifier = EncoderClassifier.from_hparams(source="speechbrain/spkrec-ecapa-voxceleb")
                    print("✅ Speaker diarization model loaded.\n")
                except Exception as e:
                    print(f"⚠️ Speaker diarization unavailable: {e}")
                    self.classifier = None
            else:
                self.classifier = None
                print("⚠️ Running without speaker diarization.\n")
            
            return True
            
        except Exception as e:
            print(f"❌ Error loading models: {str(e)}")
            self.asr_model = None
            self.classifier = None
            return False
    
    def transcribe(self, audio_path):
        """Transcribe audio file with speaker diarization"""
        try:
            if self.asr_model is None:
                return "Error: Whisper model not loaded. Please check installation."
            
            # --- Load Audio ---
            y, sr = librosa.load(audio_path, sr=SAMPLE_RATE, mono=True)
            print(f"✅ Loaded {audio_path} ({len(y)/sr:.2f}s)\n")
            
            # --- Transcribe ---
            print("🔹 Transcribing with Whisper...")
            result = self.asr_model.transcribe(audio_path, verbose=False)
            segments = result["segments"]
            text = result["text"]
            print("\n📝 Transcript:")
            print(text)
            
            # If no segments or no classifier, return plain text
            if not segments or self.classifier is None:
                if self.classifier is None:
                    print("⚠️ Speaker diarization unavailable, returning plain transcript.\n")
                return text if text else "Unable to transcribe audio."
            
            # --- Speaker Embeddings ---
            embeddings, valid_segments = [], []
            print("\n🔹 Extracting speaker embeddings...")
            for s in segments:
                start, end = int(s["start"]*sr), int(s["end"]*sr)
                chunk = y[start:end]
                if len(chunk)/sr < 1.0: 
                    continue
                wav_tensor = torch.tensor(chunk, dtype=torch.float32).unsqueeze(0)
                with torch.no_grad():
                    emb = self.classifier.encode_batch(wav_tensor).squeeze().cpu().numpy()
                    emb /= np.linalg.norm(emb) + 1e-8
                embeddings.append(emb)
                valid_segments.append(s)
            
            if not embeddings:
                print("❌ No valid segments for diarization.")
                return text
            
            embeddings = np.stack(embeddings)
            print(f"✅ Extracted {len(embeddings)} embeddings.\n")
            
            # --- Cluster Speakers ---
            print("🔹 Clustering speakers...")
            n_speakers = min(4, len(embeddings))
            clustering = AgglomerativeClustering(n_clusters=n_speakers, metric='cosine', linkage='average')
            labels = clustering.fit_predict(embeddings)
            print(f"✅ Diarization complete! Detected {len(set(labels))} speakers.\n")
            
            # --- Format Final Diarized Transcript (merge same speakers) ---
            output_lines = []
            
            current_speaker = None
            current_text = ""
            
            for i, seg in enumerate(valid_segments):
                speaker_id = labels[i] + 1
                text = seg['text'].strip()
                
                if current_speaker == speaker_id:
                    # Same speaker continues, append text
                    current_text += " " + text
                else:
                    # New speaker, write previous speaker's paragraph
                    if current_speaker is not None:
                        output_lines.append(f"Speaker {current_speaker}: {current_text.strip()}\n")
                    
                    # Start new speaker paragraph
                    current_speaker = speaker_id
                    current_text = text
            
            # Write the last speaker's paragraph
            if current_speaker is not None:
                output_lines.append(f"Speaker {current_speaker}: {current_text.strip()}\n")
            
            # Add summary footer
            output_lines.append(f"\n[Total Speakers: {len(set(labels))}]")
            
            return "\n".join(output_lines)
            
        except Exception as e:
            print(f"❌ Transcription error: {str(e)}")
            return f"Error during transcription: {str(e)}"
