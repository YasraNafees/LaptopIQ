import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    OPENROUTER_API_URL = os.getenv("OPENROUTER_API_BASE_URL")
    COHERE_API_KEY = os.getenv("COHERE_API_KEY")  
    
    
    
    if not OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY not set!")
    if not OPENROUTER_API_URL:
        raise ValueError("OPENROUTER_API_URL not set!")
    if not COHERE_API_KEY:
        raise ValueError("COHERE_API_KEY not set!")
    
    # Models
    EMBEDDING_MODEL = "text-embedding-3-small"
    LLM_MODEL = "google/gemini-2.5-flash-lite"
    COHERE_MODEL = "rerank-v3.5"
    
    # Paths
    CSV_PATH = os.getenv("DATA_FILE_PATH", "./Data_cleaning/cleaned_laptop_data_for_rag.csv")
    CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "./chroma_db")
    COLLECTION_NAME = os.getenv("COLLECTION_NAME", "laptops")
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "app.log")


config = Config()
print("Configuration loaded successfully!")