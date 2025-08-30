from transformers import pipeline
from typing import Tuple

_PIPE = None
_MODEL_ID = "distilbert-base-uncased-finetuned-sst-2-english"

def _get_pipe():
    global _PIPE
    if _PIPE is None:
        _PIPE = pipeline("sentiment-analysis", model=_MODEL_ID)
    return _PIPE

def analyze_sentiment(text: str) -> Tuple[str, str]:
    text = text.strip()
    if not text:
        raise ValueError("Cannot analyze empty text")

    out = _get_pipe()(text)
    label = out[0]["label"]  
    return label, _MODEL_ID
