"""Azure AI Search RAG retrieval tool with a credential-free sample fallback."""
from __future__ import annotations
import os
import re
from pathlib import Path
from shared.agent_base import _project_endpoint_from_connection_string, agent_tool
from shared.schemas import KnowledgeChunk, KnowledgeSearchInput, KnowledgeSearchOutput

SAMPLE_DOCS = Path(__file__).resolve().parents[1] / "data" / "sample_docs"

def _local_sample_search(query: str, top_k: int) -> list[KnowledgeChunk]:
    """Development-only fallback; production retrieval is Azure AI Search."""
    terms = set(re.findall(r"[a-z]{3,}", query.casefold()))
    results = []
    for path in SAMPLE_DOCS.glob("*.*"):
        text = path.read_text(encoding="utf-8")
        overlap = len(terms & set(re.findall(r"[a-z]{3,}", text.casefold())))
        if overlap:
            results.append(KnowledgeChunk(source_document=path.name, chunk_text=text, relevance_score=overlap / len(terms)))
    return sorted(results, key=lambda result: result.relevance_score, reverse=True)[:top_k]

def _azure_hybrid_search(query: str, top_k: int) -> list[KnowledgeChunk]:
    """Integration seam for Azure OpenAI embeddings plus Azure AI Search hybrid search."""
    from azure.ai.projects import AIProjectClient
    from azure.core.credentials import AzureKeyCredential
    from azure.identity import DefaultAzureCredential
    from azure.search.documents import SearchClient
    from azure.search.documents.models import VectorizedQuery
    project = AIProjectClient(endpoint=_project_endpoint_from_connection_string(os.environ["AZURE_AI_PROJECT_CONNECTION_STRING"]), credential=DefaultAzureCredential())
    vector = project.get_openai_client().embeddings.create(model=os.environ["AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT"], input=query).data[0].embedding
    client = SearchClient(os.environ["AZURE_SEARCH_ENDPOINT"], os.environ["AZURE_SEARCH_INDEX_NAME"], AzureKeyCredential(os.environ["AZURE_SEARCH_API_KEY"]))
    response = client.search(search_text=query, vector_queries=[VectorizedQuery(vector=vector, k_nearest_neighbors=top_k, fields="content_vector")], select=["source_document", "chunk_text"], top=top_k)
    return [KnowledgeChunk(source_document=item["source_document"], chunk_text=item["chunk_text"], relevance_score=float(item.get("@search.score", 0))) for item in response]

@agent_tool
def search_knowledge_base(query: str, top_k: int = 5) -> KnowledgeSearchOutput:
    """Retrieve cited chunks with Azure AI Search hybrid keyword/vector retrieval."""
    request = KnowledgeSearchInput(query=query, top_k=top_k)
    required = ("AZURE_SEARCH_ENDPOINT", "AZURE_SEARCH_INDEX_NAME", "AZURE_SEARCH_API_KEY", "AZURE_AI_PROJECT_CONNECTION_STRING", "AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT")
    if all(os.getenv(name) for name in required):
        return KnowledgeSearchOutput(query=request.query, results=_azure_hybrid_search(request.query, request.top_k), source_system="Azure AI Search")
    return KnowledgeSearchOutput(query=request.query, results=_local_sample_search(request.query, request.top_k), source_system="Local sample-document fallback")
