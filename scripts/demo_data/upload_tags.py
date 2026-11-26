from qdrant_client import QdrantClient
from dotenv import load_dotenv
import os
import pandas as pd
from qdrant_client.models import PayloadSchemaType, PointStruct, VectorParams, Distance

load_dotenv()

COLLECTION_NAME = "tags"

client = QdrantClient(
    url=os.environ["QDRANT_ENDPOINT"],
    api_key=os.environ["QDRANT_API_KEY"],
    cloud_inference=True,
)

client.create_collection(
    COLLECTION_NAME,
    vectors_config=VectorParams(size=384, distance=Distance.COSINE),
)

client.create_payload_index(COLLECTION_NAME, "variable_id", PayloadSchemaType.KEYWORD)

embedding_df = pd.read_parquet(r"data/tags/embeddings.parquet")

points = []

for i, row in enumerate(embedding_df.itertuples(index=False)):
    row_dict = row._asdict()

    points.append(
        PointStruct(
            id = i,
            payload={"variable_id": row_dict["variable_id"], "tag": row_dict["tag"]},
            vector=row_dict["embedding"].tolist()
        )
    )

client.upsert(collection_name=COLLECTION_NAME, points=points)