from rag.vector_store import search_chroma

def retrieve_documents(query: str):
    return search_chroma(query)
