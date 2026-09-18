from shared.schemas import KnowledgeSearchOutput
from tools.knowledge_tools import search_knowledge_base


def test_matching_query_returns_source_citations() -> None:
    result = search_knowledge_base("What is the remote work policy?")
    assert isinstance(result, KnowledgeSearchOutput)
    assert result.results
    assert any(item.source_document == "remote_work_policy.md" for item in result.results)


def test_no_match_is_graceful() -> None:
    result = search_knowledge_base("quantum entanglement horticulture")
    assert result.results == []
