import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Upload, Clock, WifiOff } from 'lucide-react';

import logger from '../utils/logger'; 

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const Admin = () => {
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState('');
  const [loading, setLoading] = useState(false);
  
  const [metadata, setMetadata] = useState({ 
    last_updated: "Checking status...", 
    filename: "Checking status..." 
  });
  
  const [isOffline, setIsOffline] = useState(false);

  useEffect(() => {
    logger.info("Checking backend status on component load...", "Admin");
    
    axios.get(`${API_URL}/admin/status`)
      .then(res => {
        setMetadata(res.data);
        setIsOffline(false);
        logger.info("Successfully connected to backend.", "Admin");
      })
      .catch((err) => {
        setMetadata({ 
          last_updated: "Connection Error", 
          filename: "Backend Disconnected" 
        });
        setIsOffline(true);
        logger.error("Failed to connect to backend. Is the Python server running?", "Admin");
      });
  }, []);

  const handleUploadAndProcess = async () => {
    if (!file) return alert("Please select a CSV file first.");
    
    setLoading(true);
    setStatus("Uploading CSV file...");
    logger.info("Starting CSV upload process...", "Admin");

    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const uploadRes = await axios.post(`${API_URL}/admin/upload`, formData);
      
      if (uploadRes.data.status === "success") {
        setStatus("File uploaded. Rebuilding Vector Database... (Takes 1-2 mins)");
        logger.info("CSV uploaded successfully. Triggering database rebuild...", "Admin");
        
        const rebuildRes = await axios.post(`${API_URL}/admin/rebuild`);
        
        if (rebuildRes.data.status === "success") {
          setStatus("Success! System updated successfully.");
          logger.info("Vector database rebuilt successfully.", "Admin");
          
          const newStatus = await axios.get(`${API_URL}/admin/status`);
          setMetadata(newStatus.data);
          setIsOffline(false);
        } else {
          setStatus("Rebuild failed: " + rebuildRes.data.message);
          logger.error("Database rebuild failed: " + rebuildRes.data.message, "Admin");
        }
      }
    } catch (error) {
      setStatus("Connection error. Is the backend running?");
      setIsOffline(true);
      logger.error("Network error during upload or rebuild process.", "Admin");
    } finally {
      setLoading(false);
      setFile(null);
    }
  };

  return (
    <div className="admin-container">
      <h2>Admin Data Management</h2>
      <a href="/" className="back-link">Back to Chat</a>
      
      <div className="admin-card" style={{background: "#f8f9fa", borderLeft: isOffline ? "4px solid #dc3545" : "4px solid #007bff"}}>
        <h3 style={{margin: "0 0 10px 0"}}>
          <Clock size={18} /> Current Database Status 
          {isOffline && <span style={{color: 'red', marginLeft: '10px'}}><WifiOff size={16} style={{verticalAlign: "middle"}} /> Offline</span>}
        </h3>
        <p style={{margin: "0", color: isOffline ? 'red' : 'black'}}><strong>Last Updated:</strong> {metadata.last_updated}</p>
        <p style={{margin: "5px 0 0 0", color: isOffline ? 'red' : 'black'}}><strong>File Name:</strong> {metadata.filename}</p>
      </div>

      <div className="admin-card">
        <h3><Upload size={20} /> Upload New CSV</h3>
        <p>Select file and click process. System will auto-rebuild.</p>
        
        <input type="file" accept=".csv" onChange={(e) => setFile(e.target.files[0])} disabled={loading} />
        <button onClick={handleUploadAndProcess} disabled={!file || loading} style={{ opacity: (!file || loading) ? 0.5 : 1 }}>
          {loading ? "Processing..." : "Upload & Process Data"}
        </button>
      </div>

      {status && <p className="status-msg">{status}</p>}
    </div>
  );
};

export default Admin;