  import React from 'react'
  import Home from './components/Home'
  import Meetings from './components/Meetings'
  import {BrowserRouter as Router, Routes, Route} from 'react-router-dom'
import Chatbot from './components/Chatbot'
import Signup from './components/Signup'
import Login from './components/Login'

  const App = () => {
    return (
      <Router>
        <Routes>
          <Route path= "/" element={<Home/>}/>
          <Route path= "/meetings" element={<Meetings/>}/>
          <Route path= "/chatbot" element={<Chatbot/>}/>
          <Route path= "/signup" element={<Signup/>}/>
          <Route path= "/login" element={<Login/>}/>

        </Routes>
      </Router>
    
    )
  }

  export default App