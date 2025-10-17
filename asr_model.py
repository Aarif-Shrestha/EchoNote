"""
ASR Model for Audio Transcription
Based on Baseline ASR with LSTM and CTC
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
import librosa
import numpy as np
import os

# ------------------- CONFIG -------------------
SAMPLE_RATE = 16000
N_MFCC = 13

# ------------------- MFCC EXTRACTION -------------------
def extract_mfcc(audio_path, n_mfcc=N_MFCC, sr=SAMPLE_RATE):
    """Extract MFCC features from audio file"""
    audio, sr = librosa.load(audio_path, sr=sr)
    mfccs = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=n_mfcc)
    return mfccs.astype(np.float32)

# ------------------- TOKENIZER -------------------
class CharTokenizer:
    def __init__(self):
        self.char_map = {c: i + 1 for i, c in enumerate(" abcdefghijklmnopqrstuvwxyz'.")}
        self.idx_map = {i + 1: c for i, c in enumerate(" abcdefghijklmnopqrstuvwxyz'.")}
        self.blank_id = 0

    def decode(self, indices):
        """Decode indices to text using CTC decoding"""
        output = []
        for i, idx in enumerate(indices):
            if idx != self.blank_id and (i == 0 or idx != indices[i - 1]):
                output.append(self.idx_map.get(idx, ''))
        return "".join(output)

# ------------------- MODEL DEFINITION -------------------
class BaselineASR(nn.Module):
    def __init__(self, input_dim, hidden_dim, output_dim, n_layers=3, dropout=0.1):
        super(BaselineASR, self).__init__()
        self.lstm = nn.LSTM(
            input_size=input_dim,
            hidden_size=hidden_dim,
            num_layers=n_layers,
            dropout=dropout,
            bidirectional=True,
            batch_first=True
        )
        self.fc = nn.Linear(hidden_dim * 2, output_dim)

    def forward(self, x):
        output, _ = self.lstm(x)
        return self.fc(output)

# ------------------- TRANSCRIPTION CLASS -------------------
class ASRTranscriber:
    def __init__(self, model_path, device=None):
        self.model_path = model_path
        self.device = device if device else torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = CharTokenizer()
        self.model = None
        self.INPUT_DIM = N_MFCC
        self.HIDDEN_DIM = 256
        self.OUTPUT_DIM = len(self.tokenizer.char_map) + 1
        
        self.load_model()
    
    def load_model(self):
        """Load the pre-trained ASR model"""
        try:
            if not os.path.exists(self.model_path):
                print(f"⚠️ Model not found at {self.model_path}")
                return False
            
            # Initialize model
            self.model = BaselineASR(
                self.INPUT_DIM, 
                self.HIDDEN_DIM, 
                self.OUTPUT_DIM
            ).to(self.device)
            
            # Load state dict
            state_dict = torch.load(self.model_path, map_location=self.device, weights_only=True)
            self.model.load_state_dict(state_dict)
            self.model.eval()
            
            print(f"✅ ASR Model loaded successfully from {self.model_path}")
            return True
            
        except Exception as e:
            print(f"❌ Error loading model: {str(e)}")
            self.model = None
            return False
    
    def transcribe(self, audio_path):
        """Transcribe audio file to text"""
        try:
            if self.model is None:
                return "Error: Model not loaded. Please check model file."
            
            # Extract MFCC features
            mfcc_features = extract_mfcc(audio_path)
            
            # Convert to tensor
            features = torch.from_numpy(mfcc_features).unsqueeze(0).to(self.device)
            
            # Transpose if needed (ensure time dimension is correct)
            if features.dim() == 3 and features.shape[1] < features.shape[2]:
                features = features.transpose(1, 2)
            
            # Run inference
            with torch.no_grad():
                logits = self.model(features)
            
            # Decode predictions
            predictions = F.log_softmax(logits, dim=-1).argmax(dim=-1).squeeze(0).tolist()
            transcript = self.tokenizer.decode(predictions)
            
            # Clean up transcript
            transcript = transcript.strip()
            if transcript:
                # Capitalize first letter
                transcript = transcript[0].upper() + transcript[1:] if len(transcript) > 1 else transcript.upper()
                # Add period if missing
                if not transcript.endswith(('.', '!', '?')):
                    transcript += '.'
            
            return transcript if transcript else "Unable to transcribe audio."
            
        except Exception as e:
            print(f"❌ Transcription error: {str(e)}")
            return f"Error during transcription: {str(e)}"
