import openai
import numpy as np
import pandas as pd
import os
from dotenv import load_dotenv
from openai import OpenAI  # Using the new OpenAI API client

load_dotenv()

def extract_keywords(query, api_key):
    client = OpenAI(api_key=api_key)  # New syntax

    prompt = f"""Please extract the most essential search keyword from the following Chinese question:

1. If the question is **"How do you say X in Jino?"**, you should return only **"X"**, not "Jino".
2. Return only one most relevant keyword.
3. Do not return a sentence or any explanation, only the keyword.

Question: {query}
Keyword:"""

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=5
    )
    keyword = response.choices[0].message.content.strip()
    print(f"Extracted keyword: {keyword}")
    return keyword


def semantic_search(query, df, index, model, top_k=5):
    print(f"Performing semantic search for: {query}")
    query_embedding = model.encode(query, normalize_embeddings=True).reshape(1, -1)
    _, indices = index.search(query_embedding, top_k)
    valid_indices = [i for i in indices[0] if i < len(df)]
    return df.iloc[valid_indices]["text"].tolist()


def process_results(df, text_results):
    file_results = df[["text", "file"]].dropna().drop_duplicates()
    text_to_files = file_results.groupby("text")["file"].apply(list).to_dict()

    output = {}
    for text in text_results:
        files = text_to_files.get(text, [])
        output[text] = {
            "images": [f for f in files if f.endswith((".jpg", ".png", ".webp"))] or ["No image available"],
            "audios": [f for f in files if f.endswith((".mp3", ".wav", ".ogg"))] or ["No audio available"],
        }
    return output


if __name__ == "__main__":
    import pickle
    import faiss
    from sentence_transformers import SentenceTransformer

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in .env file")

    df = pd.read_json("data/jino_all_media.json", encoding="utf-8")
    index = faiss.read_index("data/faiss_index.bin")
    model = SentenceTransformer("moka-ai/m3e-base")

    query = "基诺语的火怎么说？"
    keyword = extract_keywords(query, api_key)
    results = semantic_search(keyword, df, index, model)
    final = process_results(df, results)

    print("\nSearch Results:")
    for k, v in final.items():
        print(f"\nText: {k}")
        print(f"Images: {v['images']}")
        print(f"Audios: {v['audios']}")
