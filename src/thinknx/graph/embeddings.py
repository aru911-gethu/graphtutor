from typing import List, Dict, Any, Optional
import numpy as np
import networkx as nx

from thinknx.config import settings


class EmbeddingIndex:
    """Vector search index for concept discovery, semantic routing, and similarity."""

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or settings.hf_embedding_model
        self._model = None
        self.node_keys: List[str] = []
        self.embeddings: Optional[np.ndarray] = None

    @property
    def model(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name)
            except Exception:
                self._model = None
        return self._model

    def build_index(self, G: nx.MultiDiGraph) -> int:
        """Build embedding matrix from NetworkX graph nodes."""
        self.node_keys = []
        texts = []

        for node_id, data in G.nodes(data=True):
            name = data.get("name", node_id)
            desc = data.get("description", "")
            category = data.get("domain", data.get("category", ""))
            full_text = f"{name}. {category}. {desc}".strip()

            self.node_keys.append(node_id)
            texts.append(full_text)

        if not texts:
            self.embeddings = None
            return 0

        if self.model:
            raw_vectors = self.model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
            self.embeddings = raw_vectors
        else:
            # Deterministic pseudo-embedding for fallback/testing
            np.random.seed(42)
            self.embeddings = np.random.randn(len(texts), 384)
            norms = np.linalg.norm(self.embeddings, axis=1, keepdims=True)
            self.embeddings = self.embeddings / np.maximum(norms, 1e-9)

        return len(self.node_keys)

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Find concepts semantically closest to search text."""
        if self.embeddings is None or len(self.node_keys) == 0:
            return []

        if self.model:
            query_vec = self.model.encode([query], convert_to_numpy=True, normalize_embeddings=True)[0]
        else:
            np.random.seed(abs(hash(query)) % 10000)
            query_vec = np.random.randn(384)
            query_vec = query_vec / np.linalg.norm(query_vec)

        similarities = np.dot(self.embeddings, query_vec)
        top_indices = np.argsort(similarities)[::-1][:top_k]

        results = []
        for idx in top_indices:
            score = float(similarities[idx])
            results.append({
                "key": self.node_keys[idx],
                "score": round(score, 4),
            })
        return results
