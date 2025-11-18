import React from 'react'
import "../style/Home.css"
import { Link } from 'react-router-dom'

const Home = () => {
  return (
    <>
      <section className='navbar-section'>
        <div className='logo'>
          <p>EN</p>
        </div>
        <div className='logo-name'>
          <p>EchoNote</p>
        </div>
        <div className='nav-link'>
          <Link  to = "/">Home</Link>
          <Link to = "/meetings">Meetings</Link>
          <Link to = "/chatbot">Chatbot</Link>
          <div className='logo2'>
            <Link to = "/login">
            <img src="/profile.png" alt="profile" /></Link>
            
          </div>
        </div>
      </section>

      


      <section className='hero-section1'>
        <div className='hero-row'>
          <h1>Your AI Meeting <br />    
            Assistant</h1>
          <p>Transcribe, Summarize, and Chat with Meetings</p>
        </div>
      </section>


      <section className='hero-section2'>
        <div className='hero-row2'>
          <div className='hero-message'>
            <h2>Transform your meeting recording into actionable insights.
            Upload audio,get instant transcripts, and interact with AI that
            understands your conversations.</h2>
          </div>
          <div className='button-section'>
            <div className='button'>
              <Link to= "/chatbot">
               <button className='viewdemo'>View Demo</button>
              </Link>
              <Link to= "/meetings">
              <button className='upload'>Upload Meeting</button>
              </Link>
              
              
            </div>
          </div>
        </div>
      </section>


      {/* Chat Window Section */}
      <section className="chat-window-section">
        <div className="chat-window">
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
      </section>


      <section className='hero-section3'>
        <div className='sid'>
            <h1>Everything you need for smarter meetings</h1>
        </div>
      </section>



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