import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './App.css'
import logger from "./utils/logger";
try {
  logger.info("Initializing React DOM root...", "main");
  
  ReactDOM.createRoot(document.getElementById('root')).render(
    <React.StrictMode>
      <App />
    </React.StrictMode>,
  )
  
  logger.info("React DOM root rendered successfully.", "main");
} catch (error) {
  
  logger.error("Critical error: Failed to render React application.", "main");
  console.error(error); 
}