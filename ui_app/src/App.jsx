import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { useEffect } from 'react';
import Chat from './pages/Chat.jsx';
import Admin from './pages/Admin.jsx';
import logger from './utils/logger';

function App() {
  useEffect(() => {
    
    logger.info("React Application started successfully.", "App");
  }, []);

  return (
    <Router>
      <div className="app-container">
        <Routes>
          <Route path="/" element={<Chat />} />
          <Route path="/admin" element={<Admin />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;