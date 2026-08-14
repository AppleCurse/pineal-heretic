from backend.api import get_room

room = get_room("test_client")
executor = room["executor"]
vault = room["vault"]

print(f"Vault Data: {vault}")
print(f"LLM Gateway Key: {executor.llm_gateway.api_key}")
print(f"Search Engine Tavily: {executor.search_engine.tavily_key}")
print(f"Search Engine SerpAPI: {executor.search_engine.serpapi_key}")
print(f"Search Engine Exa: {executor.search_engine.exa_key}")
