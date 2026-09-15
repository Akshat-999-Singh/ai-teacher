"""sklearn transformer wrapping a sentence-transformers model.

Lives in its own module (not in train_classifier.py's __main__) so a pickled
pipeline can be unpickled by any process that has tools/ on sys.path.
"""
from pathlib import Path

from sklearn.base import BaseEstimator, TransformerMixin

# Model weights stay on D: with the project, never the default C: HF cache.
HF_CACHE = Path(__file__).resolve().parent.parent / ".cache" / "huggingface" / "hub"

_MODELS = {}


def _load(model_name):
    if model_name not in _MODELS:
        from sentence_transformers import SentenceTransformer
        _MODELS[model_name] = SentenceTransformer(model_name, cache_folder=str(HF_CACHE))
    return _MODELS[model_name]


class SentenceEmbedder(BaseEstimator, TransformerMixin):
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        self.model_name = model_name

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        return _load(self.model_name).encode(list(X), show_progress_bar=False)
