import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import ChatInterface from './components/ChatInterface';
import DocumentManager from './components/DocumentManager';
import Header from './components/Header';
import './App.css';

function App() {
  return (
    <Router>
      <div className="app-container">
        <Header />
        <div className="app-content">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/chat" element={<ChatInterface />} />
            <Route path="/documents" element={<DocumentManager />} />
          </Routes>
        </div>
      </div>
    </Router>
  );
}

function Home() {
  return (
    <div className="home-container">
      <h1>RAG Document Assistant</h1>
      <p>Welcome to the Retrieval Augmented Generation (RAG) document assistant.</p>
      
      <div className="features-grid">
        <div className="feature-card">
          <h3>Upload Documents</h3>
          <p>Upload your PDF, DOCX, and HTML files to add them to the knowledge base.</p>
          <Link to="/documents" className="feature-button">Manage Documents</Link>
        </div>
        
        <div className="feature-card">
          <h3>Chat with AI</h3>
          <p>Ask questions about your documents and get accurate, context-aware answers.</p>
          <Link to="/chat" className="feature-button">Start Chatting</Link>
        </div>
      </div>
    </div>
  );
}

export default App;