// src/components/Header.js
import React from 'react';
import { Link } from 'react-router-dom';

function Header() {
  return (
    <header className="header">
      <div className="nav-container">
        <Link to="/" className="logo">
          RAG Assistant
        </Link>
        <nav className="nav-links">
          <Link to="/" className="nav-link">Home</Link>
          <Link to="/chat" className="nav-link">Chat</Link>
          <Link to="/documents" className="nav-link">Documents</Link>
        </nav>
      </div>
    </header>
  );
}

export default Header;