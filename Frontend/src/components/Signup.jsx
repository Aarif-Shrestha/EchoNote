import React from 'react'
import "../style/Signup.css"
import { Link } from 'react-router-dom'

const Signup = () => {
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
          <Link to="/">Home</Link>
          <Link to="/meetings">Meetings</Link>
          <Link to="/chatbot">Chatbot</Link>
          <div className='logo2'>
            {/* Wrap the image with Link to navigate to signup */}
             <div className='logo2'>
                        <Link to = "/login">
                        <img src="/profile.png" alt="profile" /></Link>
                        
                      </div>
          </div>
        </div>

        
      </section>

      <section>

        
        <div className="signup-container">
      <div className="signup-box">
        <div className='signup-logo'>
        EN</div>
        <h2 className="signup-title">Create an account</h2>
        <p className="signup-subtitle">Sign up to get started with EchoNote</p>

        <form className="signup-form">
          <input type="text" placeholder="Full Name" className="signup-input" />
          <input type="email" placeholder="Email Address" className="signup-input" />
          <input type="password" placeholder="Password" className="signup-input" />
          <input type="password" placeholder="Confirm Password" className="signup-input" />

          <button type="submit" className="signup-btn">Sign Up</button>
        </form>

        <p className="signup-footer">
          Already have an account? <a href="/login">Log in</a>
        </p>
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

export default Signup;
