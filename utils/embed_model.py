from sentence_transformers import SentenceTransformer

VI_EMDED_MODEL = "hiieu/halong_embedding"


class EmbedModel(SentenceTransformer):
    def __init__(self, model_name: str = VI_EMDED_MODEL) -> None:
        super().__init__(model_name)

    def retrieve_similarity_measure(self, text1: str, text2: str) -> float:
        embedding1 = self.encode(text1)
        embedding2 = self.encode(text2)
        return float(self.similarity(embedding1, embedding2))
