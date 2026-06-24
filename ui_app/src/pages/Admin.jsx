import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Upload, Clock, WifiOff } from 'lucide-react';

const Admin = () => {
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState('');
  const [loading, setLoading] = useState(false);
  
  // ✅ FIX: State mein sirf PLAIN TEXT rakhenge, koi JSX nahi
  const [metadata, setMetadata] = useState({ 
    last_updated: "Checking status...", 
    filename: "Checking status..." 
  });
  
  // ✅ FIX: Connection error track karne ke liye alag boolean state
  const [isOffline, setIsOffline] = useState(false);

  useEffect(() => {
    axios.get('http://localhost:8000/admin/status')
      .then(res => {
        setMetadata(res.data);
        setIsOffline(false); // Connected
      })
      .catch(() => {
        setMetadata({ 
          last_updated: "Connection Error", 
          filename: "Backend Disconnected" 
        });
        setIsOffline(true); // Disconnected
      });
  }, []);

  const handleUploadAndProcess = async () => {
    if (!file) return alert("Please select a CSV file first.");
    setLoading(true);
    setStatus("⏳ Uploading CSV file...");

    try {
      const formData = new FormData();
      formData.append('file', file);
      const uploadRes = await axios.post('http://localhost:8000/admin/upload', formData);
      
      if (uploadRes.data.status === "success") {
        setStatus("✅ File uploaded! ⏳ Rebuilding Vector Database... (Takes 1-2 mins)");
        const rebuildRes = await axios.post('http://localhost:8000/admin/rebuild');
        
        if (rebuildRes.data.status === "success") {
          setStatus("🎉 Success! System updated successfully.");
          const newStatus = await axios.get('http://localhost:8000/admin/status');
          setMetadata(newStatus.data);
          setIsOffline(false);
        } else {
          setStatus("❌ Rebuild failed: " + rebuildRes.data.message);
        }
      }
    } catch (error) {
      setStatus("❌ Connection error. Is the backend running?");
      setIsOffline(true);
    } finally {
      setLoading(false);
      setFile(null);
    }
  };

  return (
    <div className="admin-container">
      <h2>Admin Data Management</h2>
      <a href="/" className="back-link">← Back to Chat</a>
      
      {/* ✅ FIX: Icon ko conditionally JSX mein render karo, state mein nahi */}
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