import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Chat from './pages/Chat.jsx';
import Admin from './pages/Admin.jsx';

function App() {
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