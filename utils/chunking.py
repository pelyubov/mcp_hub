import re


def recursive_chunking(text : str, max_chunk_size: int, overlap_sentences : int) -> list[str]:
    if not text:
        return []
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    if text and not re.search(r'[.!?]\s*$', text):
        sentences = sentences[:-1] + [sentences[-1] + '.']
    chunks = []
    current_chunk = ""
    current_sentences = []
    for sentence in sentences:
        if len(current_chunk) + len(sentence) > max_chunk_size and current_chunk:
            chunks.append(current_chunk)
            overlap_sentences_count = min(overlap_sentences, len(current_sentences))
            overlap_sentences_list = current_sentences[-overlap_sentences_count:]
            overlap_text = "".join(overlap_sentences_list) if not any(s.endswith(" ") for s in overlap_sentences_list) else " ".join(overlap_sentences_list)
            current_chunk = overlap_text
            current_sentences = current_sentences[-overlap_sentences_count:]
        current_chunk += (" " if current_chunk and not current_chunk.endswith(" ") and not sentence.startswith(" ") else "") + sentence
        current_sentences.append(sentence)
    if current_chunk:
        chunks.append(current_chunk)

    return chunks