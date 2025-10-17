import React, { useState, useEffect } from 'react'
import "../style/Home.css"
import { Link, useNavigate } from 'react-router-dom'
import Navbar from './Navbar'

const Home = () => {
  const navigate = useNavigate();
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem('token');
    setIsLoggedIn(!!token);
  }, []);

  const handleProtectedAction = (e, path) => {
    if (!isLoggedIn) {
      e.preventDefault();
      navigate('/login');
      return false;
    }
    navigate(path);
    return true;
  };

  return (
    <>
      <Navbar />

      


      <section className='hero-section1'>
        <div className='hero-row'>
          <div className='hero-left'>
            <h1 className='hero-title'>Your AI Meeting<br />Assistant</h1>
            {/* <h2 className='hero-subtitle'>Transcribe, Summarize,<br />and Chat with Meetings</h2> */}
            <p className='hero-desc'>Transform your meeting recordings into actionable insights. Upload audio, get instant transcripts, and interact with an AI that understands your conversations.</p>
            <div className='button-section'>
              <button className='viewdemo' onClick={(e) => handleProtectedAction(e, '/chatbot')}>
                View Demo
              </button>
              <button className='upload' onClick={(e) => handleProtectedAction(e, '/meetings')}>
                Upload Meeting
              </button>
            </div>
          </div>
          <div className='hero-right'>
            <div className="chat-window small">
              <div className="chat-window-header">
                <span className="dot red"></span>
                <span className="dot yellow"></span>
                <span className="dot green"></span>
              </div>
              <div className="chat-window-body">
                <div className="chat-line">
                  <span className="chat-user john">John:</span>
                  <span className="chat-text">Let's discuss the quarterly results...</span>
                </div>
                <div className="chat-line">
                  <span className="chat-user sarah">Sarah:</span>
                  <span className="chat-text">The numbers look great this quarter...</span>
                </div>
                <div className="chat-question">
                  <span className="chat-question-text">💬What were the key action items?</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>


      {/* ...existing code... */}


      <section className="features-section">
        
        <div className="features-row">
          <div className="feature-card">
            <div className="feature-icon">⚡</div>
            <h3>Fast Transcription</h3>
            <p>Get accurate transcripts in seconds with our advanced AI technology</p>
          </div>

          <div className="feature-card">
            <div className="feature-icon">📝</div>
            <h3>Action Items</h3>
            <p>Automatically extract action items and key decisions from your meetings</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">🤖</div>
            <h3>AI Chat</h3>
            <p>Ask questions about your meetings and get instant, intelligent answers</p>
          </div>
        </div>
      </section>

      <section className='hero-section4'>
        <div className='sid2'>
            <div><h1>Ready to transform your <br />meetings?    </h1></div>
        </div>
        
      </section>

      <section className='hero-section4'>
        <div className='sid3'>
            <p>Join thousands of teams already using MeetingAI to make their meetings <br />more productive. </p>

        </div>
      </section>

      <section className='hero-section5'>
        <Link to="/login">
        <button className='button2'>
            Get Started Now
            </button>
        
        </Link>
            
        
      </section>

      <section>
  <div className='footer-section'></div>
  <footer class="footer">
  <p>© 2024 EchoNote. All rights reserved.</p>
</footer>

</section>

      

      
    </>

  )
}

export default Home