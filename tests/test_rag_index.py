"""tests/test_rag_index.py - Tests for Azure AI Search product-chunks index.

Checks:
1. Index exists.
2. Field schema matches specification (names, types, attributes).
3. Vector configuration has 1536 dimensions and HNSW algorithm.
4. Total document count matches chunks.jsonl (289).

Skipped if Azure Search credentials are not configured.
"""

import os
import pytest
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import ResourceNotFoundError
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents import SearchClient
from backend.config import settings

pytestmark = pytest.mark.skipif(
    not settings.AZURE_SEARCH_ENDPOINT or not settings.AZURE_SEARCH_KEY,
    reason="Azure Search credentials not configured",
)


@pytest.fixture(scope="module")
def index_client():
    return SearchIndexClient(
        endpoint=settings.AZURE_SEARCH_ENDPOINT,
        credential=AzureKeyCredential(settings.AZURE_SEARCH_KEY),
    )


@pytest.fixture(scope="module")
def search_client():
    index_name = settings.AZURE_SEARCH_CHUNKS_INDEX or "product-chunks"
    return SearchClient(
        endpoint=settings.AZURE_SEARCH_ENDPOINT,
        index_name=index_name,
        credential=AzureKeyCredential(settings.AZURE_SEARCH_KEY),
    )


def test_index_exists(index_client):
    """Ensure the product-chunks index exists in Azure AI Search."""
    index_name = settings.AZURE_SEARCH_CHUNKS_INDEX or "product-chunks"
    index = index_client.get_index(index_name)
    assert index is not None
    assert index.name == index_name


def test_index_schema_fields(index_client):
    """Verify all required fields, their data types, and attributes."""
    index = index_client.get_index(settings.AZURE_SEARCH_CHUNKS_INDEX or "product-chunks")
    field_map = {f.name: f for f in index.fields}

    # Required fields
    expected_fields = [
        "chunk_id",
        "product_id",
        "product_name",
        "category",
        "section",
        "title",
        "content",
        "content_vector",
        "token_count",
        "is_synthetic",
    ]

    for field_name in expected_fields:
        assert field_name in field_map, f"Field '{field_name}' missing from index schema"

    # Specific field properties
    assert field_map["chunk_id"].key is True

    assert field_map["product_id"].filterable is True
    assert field_map["product_name"].searchable is True

    assert field_map["category"].filterable is True
    assert field_map["category"].facetable is True

    assert field_map["section"].filterable is True
    assert field_map["title"].searchable is True
    assert field_map["content"].searchable is True

    assert field_map["token_count"].type == "Edm.Int32"
    assert field_map["is_synthetic"].filterable is True
    assert field_map["is_synthetic"].type == "Edm.Boolean"

    # Vector field properties
    vector_field = field_map["content_vector"]
    assert vector_field.vector_search_dimensions == 1536
    assert vector_field.vector_search_profile_name is not None


def test_vector_search_config(index_client):
    """Verify vector search configuration uses HNSW with cosine metric."""
    index = index_client.get_index(settings.AZURE_SEARCH_CHUNKS_INDEX or "product-chunks")
    assert index.vector_search is not None
    assert len(index.vector_search.profiles) > 0
    assert len(index.vector_search.algorithms) > 0

    hnsw_algo = next(
        (a for a in index.vector_search.algorithms if a.name == "chunk-hnsw-config"),
        None,
    )
    assert hnsw_algo is not None, "HNSW algorithm config 'chunk-hnsw-config' not found"
    assert hnsw_algo.parameters is not None
    assert hnsw_algo.parameters.metric.lower() == "cosine"


def test_document_count(search_client):
    """Verify that document count in index equals 289 (number of chunks in chunks.jsonl)."""
    doc_count = search_client.get_document_count()
    assert doc_count == 289, f"Expected 289 indexed documents, found {doc_count}"
