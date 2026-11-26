from qdrant_client import models

from src.utils import get_qdrant_client

COLLECTION_NAME = "tags"

client = get_qdrant_client()

def search_variables(query_str: str, top_k: int) -> list[str]: 
    res = client.query_points_groups(
        collection_name=COLLECTION_NAME,
        query=models.Document(
            text=query_str,
            model="sentence-transformers/all-minilm-l6-v2"
        ),
        group_by="variable_id",
        group_size=3,
        limit=top_k
    )

    variable_ids = []

    for group in res.groups:
        hit = group.hits[0]
        variable_ids.append(hit.payload["variable_id"])

    return variable_ids


if __name__ == "__main__":
    print(search_variables("population", 10))
