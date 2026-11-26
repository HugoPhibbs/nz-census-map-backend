from sentence_transformers import SentenceTransformer
import pandas as pd
import anthropic
from tqdm import tqdm
from dotenv import load_dotenv
from pydantic import BaseModel


load_dotenv()  # For Anthropic API key

def generate_all_tags(vars_df: pd.DataFrame, ai_client: anthropic.Anthropic) -> dict[str, list[str]]:

    class VariableTags(BaseModel):
        tags: list[str]

    def generate_tags(row_dict) -> str:
        response = ai_client.messages.parse(
            model="claude-haiku-5-5",
            max_tokens=4096,
            output_config={"effort": "medium"},
            output_format=VariableTags,
            system="""
                    You're given database row from a census variable database. 
                    
                    Each row has four keys, values: variable_id, variable_unit, plain_name and description
                    
                    Your job is to generate a list of 3-10 string tags related to this variable to support semantic looking up of this variable among dozens of others in a census database
                
                    Keep tags relevant, and don't include several tags, when a few will do

                    Do not create generic / low information tags such as "census", "demographic", "statistic" or "population", as these describe basically every variable

                    Tags must be "atomic" in the sense that adding more or less information would change the meaning. They can contain hyphens, e.g. "latin-american"

                    E.g: row: "variable_id: pop_resident_usual, variable_unit: COUNT, plain_name: Usually Resident Population, description: The total number of people who usually live in the area, according to the census."
                         => "resident,inhabitants,populace"
                    """,
            messages=[{"role": "user", "content": str(row_dict)}],
        )

        output = response.parsed_output

        if output is None:
            raise ValueError(f"Could not generate tags for the row: {row_dict}")
        
        return output.tags

    all_tags = dict()

    for row in tqdm(vars_df.itertuples(index=False), "Generating tags"):
        row_dict = row._asdict()
        tags = generate_tags(row_dict)

        all_tags[row_dict["variable_id"]] = tags

    return all_tags


def embed_tag(tag: str, embedding_model: SentenceTransformer):
    return embedding_model.encode([tag])[0]

def embed_all_tags(tags: dict[str, list[str]], embedding_model: SentenceTransformer):
    all_embeddings = []

    for var_id, tags in tqdm(tags.items(), "Embedding tags"):
        for tag in tags:
            embedding = embed_tag(tag, embedding_model)

            all_embeddings.append({
                "variable_id": var_id,
                "tag": tag,
                "embedding": embedding
            })

    return all_embeddings

if __name__ == "__main__":
    # tags_df = pd.read_parquet("./data/tags/tags.parquet")

    # print(tags_df[tags_df["variable_id"] == "pop_resident_usual"]["tags"])

    embedding_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

    vars_df = pd.read_parquet(r"data/db-tables/demographic_variables_table.parquet")
    ai_client = anthropic.Anthropic()

    tags = generate_all_tags(vars_df, ai_client) 

    all_embeddings = embed_all_tags(tags, embedding_model)

    embeddings_df = pd.DataFrame(all_embeddings)
    tags_df = pd.DataFrame(tags.items(), columns=["variable_id", "tags"])

    tags_df.to_parquet("./data/tags/tags.parquet")
    embeddings_df.to_parquet("./data/tags/embeddings.parquet", engine="pyarrow") # pyarrow supports cells containing arrays