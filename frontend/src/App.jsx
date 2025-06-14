import { Routes, Route, Link } from 'react-router-dom';
import ChatInterface from './ChatInterface';

export default function App() {
  return (
    <div className="h-screen w-screen font-sans">
      <Routes>
        <Route path="/" element={<ChatInterface/>} />
      </Routes>
    </div>
  );
}