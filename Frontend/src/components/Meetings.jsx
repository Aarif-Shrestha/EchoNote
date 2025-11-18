import React from 'react'
import { Link } from 'react-router-dom'
import "../style/Meetings.css"

const Meetings = () => {
  return (
    <>
      {/* Navbar */}
      <section className='navbar-section'>
        <div className='logo'>
          <p>EN</p>
        </div>
        <div className='logo-name'>
          <p>EchoNote</p>
        </div>
        <div className='nav-link'>
          <Link to="/">Home</Link>
          <Link to="/meetings">Meetings</Link>
          <Link to="/chatbot">Chatbot</Link>
           <div className='logo2'>
                      <Link to = "/login">
                      <img src="/profile.png" alt="profile" /></Link>
                      
                    </div>
        </div>
      </section>

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
            <input type="file" id="fileInput" style={{display: 'none'}} accept=".mp3,.wav,.m4a" />
              <p>Drag and drop your audio file here, or click to browse</p>
              <button className="choose-btn" onClick={()=> document.getElementById("fileInput").click()}>Choose File</button>
              <p className="file-support">Supports MP3, WAV, M4A files up to 100MB</p>
            </div>
          </div>

          {/* Meeting Summary */}
          <div className="summary-box">
            <h3>Meeting Summary</h3>
            <div className="summary-area">
              <img src="document.png" alt="document" />
              <p>Upload a meeting audio file to see the summary here</p>
            </div>
          </div>
        </div>
      </section>

     
    </>
  )
}

export default Meetings
