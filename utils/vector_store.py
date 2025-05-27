import uuid

from qdrant_client import QdrantClient
from qdrant_client.http.models import (Distance, FieldCondition, Filter,
                                       FilterSelector, PointStruct, Range,
                                       VectorParams)
from sentence_transformers import SentenceTransformer

# from utils.get_config import load_config
# 
# config = load_config()

# embed_model = SentenceTransformer(config.embedding_model_path)
embed_model = SentenceTransformer("D:/code/RAG/RAG-lung-disease/model/halong_embedding")

qdrant_client = QdrantClient(host="localhost", port=6333)

COLLECTION_NAME = "vector_store"

# max_length = model.tokenizer.model_max_length
VECTOR_SIZE = embed_model.get_sentence_embedding_dimension()
# print(f"limited token: {max_length}")
# print(f"vector size: {VECTOR_SIZE}")

try:
    qdrant_client.get_collection(collection_name=COLLECTION_NAME)
    print(f"Collection '{COLLECTION_NAME}' already exists")
except Exception:
    qdrant_client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(
            size=VECTOR_SIZE,
            distance=Distance.COSINE
        )
    )
    print(f"Created collection '{COLLECTION_NAME}'")



#knowledge base
def add_text_to_qdrant(text, title, source, client=qdrant_client, collection_name=COLLECTION_NAME):
    try:
        embedding = embed_model.encode(text)
        point_id = str(uuid.uuid4())
        client.upsert(
            collection_name=collection_name,
            points=[
                PointStruct(
                    id=point_id,
                    vector=embedding.tolist(),
                    payload={
                        "text": text,
                        "title": title,
                        "source": source
                    }
                )
            ]
        )
        return point_id
    except Exception as e:
        print(f"Error in add_text_to_qdrant: {e}")
        return None


def search_similar_texts(query_text: str, limit: int, client=qdrant_client, collection_name=COLLECTION_NAME, threshold=0.5):
    try:
        query_embedding = embed_model.encode(query_text)
        search_results = client.search(
            collection_name=collection_name,
            query_vector=query_embedding.tolist(),
            limit=limit
        )
        results = []
        for result in search_results:
            if result.score > threshold:
                results.append({
                    "text": result.payload["text"],
                    "title": result.payload["title"],
                    "source": result.payload["source"],
                    "score": result.score,
                    "id": result.id
                })
        return results
    except Exception as e:
        print(f"Error in search_similar_texts: {e}")
        return []


def delete_collection(client=qdrant_client, collection_name=COLLECTION_NAME):
    try:
        client.delete_collection(collection_name=collection_name)
        print(f"Collection '{collection_name}' deleted")
    except Exception as e:
        print(f"Error in delete_collection: {e}")


def delete_data_in_collection(collection_name=COLLECTION_NAME, client=qdrant_client):
    try:
        client.delete(
            collection_name=collection_name,
            points_selector=FilterSelector(
                filter=Filter(
                    must=[
                        FieldCondition(
                            key="text",
                            range=Range(gte="0")
                        )
                    ]
                )
            )
        )
        print(f"Data in collection '{collection_name}' deleted")
    except Exception as e:
        print(f"Error in delete_data_in_collection: {e}")