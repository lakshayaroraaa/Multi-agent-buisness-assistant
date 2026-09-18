"""Chunk sample documents, embed them, and upload a hybrid Azure AI Search index."""
from __future__ import annotations
import hashlib
import os
from pathlib import Path

from azure.ai.projects import AIProjectClient
from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import HnswAlgorithmConfiguration, SearchField, SearchFieldDataType, SearchIndex, SimpleField, VectorSearch, VectorSearchProfile

from shared.agent_base import _project_endpoint_from_connection_string

DOCS_DIR = Path(__file__).resolve().parents[1] / "data" / "sample_docs"

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 75) -> list[str]:
    """Split text by approximate word tokens with overlap for retrieval context."""
    words = text.split()
    if not words:
        return []
    return [" ".join(words[start:start + chunk_size]) for start in range(0, len(words), chunk_size - overlap)]

def build_index(index_name: str, dimensions: int) -> SearchIndex:
    fields = [
        SimpleField(name="id", type=SearchFieldDataType.String, key=True, filterable=True),
        SearchField(name="source_document", type=SearchFieldDataType.String, searchable=True, retrievable=True),
        SearchField(name="chunk_text", type=SearchFieldDataType.String, searchable=True, retrievable=True),
        SearchField(name="content_vector", type=SearchFieldDataType.Collection(SearchFieldDataType.Single), searchable=True, vector_search_dimensions=dimensions, vector_search_profile_name="content-profile"),
    ]
    vectors = VectorSearch(algorithms=[HnswAlgorithmConfiguration(name="hnsw")], profiles=[VectorSearchProfile(name="content-profile", algorithm_configuration_name="hnsw")])
    return SearchIndex(name=index_name, fields=fields, vector_search=vectors)

def main() -> None:
    endpoint, index_name, key = (os.environ["AZURE_SEARCH_ENDPOINT"], os.environ["AZURE_SEARCH_INDEX_NAME"], os.environ["AZURE_SEARCH_API_KEY"])
    deployment = os.environ["AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT"]
    dimensions = int(os.getenv("AZURE_OPENAI_EMBEDDINGS_DIMENSIONS", "1536"))
    credential = AzureKeyCredential(key)
    SearchIndexClient(endpoint, credential).create_or_update_index(build_index(index_name, dimensions))
    project = AIProjectClient(endpoint=_project_endpoint_from_connection_string(os.environ["AZURE_AI_PROJECT_CONNECTION_STRING"]), credential=DefaultAzureCredential())
    openai = project.get_openai_client()
    documents = []
    for path in sorted(DOCS_DIR.glob("*.*")):
        for number, chunk in enumerate(chunk_text(path.read_text(encoding="utf-8"))):
            vector = openai.embeddings.create(model=deployment, input=chunk).data[0].embedding
            identifier = hashlib.sha256(f"{path.name}:{number}".encode()).hexdigest()
            documents.append({"id": identifier, "source_document": path.name, "chunk_text": chunk, "content_vector": vector})
    results = SearchClient(endpoint, index_name, credential).upload_documents(documents)
    failed = [result for result in results if not result.succeeded]
    if failed:
        raise RuntimeError(f"Failed to upload {len(failed)} knowledge chunks.")
    print(f"Uploaded {len(documents)} chunks to {index_name}.")

if __name__ == "__main__":
    main()
