import { useState } from 'react';

export default function ChatInterface() {
  const [messages, setMessages] = useState([
    { from: 'bot', text: 'Hi! Ask me anything about your documents.' },
  ]);
  const [input, setInput] = useState('');

  const sendMessage = () => {
    if (!input.trim()) return;

    setMessages([...messages, { from: 'user', text: input }]);
    setInput('');
    
    // Simulate AI reply (replace with backend later)
    setTimeout(() => {
      setMessages(prev => [...prev, { from: 'bot', text: "I'm just a stub response for now 🤖" }]);
    }, 500);
  };

  return (
    <div className="flex h-screen">
      {/* Sidebar */}
      <aside className="w-64 bg-gray-100 p-4 border-r">
        <h2 className="font-semibold mb-4">🗂 Chat History</h2>
        <ul className="space-y-2 text-sm">
          <li className="cursor-pointer hover:underline">Chat 1</li>
          <li className="cursor-pointer hover:underline">Chat 2</li>
        </ul>
      </aside>

      {/* Main Chat Area */}
      <main className="flex-1 flex flex-col">
        {/* Header */}
        <header className="p-4 border-b bg-white font-semibold">
          Chat with RAG Assistant
        </header>

        {/* Message list */}
        <div className="flex-1 p-4 overflow-y-auto bg-gray-50 space-y-3">
          {messages.map((msg, idx) => (
            <div
              key={idx}
              className={`p-3 rounded max-w-lg ${
                msg.from === 'user'
                  ? 'bg-blue-600 text-white self-end'
                  : 'bg-white border self-start'
              }`}
            >
              {msg.text}
            </div>
          ))}
        </div>

        {/* Input */}
        <footer className="p-4 border-t bg-white">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              sendMessage();
            }}
            className="flex"
          >
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Type a message..."
              className="flex-1 border p-2 rounded-l"
            />
            <button
              type="submit"
              className="bg-blue-600 text-white px-4 rounded-r"
            >
              Send
            </button>
          </form>
        </footer>
      </main>
    </div>
  );
}
