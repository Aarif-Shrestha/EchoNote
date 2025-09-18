import "./App.css";

export default function App() {
  return (
    <div className="app">
      {/* Navbar */}
      <header className="navbar">
        <div className="logo">
          <span className="logo-box">EN</span>
          <span className="logo-text">EchoNote</span>
        </div>
        <nav>
          <a href="#" className="active">Home</a>
          <a href="#">Meetings</a>
          <a href="#">Chatbot</a>
          <a href="#">⚙️</a>
        </nav>
      </header>

      {/* Hero Section */}
      <section className="hero">
        <h1>Your AI Meeting Assistant</h1>
        <p className="subtitle">Transcribe, Summarize, and Chat with Meetings</p>
        <p className="description">
          Transform your meeting recordings into actionable insights. Upload audio,
          get instant transcripts, and interact with an AI that understands your conversations.
        </p>
        <div className="hero-buttons">
          <button className="btn primary">Upload Meeting</button>
          <button className="btn secondary">View Demo</button>
        </div>

        <div className="chatbox">
          <p><b>John:</b> Let’s discuss the quarterly results...</p>
          <p><b>Sarah:</b> That works. Let’s look at Q2...</p>
          <p className="ai">AI: Do you want me to recap notes?</p>
        </div>
      </section>

      {/* Features */}
      <section className="features">
        <h2>Everything you need for smarter meetings</h2>
        <div className="feature-grid">
          <div className="feature-card">
            <div className="icon">⚡</div>
            <h3>Fast Transcription</h3>
            <p>Get accurate transcripts in seconds with our advanced AI technology.</p>
          </div>
          <div className="feature-card">
            <div className="icon">📄</div>
            <h3>Action Items</h3>
            <p>Automatically extract action items and key decisions from your meetings.</p>
          </div>
          <div className="feature-card">
            <div className="icon">🤖</div>
            <h3>AI Chat</h3>
            <p>Ask questions about your meetings and get instant, intelligent answers.</p>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="cta">
        <h2>Ready to transform your meetings?</h2>
        <p>
          Join thousands of teams already using MeetingAI to make their meetings more productive.
        </p>
        <button className="btn gradient">Get Started Now</button>
      </section>

      {/* Footer */}
      <footer className="footer">
        © 2025 EchoNote. All rights reserved.
      </footer>
    </div>
  );
}
