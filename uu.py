from config import Config
from llama_index.llms.openrouter import OpenRouter

llm = OpenRouter(
    model=Config.LLM_MODEL,
    api_key=Config.OPENROUTER_API_KEY,
    api_base=Config.OPENROUTER_API_URL,
)

response = llm.stream_complete("Write a detailed 200 word essay about why laptops are expensive")

count = 0
for chunk in response:
    count += 1
    print(f"CHUNK #{count}: {repr(chunk.delta)}")

print(f"TOTAL CHUNKS: {count}")