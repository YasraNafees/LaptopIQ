import sys
import re
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
from logger import get_logger

logger = get_logger(__name__)


class SmartRoutingRetriever(BaseRetriever):

    def __init__(self, llm, broad_retriever, specific_retriever, memory_buffer, all_nodes):
        super().__init__()
        self._llm = llm
        self._broad_retriever = broad_retriever
        self._specific_retriever = specific_retriever
        self._memory = memory_buffer
        self._all_nodes = all_nodes  

    def _retrieve(self, query_bundle: QueryBundle) -> List:
        query_str = query_bundle.query_str
        
        
        if "cheapest" in query_str.lower():
            logger.info("CHEAPEST trigger detected. Using Python sort instead of Reranker.")
            valid_nodes = [n for n in self._all_nodes if isinstance(n.metadata.get("price"), (int, float))]
            
            valid_nodes.sort(key=lambda x: x.metadata["price"])
            return valid_nodes[:3] 
            
        if "expensive" in query_str.lower():
            logger.info("EXPENSIVE trigger detected. Using Python sort instead of Reranker.")
            valid_nodes = [n for n in self._all_nodes if isinstance(n.metadata.get("price"), (int, float))]
            
            valid_nodes.sort(key=lambda x: x.metadata["price"], reverse=True)
            return valid_nodes[:3] 


        
        clear_search_keywords = [
            "show", "find", "search", 
            "under", "below", "above", "over", "laptops", "options", "give me"
        ]
        
        is_clear_search = any(word in query_str.lower() for word in clear_search_keywords)
        
        trigger_words = [
            "first", "second", "third", "1st", "2nd", "3rd", 
            "option 1", "option 2", "option 3", "number 1", "number 2",
            "it", "that", "this one", "previous", "the one", 
            "chose", "selected", "details", "tell me about", "more about"
        ]
        
        is_vague = (
            not is_clear_search and 
            (len(query_str.split()) <= 8 or any(word in query_str.lower() for word in trigger_words))
        )

        resolved_query = query_str

        if is_vague and len(self._memory.get()) > 0:
            history_text = "\n".join(
                [f"{msg.role.value}: {msg.content}" for msg in self._memory.get()]
            )
            
            rewrite_prompt = f"""You are a state-tracking assistant.
Chat History:
{history_text}

User's latest message: '{query_str}'

Task: Identify the EXACT laptop the user is referring to OR format budget queries.
- If they say "1st option", "first one", "that one", look at the last list and extract the exact Brand and Model name.
- If they just give a number for budget (e.g., "give me 600", "600"), rewrite it strictly as "Laptops under 600".
- If it's a normal new search, keep it as is.
- Output ONLY the exact laptop name or new search query. No extra text."""

            try:
                resolved_query = str(self._llm.complete(rewrite_prompt)).strip()
                logger.info(f"Memory Recall: '{query_str}' -> '{resolved_query}'")
            except Exception as e:
                logger.warning(f"Query rewrite failed: {e}")

        new_bundle = QueryBundle(query_str=resolved_query)

        math_keywords = ["under", "below", "above", "over", "less than", "greater than", "$", "budget"]
        needs_math_filtering = any(word in resolved_query.lower() for word in math_keywords)

        if needs_math_filtering:
            nodes = self._broad_retriever.retrieve(new_bundle)
        else:
            nodes = self._specific_retriever.retrieve(new_bundle)

        return nodes


def create_chat_engine(index_obj, nodes_list):
    logger.info("Setting up Retrieval Engine...")
    
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
            prompt_template_str="""Extract metadata filters from the user query as a Python boolean expression.
Available fields: 'brand' (str), 'price' (float)

Rules:
- ALWAYS assume a price constraint if ANY number related to money/budget is mentioned, even in a long sentence.
- Never put quotes around numbers.
- Output ONLY the python expression. No explanations.

Examples:
"laptops under 1000" -> price < 1000
"just 200" -> price < 200
"macbook" -> brand == 'Apple' or price > 0
"anything" -> price > 0
"""
        )
        
    except Exception as e:
        logger.error(f"Auto Retriever failed, using default: {e}")
        auto_retriever = index_obj.as_retriever(similarity_top_k=15)

    try:
        temp_docstore = SimpleDocumentStore()
        temp_docstore.add_documents(nodes_list)
        bm25_retriever = BM25Retriever.from_defaults(docstore=temp_docstore, similarity_top_k=15)
    except Exception as e:
        logger.error(f"BM25 Retriever failed, using default: {e}")
        bm25_retriever = index_obj.as_retriever(similarity_top_k=15)

    try:
        broad_hybrid_retriever = QueryFusionRetriever(
            retrievers=[auto_retriever, bm25_retriever],
            similarity_top_k=15,
            num_queries=1,
            mode="reciprocal_rerank",
        )
    except Exception as e:
        logger.error(f"Hybrid Retriever failed, using default: {e}")
        broad_hybrid_retriever = index_obj.as_retriever(similarity_top_k=15)

    specific_vector_retriever = index_obj.as_retriever(similarity_top_k=5)
    memory = ChatMemoryBuffer.from_defaults(token_limit=1500)

    
    smart_retriever = SmartRoutingRetriever(
        llm=Settings.llm,
        broad_retriever=broad_hybrid_retriever,
        specific_retriever=specific_vector_retriever,
        memory_buffer=memory,
        all_nodes=nodes_list 
    )

    cohere_reranker = CohereRerank(
        api_key=Config.COHERE_API_KEY,
        model=Config.COHERE_MODEL,
        top_n=3,
    )

    
    system_prompt = """You are an expert laptop sales assistant. You handle a 5-step sales flow using ONLY the provided context data. 

GLOBAL RULES:
- NEVER make up information, specs, battery life, or display quality that is not written in the context.
- STRICT PRICE FORMAT: Prices MUST be whole integers with NO decimals. E.g., $516 (NEVER $515.9 or $515.90). Round them if necessary.
- Keep answers short and concise. ALWAYS reply in English.
- EMPTY CONTEXT RULE: If the user asks for a specific budget and you are given NO laptop data, reply EXACTLY with: "I apologize, but I do not have any laptops under that budget. Would you like to see the cheapest available laptop I have instead?"
- CRITICAL BUDGET CHECK: If the user specifies a budget limit (e.g., "under 400"), you MUST strictly verify the prices in the provided context. If a laptop's price is equal to or higher than the specified limit, DO NOT include it in your list.

PHASE 1: SEARCH (User asks for laptops)
- List MAXIMUM 3 laptops.
- SUPER CRITICAL RULE: If the user asks for the "cheapest" or "most expensive" laptop, you MUST look at ALL provided context, find the absolute lowest (or highest) price, and show ONLY THAT ONE LAPTOP. Do NOT show a list of 3.
- For specific budget queries ("under $X"), ONLY show laptops that strictly fit the budget.
- For standard budget queries, show highest prices first (closest to budget).
- FORMAT (For standard list):
**Found Laptops:**
1. [Brand] [Model] - $[Price]
2. [Brand] [Model] - $[Price]
Which one would you like details for?

- FORMAT (For Cheapest/Most Expensive):
**Found Laptop:**
[Brand] [Model] - $[Price]
Would you like details for this one?

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

PHASE 4: ORDER CONFIRMATION (User says "yes", "done", "I'll take it")
- Acknowledge the choice.
- Respond EXACTLY with: "Great choice! To proceed with your order for [Exact Laptop Name], please provide your email or phone number to confirm the order."
- Do NOT invent payment links or delivery dates.

PHASE 5: EXIT (User says "not interested", "don't want to buy", "bye", "leave it", "nowhere")
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

    logger.info("Retrieval Engine Ready!")
    return chat_engine


if __name__ == "__main__":
    logger.warning("Please run 'api.py' instead to start the FastAPI server.")