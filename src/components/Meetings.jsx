import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import "../style/Meetings.css"
import Navbar from './Navbar'

const Meetings = () => {
  const navigate = useNavigate();
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [meetingName, setMeetingName] = useState('');
  const [transcript, setTranscript] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState('');
  
  // New states for meeting URL recording
  const [meetingUrl, setMeetingUrl] = useState('');
  const [meetingBotName, setMeetingBotName] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [recordStatus, setRecordStatus] = useState('');

  useEffect(() => {
    const token = localStorage.getItem('token');
    setIsLoggedIn(!!token);
  }, []);

  const handleProtectedAction = (e) => {
    if (!isLoggedIn) {
      e.preventDefault();
      navigate('/login');
      return false;
    }
    return true;
  };

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedFile(file);
      setMeetingName(file.name.replace(/\.[^/.]+$/, "")); // Remove extension
      setUploadStatus(`Selected: ${file.name}`);
    }
  };

  const handleUpload = async () => {
    if (!handleProtectedAction()) return;
    
    if (!selectedFile) {
      setUploadStatus('Please select a file first');
      return;
    }

    setIsUploading(true);
    setUploadStatus('Uploading and transcribing...');
    setTranscript('');

    try {
      const token = localStorage.getItem('token');
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('meeting_name', meetingName);

      const response = await fetch('/api/upload_audio', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });

      if (response.status === 401) {
        // Token expired or invalid
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        setIsLoggedIn(false);
        navigate('/login');
        return;
      }

      if (!response.ok) {
        const data = await response.json().catch(() => ({ error: 'Server error' }));
        setUploadStatus(`Error: ${data.error}`);
        return;
      }

      const data = await response.json();
      setTranscript(data.transcript);
      setUploadStatus('✅ Transcription complete!');
      setSelectedFile(null);
    } catch (error) {
      setUploadStatus(`Error: ${error.message}`);
    } finally {
      setIsUploading(false);
    }
  };

  const handleRecordMeeting = async () => {
    if (!handleProtectedAction()) return;
    
    if (!meetingUrl.trim()) {
      setRecordStatus('Please enter a meeting URL');
      return;
    }

    setIsRecording(true);
    setRecordStatus('🤖 Starting Echo Note Bot...');

    try {
      const token = localStorage.getItem('token');

      const response = await fetch('/api/record_meeting', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          meeting_url: meetingUrl,
          meeting_name: meetingBotName || 'Recorded Meeting'
        })
      });

      if (response.status === 401) {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        setIsLoggedIn(false);
        navigate('/login');
        return;
      }

      const data = await response.json();

      if (response.ok) {
        setRecordStatus(`✅ ${data.message}. Transcript will appear in your meetings after completion.`);
        setMeetingUrl('');
        setMeetingBotName('');
      } else {
        setRecordStatus(`❌ Error: ${data.error}`);
      }
    } catch (error) {
      setRecordStatus(`❌ Error: ${error.message}`);
    } finally {
      setIsRecording(false);
    }
  };

  return (
    <>
      <Navbar />

      {/* Meetings Section */}
      <section className="meetings-container">
        <h1 className="meetings-title">Meetings</h1>
        <p className="meetings-subtitle">
          Upload audio, or paste meeting URL to record automatically
        </p>

        <div className="meetings-content">
          {/* Record Live Meeting */}
          <div className="upload-box">
            <h3>🎥 Record Live Meeting</h3>
            
            <div className="upload-area">
              <p>Paste your Zoom, Google Meet, or Teams meeting URL</p>
              
              <input 
                type="text" 
                placeholder="Meeting URL (e.g., https://zoom.us/j/...)" 
                value={meetingUrl}
                onChange={(e) => setMeetingUrl(e.target.value)}
                style={{
                  padding: '10px', 
                  marginTop: '10px', 
                  width: '90%', 
                  borderRadius: '4px', 
                  border: '1px solid #ccc',
                  fontSize: '14px'
                }}
              />
              
              <input 
                type="text" 
                placeholder="Meeting name (optional)" 
                value={meetingBotName}
                onChange={(e) => setMeetingBotName(e.target.value)}
                style={{
                  padding: '10px', 
                  marginTop: '10px', 
                  width: '90%', 
                  borderRadius: '4px', 
                  border: '1px solid #ccc',
                  fontSize: '14px'
                }}
              />
              
              <button 
                className="upload-btn" 
                onClick={handleRecordMeeting}
                disabled={isRecording}
                style={{
                  marginTop: '15px',
                  padding: '12px 30px',
                  backgroundColor: isRecording ? '#ccc' : '#2196F3',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: isRecording ? 'not-allowed' : 'pointer',
                  fontSize: '16px',
                  fontWeight: '500'
                }}
              >
                {isRecording ? '⏳ Starting Bot...' : '🤖 Start Recording Bot'}
              </button>
              
              {recordStatus && (
                <p style={{
                  marginTop: '15px', 
                  color: recordStatus.includes('Error') || recordStatus.includes('❌') ? 'red' : 'green',
                  fontSize: '14px',
                  lineHeight: '1.6'
                }}>
                  {recordStatus}
                </p>
              )}
              
              <p className="file-support" style={{marginTop: '15px'}}>
                Echo Note Bot will join, record, and transcribe automatically
              </p>
            </div>
          </div>

          {/* Upload Meeting Audio */}
          <div className="upload-box">
            <h3>📂 Upload Meeting Audio</h3>
            
            <div className="upload-area">
              <div className='upload-logo'>
                <img src="upload.png" alt="upload" />
              </div>
              <input 
                type="file" 
                id="fileInput" 
                style={{display: 'none'}} 
                accept=".mp3,.wav,.m4a,.ogg,.flac,.aac,.webm" 
                onChange={handleFileSelect}
              />
              <p>Drag and drop your audio file here, or click to browse</p>
              
              {selectedFile && (
                <input 
                  type="text" 
                  placeholder="Meeting name (optional)" 
                  value={meetingName}
                  onChange={(e) => setMeetingName(e.target.value)}
                  style={{
                    padding: '8px', 
                    marginTop: '10px', 
                    width: '80%', 
                    borderRadius: '4px', 
                    border: '1px solid #ccc'
                  }}
                />
              )}
              
              <button 
                className="choose-btn" 
                onClick={(e) => {
                  if (handleProtectedAction(e)) {
                    document.getElementById("fileInput").click();
                  }
                }}
                disabled={isUploading}
              >
                Choose File
              </button>
              
              {selectedFile && (
                <button 
                  className="upload-btn" 
                  onClick={handleUpload}
                  disabled={isUploading}
                  style={{
                    marginTop: '10px',
                    padding: '10px 20px',
                    backgroundColor: isUploading ? '#ccc' : '#4CAF50',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: isUploading ? 'not-allowed' : 'pointer'
                  }}
                >
                  {isUploading ? '⏳ Processing...' : '🚀 Upload & Transcribe'}
                </button>
              )}
              
              {uploadStatus && (
                <p style={{marginTop: '10px', color: uploadStatus.includes('Error') ? 'red' : 'green'}}>
                  {uploadStatus}
                </p>
              )}
              
              <p className="file-support">Supports MP3, WAV, M4A, OGG, FLAC, AAC, WEBM files</p>
            </div>
          </div>

          {/* Meeting Summary */}
          <div className="summary-box">
            <h3>Meeting Summary</h3>
            <div className="summary-area">
              {transcript ? (
                <div style={{
                  textAlign: 'left', 
                  padding: '0px',
                  maxHeight: '100%',
                  overflowY: 'auto'
                }}>
                  <h4 style={{
                    marginTop: '0',
                    marginBottom: '10px',
                    color: '#333',
                    fontSize: '18px',
                    fontWeight: '600'
                  }}> Transcript:</h4>
                  <p style={{
                    lineHeight: '1.8', 
                    whiteSpace: 'pre-wrap',
                    color: '#444',
                    fontSize: '14px',
                    wordBreak: 'break-word'
                  }}>{transcript}</p>
                </div>
              ) : (
                <div style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  height: '100%'
                }}>
                  <img src="document.png" alt="document" />
                  <p>Upload a meeting audio file to see the transcript here</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </section>

     
    </>
  )
}

export default Meetings
