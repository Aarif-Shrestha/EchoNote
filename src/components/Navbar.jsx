import React, { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'

const Navbar = () => {
  const navigate = useNavigate();
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [user, setUser] = useState(null);
  const [showDropdown, setShowDropdown] = useState(false);

  useEffect(() => {
    // Check if user is logged in
    const token = localStorage.getItem('token');
    const userData = localStorage.getItem('user');
    
    if (token && userData) {
      setIsLoggedIn(true);
      setUser(JSON.parse(userData));
    }
  }, []);

  const handleLogout = () => {
    // Clear localStorage
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    
    // Update state
    setIsLoggedIn(false);
    setUser(null);
    setShowDropdown(false);
    
    // Redirect to home
    navigate('/');
  };

  // Extract username before @
  const getDisplayName = (email) => {
    if (!email) return '';
    return email.split('@')[0];
  };

  return (
    <section className='navbar-section'>
      <div className='logo'>
        <p>EN</p>
      </div>
      <div className='logo-name'>
        <p>EchoNote</p>
      </div>
      <div className='nav-link'>
        <Link to="/">Home</Link>
        <Link to="/meetings">
          Meetings
        </Link>
        <Link to="/chatbot">
          Chatbot
        </Link>
        <div className='logo2'>
          {isLoggedIn ? (
            // Show logged-in user with dropdown
            <div style={{ position: 'relative' }}>
              <div 
                onClick={() => setShowDropdown(!showDropdown)}
                style={{ 
                  color: '#000', 
                  fontSize: '16px', 
                  fontWeight: '500',
                  cursor: 'pointer',
                  padding: '8px 15px',
                  borderRadius: '5px',
                  background: showDropdown ? '#f0f0f0' : 'transparent',
                  transition: 'background 0.2s'
                }}
              >
                {getDisplayName(user?.username)}
              </div>
              
              {showDropdown && (
                <div 
                  style={{
                    position: 'absolute',
                    top: '100%',
                    right: '0',
                    marginTop: '5px',
                    background: '#fff',
                    border: '1px solid #ddd',
                    borderRadius: '5px',
                    boxShadow: '0 2px 10px rgba(0,0,0,0.1)',
                    minWidth: '150px',
                    zIndex: 1000
                  }}
                >
                  <div 
                    onClick={handleLogout}
                    style={{
                      padding: '12px 20px',
                      cursor: 'pointer',
                      color: '#000',
                      fontSize: '14px',
                      fontWeight: '500',
                      borderRadius: '5px',
                      transition: 'background 0.2s'
                    }}
                    onMouseEnter={(e) => e.target.style.background = '#f0f0f0'}
                    onMouseLeave={(e) => e.target.style.background = 'transparent'}
                  >
                    Logout
                  </div>
                </div>
              )}
            </div>
          ) : (
            // Show login icon
            <Link to="/login">
              <img src="/profile.png" alt="profile" />
            </Link>
          )}
        </div>
      </div>
    </section>
  )
}

export default Navbar
