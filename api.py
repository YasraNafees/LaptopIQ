import json
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
import os
import shutil

# Apne purane modules import karo
from creating_vectordatabase import build_vector_database
from Reterival_engine import create_chat_engine

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
    print(" Loading RAG System into Memory...")
    index, nodes = build_vector_database(force_rebuild=False)
    chat_engine = create_chat_engine(index, nodes)
    print(" System Ready for API Calls!")

@app.post("/chat")
async def chat_endpoint(message: str = Form(...), session_id: str = Form("default")):
    try:
        response = chat_engine.chat(message)
        return {"status": "success", "response": str(response)}
    except Exception as e:
        return {"status": "error", "response": str(e)}

@app.post("/admin/upload")
async def upload_csv(file: UploadFile = File(...)):
    try:
        
        upload_dir = "./Data_cleaning"
        os.makedirs(upload_dir, exist_ok=True)
        
        file_location = f"{upload_dir}/cleaned_laptop_data_for_rag.csv"
        with open(file_location, "wb+") as file_object:
            shutil.copyfileobj(file.file, file_object)
            
        
        save_metadata(file.filename)
            
        return {"status": "success", "message": "CSV uploaded successfully. Rebuilding DB..."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/admin/rebuild")
async def rebuild_database():
    global index, nodes, chat_engine
    try:
        index, nodes = build_vector_database(force_rebuild=True)
        chat_engine = create_chat_engine(index, nodes)
        return {"status": "success", "message": "Database rebuilt successfully!"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/admin/status")
async def check_status():
    return get_metadata()