import React from 'react'
import { Link } from 'react-router-dom'
import "../style/Chatbot.css"

const Chatbot = () => {
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

     
<section class="chatbot-section">
  <h1 class="chatbot-title">Meeting Chatbot</h1>
  <p class="chatbot-subtitle">Ask questions about your meeting content</p>

 
  <div class="context-section">
    <p className='context'>Context</p>
    <button class="context-btn">This Meeting</button>
    <p class="context-info">Currently analyzing: Product Planning Session (March 15, 2024)</p>
  </div>

  
  <div class="chat-window">
    <div class="chat-message">
      <p>
        Hello! I'm your AI meeting assistant. I can help you find information from your recent Product Planning Session. 
        What would you like to know?
      </p>
      <span class="chat-time">11:42 AM</span>
    </div>
    <div class="chat-input-section">
    <input type="text" placeholder="Ask a question about your meeting..." />
    <button class="send-btn">Send</button>
  </div>
  </div>

  
  


  <div class="suggested-questions">
    <p>Suggested Questions:</p>
    <div class="question-tags">
      <span>What were the main action items?</span>
      <span>Who is responsible for mobile optimization?</span>
      <span>What decisions were made?</span>
      <span>When is the follow-up meeting?</span>
    </div>
  </div>
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

export default Chatbot