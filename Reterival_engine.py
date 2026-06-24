import sys
from typing import List

from llama_index.core import QueryBundle, Settings
from llama_index.core.retrievers import (
    BaseRetriever,
    VectorIndexAutoRetriever,
    QueryFusionRetriever,
)
from llama_index.core.vector_stores.types import MetadataInfo, VectorStoreInfo
from llama_index.retrievers.bm25 import BM25Retriever
from llama_index.postprocessor.cohere_rerank import CohereRerank
from llama_index.core.chat_engine import ContextChatEngine
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.storage.docstore import SimpleDocumentStore

from config import Config
from logger import logger


class SmartRoutingRetriever(BaseRetriever):
    def __init__(self, llm, broad_retriever, specific_retriever, memory_buffer):
        super().__init__()
        self._llm = llm
        self._broad_retriever = broad_retriever
        self._specific_retriever = specific_retriever
        self._memory = memory_buffer

    def _retrieve(self, query_bundle: QueryBundle) -> List:
        query_str = query_bundle.query_str
        
        # ✅ EXPANDED trigger words for follow-up detection
        trigger_words = [
            "first", "second", "third", "1st", "2nd", "3rd", 
            "option 1", "option 2", "option 3", "number 1", "number 2",
            "it", "that", "this one", "previous", 
            "bola tha", "manga tha", "wo laptop", "iska", "uska", 
            "chose", "selected", "chahiye", "details", "tell me about"
        ]
        
        # ✅ Increased word limit from 6 to 8 for Urdu/English mix
        is_vague = (
            len(query_str.split()) <= 8 or 
            any(word in query_str.lower() for word in trigger_words)
        )

        resolved_query = query_str

        if is_vague and len(self._memory.get()) > 0:
            history_text = "\n".join(
                [f"{msg.role.value}: {msg.content}" for msg in self._memory.get()]
            )
            
            # ✅ SMART REWRITE PROMPT: Extracts exact laptop name
            rewrite_prompt = f"""You are a state-tracking assistant.
Chat History:
{history_text}

User's latest message: '{query_str}'

Task: Identify the EXACT laptop the user is referring to.
- If they say "1st option", "first one", "wo laptop", look at the last list provided and extract the exact Brand and Model name.
- If it's a new search, keep it as is.
- Output ONLY the exact laptop name or new search query. No extra text."""

            try:
                resolved_query = str(self._llm.complete(rewrite_prompt)).strip()
                #print(f"    Memory Recall: '{query_str}' -> '{resolved_query}'")
            except Exception as e:
                logger.warning(f"Query rewrite failed: {e}")

        new_bundle = QueryBundle(query_str=resolved_query)

        # Routing logic
        math_keywords = ["under", "below", "above", "over", "less than", "greater than", "$", "budget", "cheapest", "expensive"]
        needs_math_filtering = any(word in resolved_query.lower() for word in math_keywords)

        if needs_math_filtering:
            nodes = self._broad_retriever.retrieve(new_bundle)
        else:
            # Always use specific vector search for follow-ups to get exact match
            nodes = self._specific_retriever.retrieve(new_bundle)

        return nodes


def create_chat_engine(index_obj, nodes_list):
    print(" Setting up Retrieval Engine...")
    
    vector_store_info = VectorStoreInfo(
        content_info="Laptop specifications and prices",
        metadata_info=[
            MetadataInfo(name="brand", type="str", description="Laptop brand"),
            MetadataInfo(name="price", type="float", description="Price in USD"),
        ],
    )

    try:
        auto_retriever = VectorIndexAutoRetriever(
            index=index_obj,
            vector_store_info=vector_store_info,
            similarity_top_k=15,
        )
    except Exception as e:
        auto_retriever = index_obj.as_retriever(similarity_top_k=15)

    try:
        temp_docstore = SimpleDocumentStore()
        temp_docstore.add_documents(nodes_list)
        bm25_retriever = BM25Retriever.from_defaults(docstore=temp_docstore, similarity_top_k=15)
    except Exception as e:
        bm25_retriever = index_obj.as_retriever(similarity_top_k=15)

    try:
        broad_hybrid_retriever = QueryFusionRetriever(
            retrievers=[auto_retriever, bm25_retriever],
            similarity_top_k=15,
            num_queries=1,
            mode="reciprocal_rerank",
        )
    except Exception as e:
        broad_hybrid_retriever = index_obj.as_retriever(similarity_top_k=15)

    specific_vector_retriever = index_obj.as_retriever(similarity_top_k=5)
    memory = ChatMemoryBuffer.from_defaults(token_limit=1500)

    smart_retriever = SmartRoutingRetriever(
        llm=Settings.llm,
        broad_retriever=broad_hybrid_retriever,
        specific_retriever=specific_vector_retriever,
        memory_buffer=memory,
    )

    cohere_reranker = CohereRerank(
        api_key=Config.COHERE_API_KEY,
        model=Config.COHERE_MODEL,
        top_n=3,
    )

    system_prompt = """You are an expert laptop sales assistant. You handle a 5-step sales flow using ONLY the provided context data. 

GLOBAL RULES:
- NEVER make up information, specs, battery life, or display quality that is not written in the context.
- Prices MUST be whole numbers: $1197 (NOT $1197.00).
- Keep answers short and concise.

PHASE 1: SEARCH (User asks for laptops, e.g., "under 1200")
- List MAXIMUM 3 laptops.
- For budget queries ("under $X"), show highest prices first (closest to budget).
- FORMAT:
**Found Laptops:**
1. [Brand] [Model] - $[Price]
2. [Brand] [Model] - $[Price]
Which one would you like details for?

PHASE 2: DETAILS (User selects a laptop like "1st option", "tell me about it")
- Give the exact CPU, RAM, and Price from the context.
- If user asks "why buy" or "benefits", summarize the given specs positively (e.g., "This i5 processor handles daily tasks smoothly"). Do NOT say "I don't have info".
- FORMAT:
**Details for [Brand] [Model]:**
- CPU: [CPU]
- RAM: [RAM]
- Price: $[Price]

PHASE 3: REJECTION & ALTERNATIVES (User says "no", "don't like", "show another")
- Look at the previous list you provided and suggest the NEXT laptop from that list with its details.
- If no previous list exists, find a new alternative from the context.
- FORMAT:
"No problem! How about this reliable alternative?
**Details for [Brand] [Model]:**
- CPU: [CPU]
- RAM: [RAM]
- Price: $[Price]
Would you like to go with this one?"

PHASE 4: ORDER CONFIRMATION (User says "yes", "done", "order karo", "I'll take it")
- Acknowledge the choice.
- Respond EXACTLY with: "Great choice! To proceed with your order for [Exact Laptop Name], please provide your email or phone number to confirm the order."
- Do NOT invent payment links or delivery dates.

PHASE 5: EXIT (User says "not interested", "nahi lena", "don't want to buy", "bye", "leave it", "nowhere")
- Do NOT try to sell anymore. Do NOT ask for reasons.
- Respond EXACTLY with: "Thank you for your time! Have a great day."
"""

    chat_engine = ContextChatEngine.from_defaults(
        retriever=smart_retriever,
        memory=memory,
        system_prompt=system_prompt,
        node_postprocessors=[cohere_reranker],
        verbose=False,
    )

    print(" Retrieval Engine Ready!\n")
    return chat_engine


if __name__ == "__main__":
    print("⚠️ Run main.py instead")