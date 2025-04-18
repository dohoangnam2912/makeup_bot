// src/components/DocumentManager.js
import React, { useState, useEffect, useRef } from 'react';
import { FaFileUpload, FaFileAlt, FaFilePdf, FaFileWord, FaFileCode, FaTrash } from 'react-icons/fa';
import api from '../services/api';

function DocumentManager() {
  const [documents, setDocuments] = useState([]);
  const [file, setFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const fileInputRef = useRef(null);

  // Fetch all documents on component mount
  useEffect(() => {
    fetchDocuments();
  }, []);

  // Fetch documents from the API
  const fetchDocuments = async () => {
    try {
      setIsLoading(true);
      const response = await api.get('/list-docs');
      setDocuments(response.data);
      setError('');
    } catch (err) {
      setError('Failed to load documents. Please try again later.');
      console.error('Error fetching documents:', err);
    } finally {
      setIsLoading(false);
    }
  };

  // Handle file selection
  const handleFileChange = (e) => {
    if (e.target.files.length > 0) {
      const selectedFile = e.target.files[0];
      const extension = selectedFile.name.split('.').pop().toLowerCase();
      
      if (['pdf', 'docx', 'html'].includes(extension)) {
        setFile(selectedFile);
        setError('');
      } else {
        setFile(null);
        setError('Unsupported file type. Please upload PDF, DOCX, or HTML files.');
      }
    }
  };

  // Handle file upload
  const handleUpload = async () => {
    if (!file) {
      setError('Please select a file to upload.');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

    try {
      setIsUploading(true);
      setError('');
      
      const response = await api.post('/upload-doc', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      setSuccess(`File ${file.name} has been successfully uploaded and indexed.`);
      setFile(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
      
      // Refresh the documents list
      fetchDocuments();
      
      // Clear success message after 5 seconds
      setTimeout(() => {
        setSuccess('');
      }, 5000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to upload file. Please try again.');
      console.error('Error uploading file:', err);
    } finally {
      setIsUploading(false);
    }
  };

  // Handle document deletion
  const handleDelete = async (fileId) => {
    try {
      await api.post('/delete-doc', { file_id: fileId });
      
      // Refresh the documents list
      fetchDocuments();
      setSuccess('Document has been successfully deleted.');
      
      // Clear success message after 5 seconds
      setTimeout(() => {
        setSuccess('');
      }, 5000);
    } catch (err) {
      setError('Failed to delete document. Please try again.');
      console.error('Error deleting document:', err);
    }
  };

  // Get icon for document based on file extension
  const getDocumentIcon = (fileName) => {
    const extension = fileName.split('.').pop().toLowerCase();
    
    switch (extension) {
      case 'pdf':
        return <FaFilePdf className="document-icon" />;
      case 'docx':
        return <FaFileWord className="document-icon" />;
      case 'html':
        return <FaFileCode className="document-icon" />;
      default:
        return <FaFileAlt className="document-icon" />;
    }
  };

  // Format date for display
  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  return (
    <div className="document-manager">
      <h2>Document Manager</h2>
      
      {error && <div className="error-message">{error}</div>}
      {success && <div className="success-message">{success}</div>}
      
      <div className="upload-section">
        <input
          type="file"
          id="file-upload"
          className="upload-input"
          accept=".pdf,.docx,.html"
          onChange={handleFileChange}
          ref={fileInputRef}
        />
        <label htmlFor="file-upload" className="upload-label">
          <FaFileUpload className="upload-icon" />
          <span>Click to select a PDF, DOCX, or HTML file</span>
          {file && (
            <div className="file-info">
              <strong>Selected file:</strong> {file.name}
            </div>
          )}
        </label>
        <button 
          className="upload-button" 
          onClick={handleUpload} 
          disabled={!file || isUploading}
        >
          {isUploading ? 'Uploading...' : 'Upload Document'}
        </button>
      </div>
      
      <h3>Your Documents</h3>
      
      {isLoading ? (
        <div className="loading-spinner">
          <div className="spinner"></div>
        </div>
      ) : documents.length > 0 ? (
        <div className="documents-list">
          {documents.map((doc) => (
            <div className="document-card" key={doc.id || doc.file_id}>
              <button 
                className="delete-button" 
                onClick={() => handleDelete(doc.id || doc.file_id)}
                aria-label="Delete document"
              >
                <FaTrash />
              </button>
              <div className="document-name">
                {getDocumentIcon(doc.file_name)}
                {doc.file_name}
              </div>
              <div className="document-date">
                Uploaded: {formatDate(doc.upload_timestamp)}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <p>No documents found. Upload a document to get started.</p>
      )}
    </div>
  );
}

export default DocumentManager;