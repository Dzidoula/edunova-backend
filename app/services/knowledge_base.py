import math
import re
from typing import Dict, List, Optional, Tuple


def chunk_text(text: str, max_chars: int = 900, overlap: int = 120) -> List[str]:
    """Découpe un texte en chunks pour la base vectorielle."""
    text = re.sub(r"\s+", " ", (text or "").strip())
    if not text:
        return []
    if len(text) <= max_chars:
        return [text]
    chunks = []
    start = 0
    while start < len(text):
        end = min(len(text), start + max_chars)
        if end < len(text):
            cut = text.rfind(". ", start, end)
            if cut == -1 or cut < start + max_chars // 3:
                cut = text.rfind(" ", start, end)
            if cut > start:
                end = cut + 1
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start = max(end - overlap, start + 1)
        if start >= len(text):
            break
    return chunks


class VectorKnowledgeBase:
    """Base de connaissances locale simple (TF-IDF + cosine), sans dépendance d'embedding."""

    def __init__(self):
        self._vocab: Dict[str, int] = {}
        self._idf: Dict[str, float] = {}
        self._doc_vectors: List[Tuple[str, str, Dict[str, float]]] = []

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        text = (text or "").lower()
        return re.findall(r"[a-zàâäéèêëïîôùûüç0-9]{2,}", text, flags=re.IGNORECASE)

    def build_from_pairs(self, pairs: List[Tuple[str, str]]) -> None:
        self._vocab = {}
        self._idf = {}
        self._doc_vectors = []
        if not pairs:
            return

        tokenized = []
        df: Dict[str, int] = {}
        for doc_id, content in pairs:
            tokens = self._tokenize(content)
            tokenized.append((doc_id, content, tokens))
            for t in set(tokens):
                df[t] = df.get(t, 0) + 1

        for i, term in enumerate(sorted(df.keys())):
            self._vocab[term] = i

        n = max(1, len(tokenized))
        self._idf = {t: math.log((n + 1) / (df[t] + 1)) + 1.0 for t in df}

        for doc_id, content, tokens in tokenized:
            tf: Dict[str, float] = {}
            for t in tokens:
                tf[t] = tf.get(t, 0.0) + 1.0
            length = max(1.0, float(len(tokens)))
            vec = {t: (cnt / length) * self._idf.get(t, 0.0) for t, cnt in tf.items()}
            self._doc_vectors.append((doc_id, content, vec))

    @staticmethod
    def _cosine(a: Dict[str, float], b: Dict[str, float]) -> float:
        if not a or not b:
            return 0.0
        common = set(a) & set(b)
        if not common:
            return 0.0
        dot = sum(a[t] * b[t] for t in common)
        na = math.sqrt(sum(v * v for v in a.values()))
        nb = math.sqrt(sum(v * v for v in b.values()))
        if na == 0 or nb == 0:
            return 0.0
        return dot / (na * nb)

    def search(self, query: str, top_k: int = 4, document_id: Optional[str] = None) -> List[str]:
        if not self._doc_vectors or not query.strip():
            return []
        q_tokens = self._tokenize(query)
        tf: Dict[str, float] = {}
        for t in q_tokens:
            tf[t] = tf.get(t, 0.0) + 1.0
        length = max(1.0, float(len(q_tokens)))
        q_vec = {t: (cnt / length) * self._idf.get(t, 0.0) for t, cnt in tf.items()}

        scored = []
        for doc_id, content, vec in self._doc_vectors:
            if document_id and doc_id != document_id:
                continue
            scored.append((self._cosine(q_vec, vec), content))
        scored.sort(key=lambda x: x[0], reverse=True)
        results = []
        for score, content in scored[:top_k]:
            if score > 0.01:
                results.append(content)
        return results
