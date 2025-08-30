from transformers import pipeline
from typing import Tuple

_PIPE = None
_MODEL_ID = "sshleifer/distilbart-cnn-12-6"

def _get_pipe():
    global _PIPE
    if _PIPE is None:
        _PIPE = pipeline("summarization", model=_MODEL_ID)
    return _PIPE

def summarize_text(text: str) -> Tuple[str, str]:
   
    if not isinstance(text, str):
        raise ValueError("Text must be str")
    text = text.strip()
    if not text:
        raise ValueError("Cannot summarize empty text")

    text = text[:4000]

    if len(text) < 500:
        gen_kwargs = dict(max_length=80, min_length=30, do_sample=False)
    else:
        gen_kwargs = dict(max_length=130, min_length=30, do_sample=False)

    pipe = _get_pipe()
    out = pipe(text, **gen_kwargs)
  
    summary = out[0]["summary_text"].strip()
    return summary, _MODEL_ID


