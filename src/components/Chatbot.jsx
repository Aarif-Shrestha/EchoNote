import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import "../style/Chatbot.css"
import Navbar from './Navbar'

const initialQuestions = [
  "What were the main action items?",
  "Who is responsible for mobile optimization?",
  "What decisions were made?",
  "When is the follow-up meeting?"
]

const Chatbot = () => {
  const navigate = useNavigate();
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [meetings, setMeetings] = useState([])
  const [selectedMeeting, setSelectedMeeting] = useState("")
  const [selectedTranscript, setSelectedTranscript] = useState("")
  const [suggestedQuestions, setSuggestedQuestions] = useState(initialQuestions)
  const [messages, setMessages] = useState([
    {
      sender: "bot",
      text: "Hello! I'm your AI meeting assistant. Please select a meeting from the dropdown above to get started.",
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
  ])
  const [input, setInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)

  useEffect(() => {
    const token = localStorage.getItem('token');
    setIsLoggedIn(!!token);
    
    // Fetch user's meetings if logged in
    if (token) {
      fetchUserMeetings(token);
    }
  }, [])

  const fetchUserMeetings = async (token) => {
    try {
      const response = await fetch('/api/user_meetings', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.status === 401) {
        // Token expired or invalid
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        setIsLoggedIn(false);
        navigate('/login');
        return;
      }
      
      if (response.ok) {
        const data = await response.json();
        setMeetings(data.meetings || []);
      }
    } catch (error) {
      console.error('Error fetching meetings:', error);
      setMeetings([]);
    }
  };

  // Fetch transcript when meeting is selected
  useEffect(() => {
    if (selectedMeeting) {
      fetchTranscript(selectedMeeting);
    } else {
      setSelectedTranscript("");
      setSuggestedQuestions(initialQuestions);
    }
  }, [selectedMeeting]);

  // Show full transcript in chat as a bot message (verbatim)
  const handleShowTranscript = (e) => {
    if (!handleProtectedAction(e)) return;
    if (!selectedTranscript) return;
    const paragraphs = splitIntoSpeakerParagraphs(selectedTranscript);
    const newMessages = paragraphs.map(p => ({
      sender: 'bot',
      text: p,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }));
    setMessages(prev => [...prev, ...newMessages]);
    // hide suggestions after showing transcript
    hideSuggestions();
  };

  // Return true if the question is a transcript request (including common misspellings)
  const isTranscriptQuery = (q) => {
    if (!q) return false;
    const qLower = q.trim().toLowerCase();
    const triggers = [
      "show transcript", "display transcript", "show me the transcript",
      "display the transcript", "view transcript", "see transcript",
      "full transcript", "entire transcript", "whole transcript",
      "read transcript", "give me transcript", "get transcript",
      "transcript please", "show full", "transcript", "trans", "show trans"
    ];
    const misspellings = ["transciot", "transcipt", "transcipt", "transciipt", "transciot"];
    return triggers.some(t => qLower.includes(t)) || misspellings.some(m => qLower.includes(m)) || qLower === 'transcript' || qLower === 'trans';
  }

  // Split transcript into speaker paragraphs. It attempts to split before speaker labels like "Speaker 2:" or "Name:"
  const splitIntoSpeakerParagraphs = (text) => {
    if (!text) return [];
    // Normalize newlines
    const norm = text.replace(/\r\n/g, '\n').trim();
    // Split before occurrences of 'Speaker X:' or any 'Name:' pattern
    const parts = norm.split(/(?=(?:Speaker\s*\d+:)|(?:[A-Za-z][A-Za-z0-9 .'-]+:))/g)
      .map(p => p.trim())
      .filter(p => p.length > 0);
    // If splitting produced only one long block, fallback to splitting on double newlines
    if (parts.length <= 1) {
      return norm.split(/\n{2,}/).map(p => p.replace(/\n+/g, ' ').trim()).filter(Boolean);
    }
    // Clean up internal newlines inside each part
    return parts.map(p => p.replace(/\n+/g, ' ').trim());
  }

  const fetchTranscript = async (meetingId) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/meeting/${meetingId}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.status === 401) {
        // Token expired or invalid
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        setIsLoggedIn(false);
        navigate('/login');
        return;
      }
      
      if (response.ok) {
        const data = await response.json();
        setSelectedTranscript(data.transcript || "");
        
        // Update initial message when meeting is selected
        setMessages([
          {
            sender: "bot",
            text: `Great! I've loaded the transcript for "${data.meeting_name}". You can ask me questions about this meeting, or use the suggested questions below.`,
            time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
          }
        ]);
        
        // Update suggested questions based on transcript
        updateSuggestedQuestions(data.transcript);
      }
    } catch (error) {
      console.error('Error fetching transcript:', error);
      setSelectedTranscript("");
    }
  };

  const updateSuggestedQuestions = (transcript) => {
    if (!transcript) {
      setSuggestedQuestions(initialQuestions);
      return;
    }
    
    // Generate context-aware questions
    const contextQuestions = [
      "What were the main topics discussed?",
      "Can you summarize this meeting?",
      "What action items were mentioned?",
      "Who participated in this meeting?"
    ];
    setSuggestedQuestions(contextQuestions);
  };

  const handleProtectedAction = (e) => {
    if (!isLoggedIn) {
      e?.preventDefault();
      navigate('/login');
      return false;
    }
    return true;
  };

  // Hide suggestions after any user action
  const hideSuggestions = () => setSuggestedQuestions([]);

  // Function to call Ollama backend
  const askOllama = async (question) => {
    if (!selectedTranscript) {
      return "Please select a meeting from the dropdown above to start asking questions.";
    }

    // Client-side quick handling: if user asks for the transcript (or typoed variants),
    // immediately return the verbatim transcript without calling the backend model.
    const qLower = question.trim().toLowerCase();
    const transcriptTriggers = [
      "show transcript", "display transcript", "show me the transcript",
      "display the transcript", "view transcript", "see transcript",
      "full transcript", "entire transcript", "whole transcript",
      "read transcript", "give me transcript", "get transcript",
      "transcript please", "show full", "transcript", "trans", "show trans"
    ];
    const misspellings = ["transciot", "transcipt", "transcipt", "transciipt", "transciot"];

    if (
      transcriptTriggers.some(t => qLower.includes(t)) ||
      misspellings.some(m => qLower.includes(m)) ||
      qLower === "transcript" || qLower === "trans"
    ) {
      // Return the selected transcript directly (no extra prefix)
      // Collapse newlines so it appears as one line in chat
      return selectedTranscript.replace(/\n+/g, ' ');
    }

    setIsLoading(true);

    try {
      const token = localStorage.getItem('token');
      
      // Filter out "thanks" messages from history
      const filteredMessages = messages.filter(
        msg => msg.sender === "user" && !["thanks", "thank you", "thank u"].includes(msg.text.toLowerCase())
      );
      
      // Build chat history for context
      const chatHistory = [];
      for (let i = 0; i < filteredMessages.length - 1; i += 2) {
        if (filteredMessages[i] && filteredMessages[i + 1]) {
          chatHistory.push({
            question: filteredMessages[i].text,
            answer: filteredMessages[i + 1].text
          });
        }
      }

      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          transcript: selectedTranscript,
          question: question,
          chat_history: chatHistory,
          model_name: 'gemma:2b'
        })
      });

      if (response.status === 401) {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        setIsLoggedIn(false);
        navigate('/login');
        return null;
      }

      const data = await response.json();
      
      if (data.error) {
        return `Error: ${data.error}`;
      }

      return data.answer;
    } catch (error) {
      console.error('Error calling Ollama:', error);
      return "Sorry, I encountered an error. Please make sure Ollama is running and try again.";
    } finally {
      setIsLoading(false);
    }
  };

  const handleQuestionClick = async (question) => {
    if (!handleProtectedAction()) return;
    
    const userMessage = { 
      sender: "user", 
      text: question, 
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) 
    };
    
    setMessages(prevMessages => [...prevMessages, userMessage]);
    hideSuggestions();
    
    // Get Ollama response
    const answer = await askOllama(question);

    if (answer) {
      if (isTranscriptQuery(question)) {
        // Split transcript into paragraphs and insert each as its own bot message
        const paragraphs = splitIntoSpeakerParagraphs(answer);
        const newMessages = paragraphs.map(p => ({
          sender: 'bot',
          text: p,
          time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }));
        setMessages(prev => [...prev, ...newMessages]);
      } else {
        const botMessage = {
          sender: "bot",
          text: answer,
          time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        };
        setMessages(prevMessages => [...prevMessages, botMessage]);
      }
    }
  };

  const handleSend = async () => {
    if (!handleProtectedAction()) return;
    if (!input.trim()) return;
    
    const question = input;
    const userMessage = { 
      sender: "user", 
      text: question, 
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) 
    };
    
    setMessages(prevMessages => [...prevMessages, userMessage]);
    setInput("");
    hideSuggestions();
    
    // Get Ollama response
    const answer = await askOllama(question);

    if (answer) {
      if (isTranscriptQuery(question)) {
        const paragraphs = splitIntoSpeakerParagraphs(answer);
        const newMessages = paragraphs.map(p => ({
          sender: 'bot',
          text: p,
          time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }));
        setMessages(prev => [...prev, ...newMessages]);
      } else {
        const botMessage = {
          sender: "bot",
          text: answer,
          time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        };
        setMessages(prevMessages => [...prevMessages, botMessage]);
      }
    }
  };

  const handleMeetingChange = (e) => {
    if (!handleProtectedAction(e)) return;
    setSelectedMeeting(e.target.value);
  };

  return (
     <>
      <Navbar />

     
<section className="chatbot-section">
  <h1 className="chatbot-title">Meeting Chatbot</h1>
  <p className="chatbot-subtitle">Ask questions about your meeting content</p>

 
  <div className="context-section">
    <p className='context'>Context</p>
    <select
      className="context-dropdown"
      value={selectedMeeting}
      onChange={handleMeetingChange}
    >
      <option value="">Choose Meeting</option>
      {meetings.map(meeting => (
        <option key={meeting.meeting_id} value={meeting.meeting_id}>{meeting.meeting_name}</option>
      ))}
    </select>
    <p className="context-info">
      {selectedMeeting
        ? `Currently analyzing: ${meetings.find(m => m.meeting_id === selectedMeeting)?.meeting_name}`
        : "No meeting selected"}
    </p>
    {/* Button to show the full transcript verbatim in the chat */}
    <div style={{marginTop: '8px'}}>
      <button className="show-transcript-btn" onClick={handleShowTranscript} disabled={!selectedTranscript}>
        Show full transcript
      </button>
    </div>
  </div>

  
  <div className="chat-window">
    {messages.map((msg, idx) => (
      <div className={`chat-message ${msg.sender}`} key={idx}>
        <p>{msg.text}</p>
        <span className="chat-time">{msg.time}</span>
      </div>
    ))}
    {isLoading && (
      <div className="chat-message bot">
        <p>🤔 Thinking...</p>
      </div>
    )}
    {suggestedQuestions.length > 0 && (
      <div className="suggested-questions" style={{marginBottom: '10px'}}>
        <p>Suggested Questions:</p>
        <div className="question-tags">
          {suggestedQuestions.map(q => (
            <span key={q} onClick={() => handleQuestionClick(q)} style={{cursor: 'pointer'}}>{q}</span>
          ))}
        </div>
      </div>
    )}
    <div className="chat-input-section">
      <input
        type="text"
        placeholder="Ask a question about your meeting..."
        value={input}
        onChange={e => setInput(e.target.value)}
        onFocus={(e) => {
          if(handleProtectedAction(e)) hideSuggestions();
        }}
        onKeyDown={e => { if (e.key === 'Enter' && !isLoading) handleSend(); }}
        disabled={isLoading}
      />
      <button className="send-btn" onClick={handleSend} disabled={isLoading}>
        {isLoading ? '...' : 'Send'}
      </button>
    </div>
  </div>

  
  


  {/* Removed duplicate suggested questions outside chat window */}
</section>


<section>
  <div className='footer-section'></div>
  <footer className="footer">
  <p>© 2024 EchoNote. All rights reserved.</p>
</footer>

</section>


      </>
    

    

    
  )
}

export default Chatbot