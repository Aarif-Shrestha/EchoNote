import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import "../style/Login.css"
import Navbar from './Navbar'

const Login = () => {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const handleLogin = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess("");
    try {
      const res = await fetch("http://localhost:5000/api/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: email, password })
      });
      const data = await res.json();
      if (res.ok) {
        setSuccess("Login successful! Redirecting...");
        
        // Store JWT token and user info in localStorage
        localStorage.setItem('token', data.token);
        localStorage.setItem('user', JSON.stringify(data.user));
        
        // Redirect to home page after 1 second
        setTimeout(() => {
          navigate('/');
        }, 1000);
      } else {
        setError(data.error || "Login failed");
      }
    } catch {
      setError("Network error");
    }
  };

  return (
     <>
      <Navbar />

     
<section class="login-section">

  

  <div className='app-wrapper'>
    <div className='main-content'>
      <div class="login-container">
    <div className='login-header'>
      <div class="logo-login">
      <p>EN</p>
    </div>
    <div class="logo-name-login">
      <p>EchoNote</p>
    </div>
      
    </div>
    
    <p class="signup-prompt">Don't have an account? <Link to="/signup">Sign up for free</Link></p>
    
    <form class="login-form" onSubmit={handleLogin}>
      <input type="email" placeholder="Email" required value={email} onChange={e => setEmail(e.target.value)} />
      <input type="password" placeholder="Password" required value={password} onChange={e => setPassword(e.target.value)} />
      <Link to="/forgot-password" class="forgot-password">Forgot your password?</Link>
      <button type="submit" className="email-btn">Log in</button>
    </form>
    {error && <p style={{color: 'red'}}>{error}</p>}
    {success && <p style={{color: 'green'}}>{success}</p>}
    {/* <button class="email-btn">
      <img src="/email-icon.png" alt="Email" class="btn-icon" />
      Log in 
    </button> */}
    
    {/* <p class="or-divider">Or</p> */}
    
    <button class="google-btn">
      {/* <img src="/google-icon.png" alt="google" class="btn-icon" /> */}
      Log in 
    </button>
    
    
    
    <p class="terms">By signing up, you agree to the <Link to="/terms">Terms and Conditions</Link> and <Link to="/privacy">Privacy Policy</Link></p>
  </div>
      
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

export default Login