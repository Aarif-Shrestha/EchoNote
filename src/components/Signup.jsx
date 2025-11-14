import React, { useState } from 'react'
import "../style/Signup.css"
import { Link, useNavigate } from 'react-router-dom'
import Navbar from './Navbar'

const Signup = () => {
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const handleSignup = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess("");
    if (password !== confirm) {
      setError("Passwords do not match");
      return;
    }
    try {
      const res = await fetch("/api/signup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });
      const data = await res.json();
      if (res.ok) {
        setSuccess("Signup successful! Redirecting to login...");
        // Redirect to login page after 1 second
        setTimeout(() => {
          navigate('/login');
        }, 1000);
      } else {
        setError(data.error || "Signup failed");
      }
    } catch {
      setError("Network error");
    }
  };

  return (
    <>
      <Navbar />

      <section>
        <div className="signup-container">
          <div className="signup-box">
            <div className='signup-logo'>
            EN</div>
            <h2 className="signup-title">Create an account</h2>
            <p className="signup-subtitle">Sign up to get started with EchoNote</p>

            <form className="signup-form" onSubmit={handleSignup}>
              <input type="text" placeholder="Full Name" className="signup-input" value={name} onChange={e => setName(e.target.value)} />
              <input type="email" placeholder="Email Address" className="signup-input" value={email} onChange={e => setEmail(e.target.value)} />
              <input type="password" placeholder="Password" className="signup-input" value={password} onChange={e => setPassword(e.target.value)} />
              <input type="password" placeholder="Confirm Password" className="signup-input" value={confirm} onChange={e => setConfirm(e.target.value)} />
              <button type="submit" className="signup-btn">Sign Up</button>
            </form>
            {error && <p style={{color: 'red'}}>{error}</p>}
            {success && <p style={{color: 'green'}}>{success}</p>}

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
