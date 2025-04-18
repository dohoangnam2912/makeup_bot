import { Link } from 'react-router-dom';

export default function Home() {
  return (
    <div className="h-screen flex flex-col items-center justify-center text-center p-6">
      <h1 className="text-3xl font-bold mb-4">🏠 Welcome to RAG Chatbot</h1>
      <p className="mb-6">Click below to start chatting with AI:</p>
      <Link
        to="/chat"
        className="px-6 py-3 bg-blue-600 text-white rounded hover:bg-blue-700"
      >
        Go to Chat
      </Link>
    </div>
  );
}
