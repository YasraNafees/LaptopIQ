import json
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
import os
import shutil


from creating_vectordatabase import build_vector_database
from Reterival_engine import create_chat_engine
from logger import get_logger  


logger = get_logger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


index = None
nodes = None
chat_engine = None

METADATA_FILE = "upload_metadata.json"

def save_metadata(filename):
    data = {
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "filename": filename
    }
    with open(METADATA_FILE, "w") as f:
        json.dump(data, f)

def get_metadata():
    if os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, "r") as f:
            return json.load(f)
    return {"last_updated": "Never", "filename": "None"}

@app.on_event("startup")
def startup_event():
    global index, nodes, chat_engine
    logger.info("Loading RAG System into Memory...")
    index, nodes = build_vector_database(force_rebuild=False)
    chat_engine = create_chat_engine(index, nodes)
    logger.info("System Ready for API Calls!")

@app.post("/chat")
async def chat_endpoint(message: str = Form(...), session_id: str = Form("default")):
    try:
        
        logger.debug(f"Chat request | Session: {session_id} | Message: {message}")
        response = chat_engine.chat(message)
        return {"status": "success", "response": str(response)}
    except Exception as e:
        
        logger.error(f"Chat endpoint failed: {e}", exc_info=True)
        return {"status": "error", "response": str(e)}

@app.post("/admin/upload")
async def upload_csv(file: UploadFile = File(...)):
    try:
        logger.info(f"Received new CSV upload: {file.filename}")
        
        upload_dir = "./Data_cleaning"
        os.makedirs(upload_dir, exist_ok=True)
        
        file_location = f"{upload_dir}/cleaned_laptop_data_for_rag.csv"
        with open(file_location, "wb+") as file_object:
            shutil.copyfileobj(file.file, file_object)
            
        save_metadata(file.filename)
        logger.info("CSV uploaded and metadata saved successfully.")
            
        return {"status": "success", "message": "CSV uploaded successfully. Rebuilding DB..."}
    except Exception as e:
        logger.error(f"CSV Upload failed: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}

@app.post("/admin/rebuild")
async def rebuild_database():
    global index, nodes, chat_engine
    try:

        logger.warning("Database rebuild triggered via Admin API.")
        index, nodes = build_vector_database(force_rebuild=True)
        chat_engine = create_chat_engine(index, nodes)
        logger.info("Database rebuilt and Chat Engine updated successfully.")
        return {"status": "success", "message": "Database rebuilt successfully!"}
    except Exception as e:
        logger.error(f"Database rebuild failed: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}

@app.get("/admin/status")
async def check_status():
    return get_metadata()