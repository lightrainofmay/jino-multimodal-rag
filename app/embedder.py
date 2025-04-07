# -*- coding: utf-8 -*-
import os
import json
import pickle
import numpy as np
import pandas as pd
import faiss
from sentence_transformers import SentenceTransformer

DEFAULT_MODEL = "moka-ai/m3e-base"

def load_and_embed(json_path, embedding_path, index_path, model_name=DEFAULT_MODEL):
    """
    Load text from a JSON file, generate embeddings, and build a FAISS index.
    If embedding and index files already exist, load them directly.
    Returns: df, index, model
    """
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"JSON file not found: {json_path}")

    with open(json_path, "r", encoding="utf-8") as f:
        media_entries = json.load(f)

    df = pd.DataFrame(media_entries)
    df["text"] = df["text"].fillna("")
    df["enhanced_text"] = df["text"].apply(lambda x: f"{x} {x.lower()}")

    model = SentenceTransformer(model_name)

    if os.path.exists(index_path) and os.path.exists(embedding_path):
        print("Loading existing FAISS index and embeddings...")
        index = faiss.read_index(index_path)
        with open(embedding_path, "rb") as f:
            embeddings = pickle.load(f)
    else:
        print("Generating new embeddings and creating FAISS index...")
        df["embedding"] = df["enhanced_text"].apply(
            lambda x: model.encode(x, normalize_embeddings=True) if isinstance(x, str) and x.strip() else np.zeros(768)
        )
        embeddings = np.vstack(df["embedding"].values).astype(np.float32)

        index = faiss.IndexFlatL2(embeddings.shape[1])
        index.add(embeddings)

        # Save index and embeddings
        faiss.write_index(index, index_path)
        with open(embedding_path, "wb") as f:
            pickle.dump(embeddings, f)

        print("Embeddings and index saved.")

    return df, index, model


def create_embeddings_and_index(json_path, embedding_path, index_path, model_name=DEFAULT_MODEL):
    """
    Force regeneration of embeddings and index (used by /refresh endpoint).
    """
    print("Regenerating embeddings and index...")

    if not os.path.exists(json_path):
        raise FileNotFoundError(f"JSON file not found: {json_path}")

    with open(json_path, "r", encoding="utf-8") as f:
        media_entries = json.load(f)

    df = pd.DataFrame(media_entries)
    df["text"] = df["text"].fillna("")
    df["enhanced_text"] = df["text"].apply(lambda x: f"{x} {x.lower()}")

    model = SentenceTransformer(model_name)
    df["embedding"] = df["enhanced_text"].apply(
        lambda x: model.encode(x, normalize_embeddings=True) if isinstance(x, str) and x.strip() else np.zeros(768)
    )
    embeddings = np.vstack(df["embedding"].values).astype(np.float32)

    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)

    with open(embedding_path, "wb") as f:
        pickle.dump(embeddings, f)
    faiss.write_index(index, index_path)

    print("Embeddings and index created successfully.")
    return df, index, model


# CLI testing entry point
if __name__ == "__main__":
    df, index, model = load_and_embed(
        json_path="data/jino_all_media.json",
        embedding_path="data/text_embeddings.pkl",
        index_path="data/faiss_index.bin"
    )
    print(f"Embedding completed. Total entries processed: {len(df)}")
