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

      const data = await response.json();

      if (response.ok) {
        setTranscript(data.transcript);
        setUploadStatus('✅ Transcription complete!');
        setSelectedFile(null);
      } else {
        setUploadStatus(`Error: ${data.error}`);
      }
    } catch (error) {
      setUploadStatus(`Error: ${error.message}`);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <>
      <Navbar />

      {/* Meetings Section */}
      <section className="meetings-container">
        <h1 className="meetings-title">Meetings</h1>
        <p className="meetings-subtitle">
          Upload or record your meeting audio to get started
        </p>

        <div className="meetings-content">
          {/* Upload Meeting Audio */}
          <div className="upload-box">
            <h3>Upload Meeting Audio</h3>
            
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
