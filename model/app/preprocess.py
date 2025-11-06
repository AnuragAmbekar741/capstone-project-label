from .models import Thread

THREAD_SEP = " ||| "

def thread_to_source(thread: Thread) -> str:
    # Join messages chronologically into EmailSum-style source
    parts = [m.text.strip() for m in thread.messages if m.text and m.text.strip()]
    return THREAD_SEP.join(parts)
