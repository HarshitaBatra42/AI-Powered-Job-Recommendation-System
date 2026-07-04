import builtins
import importlib
import sys


def test_recommender_imports_when_optional_ml_deps_are_missing(monkeypatch):
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name.startswith("sentence_transformers") or name.startswith("sklearn"):
            raise ImportError("simulated missing dependency")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    sys.modules.pop("recommender", None)

    module = importlib.import_module("recommender")

    assert hasattr(module, "recommend_jobs")
    assert module.embedding_model is None
