from app.services.knowledge_base import VectorKnowledgeBase, chunk_text


def test_search_ranks_relevant_chunk_first():
    kb = VectorKnowledgeBase()
    kb.build_from_pairs([
        ("doc-1", "La photosynthèse transforme la lumière en énergie chimique dans les plantes."),
        ("doc-1", "Le théorème de Pythagore relie les côtés d'un triangle rectangle."),
    ])
    results = kb.search("Comment les plantes utilisent la lumière ?", top_k=1)
    assert results
    assert "photosynthèse" in results[0]


def test_search_filters_by_document_id():
    kb = VectorKnowledgeBase()
    kb.build_from_pairs([
        ("doc-1", "Les fractions représentent une division entre deux nombres."),
        ("doc-2", "Les fractions apparaissent aussi en musique et en cuisine."),
    ])
    results = kb.search("fractions", top_k=5, document_id="doc-2")
    assert results == ["Les fractions apparaissent aussi en musique et en cuisine."]


def test_chunk_text_splits_long_text_with_overlap():
    text = "Phrase. " * 300
    chunks = chunk_text(text, max_chars=200, overlap=20)
    assert len(chunks) > 1
    assert all(len(c) <= 220 for c in chunks)
