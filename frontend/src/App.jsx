import { Routes, Route, Link } from 'react-router-dom';
import Home from './pages/Home';
import ChatInterface from './components/ChatInterface';

export default function App() {
  return (
    <div className="h-screen w-screen">
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/chat" element={<ChatInterface />} />
      </Routes>
    </div>
  );
}