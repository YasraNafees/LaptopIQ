import os
import sys
import chromadb

from llama_index.llms.openrouter import OpenRouter
from llama_index.core import Settings, VectorStoreIndex
from llama_index.core.node_parser import SentenceSplitter
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core import StorageContext
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

from data_ingestion import load_and_clean_data
from config import Config
from logger import logger


def build_vector_database(force_rebuild=False):
    
    try:
        print("\n" + "="*50)
        print(" INITIALIZING RAG SYSTEM")
        print("="*50)
        
        # Step 1: Load Embedding Model
        print("\n  Step 1/5: Loading Embedding Model...")
        print(f"   Model: {Config.EMBEDDING_MODEL}")
        print("    This may take 1-3 minutes on first run...")
        
        # ✅ FIXED: token ko model_kwargs mein pass kiya
        embed_model = HuggingFaceEmbedding(
        model_name=Config.EMBEDDING_MODEL,
        model_kwargs={"token": Config.HF_TOKEN}
        )
        print("    Embedding model loaded!")
        
        # Step 2: Initialize LLM
        print("\n🤖 Step 2/5: Connecting to LLM...")
        llm = OpenRouter(
            model=Config.LLM_MODEL,
            api_key=Config.OPENROUTER_API_KEY,
            api_base=Config.OPENROUTER_API_URL,
        )
        Settings.llm = llm
        Settings.embed_model = embed_model
        print("    LLM connected!")
        
        # Step 3: Load Documents
        print("\n Step 3/5: Loading documents...")
        raw_documents = load_and_clean_data(Config.CSV_PATH)
        
        print("    Splitting into chunks...")
        splitter = SentenceSplitter(chunk_size=256, chunk_overlap=20)
        nodes = splitter.get_nodes_from_documents(raw_documents, show_progress=True)
        print(f"    Created {len(nodes)} chunks")
        
        # Step 4: Build/Load Vector DB
        print("\n Step 4/5: Setting up Vector Database...")
        
        db_exists = os.path.exists(Config.CHROMA_DB_PATH) and len(os.listdir(Config.CHROMA_DB_PATH)) > 0

        if db_exists and not force_rebuild:
            print("    Loading existing database...")
            db = chromadb.PersistentClient(path=Config.CHROMA_DB_PATH)
            chroma_collection = db.get_collection(Config.COLLECTION_NAME)
            vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
            index = VectorStoreIndex.from_vector_store(vector_store, embed_model=embed_model)
            print("    Database loaded!")
        else:
            print("   Building NEW database...")
            print("   Embedding all chunks...")
            
            db = chromadb.PersistentClient(path=Config.CHROMA_DB_PATH)
            chroma_collection = db.get_or_create_collection(Config.COLLECTION_NAME)
            vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
            storage_context = StorageContext.from_defaults(vector_store=vector_store)
            
            index = VectorStoreIndex(
                nodes=nodes,
                storage_context=storage_context,
                show_progress=True
            )
            
            index.storage_context.persist(persist_dir=Config.CHROMA_DB_PATH)
            print("    Database built and saved!")
        
        # Step 5: Complete
        print(f"\n Step 5/5: System Ready! {len(nodes)} chunks loaded")
        print("="*50 + "\n")
        
        return index, nodes

    except Exception as e:
        logger.error(f"Vector DB build failed: {e}", exc_info=True)
        print(f"\n FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    build_vector_database()