# def recursive_chunking(text : str, max_chunk_size: int, overlap_sentences : int) -> list[str]:
#     if not text:
#         return []
#     sentences = re.split(r'(?<=[.!?])\s+', text.strip())
#     if text and not re.search(r'[.!?]\s*$', text):
#         sentences = sentences[:-1] + [sentences[-1] + '.']
#     chunks = []
#     current_chunk = ""
#     current_sentences = []
#     for sentence in sentences:
#         if len(current_chunk) + len(sentence) > max_chunk_size and current_chunk:
#             chunks.append(current_chunk)
#             overlap_sentences_count = min(overlap_sentences, len(current_sentences))
#             overlap_sentences_list = current_sentences[-overlap_sentences_count:]
#             overlap_text = "".join(overlap_sentences_list) if not any(s.endswith(" ") for s in overlap_sentences_list) else " ".join(overlap_sentences_list)
#             current_chunk = overlap_text
#             current_sentences = current_sentences[-overlap_sentences_count:]
#         current_chunk += (" " if current_chunk and not current_chunk.endswith(" ") and not sentence.startswith(" ") else "") + sentence
#         current_sentences.append(sentence)
#     if current_chunk:
#         chunks.append(current_chunk)

#     return chunks


def recursive_chunking(
        text: str, max_chunk_size: int = 100, overlap_sentences: int = 20
    ) -> list[str]:
        assert max_chunk_size > overlap_sentences, "max_words must be greater than overlap"
        words = text.split()
        W = len(words)
        if W <= max_chunk_size * 1.3:
            return [text]
        assert W > overlap_sentences, "text must have more words than overlap"
        step = max_chunk_size - overlap_sentences
        chunking_text = [
            words[max(i - overlap_sentences, 0) : min(i + step, W)]
            for i in range(0, W, step)
        ]
        if (len(chunking_text) > 1) and (
            len(chunking_text[-1])
            <= max_chunk_size * 0.3
        ):
            chunking_text[-2] = (
                chunking_text[-2][-(max_chunk_size - overlap_sentences) :] + chunking_text[-1]
            )
            chunking_text.pop()
        return [" ".join(chunk) for chunk in chunking_text]