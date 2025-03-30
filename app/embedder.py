import os
import json
import pickle
import numpy as np
import pandas as pd
import faiss
from sentence_transformers import SentenceTransformer

def load_and_embed(json_path, embedding_path, index_path, model_name="moka-ai/m3e-base"):
    """
    从 JSON 文件加载文本，生成嵌入向量并建立 FAISS 索引。
    如果已存在嵌入和索引文件，则直接加载。
    返回：df, index, model
    """
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"❌ 未找到 JSON 文件：{json_path}")

    with open(json_path, "r", encoding="utf-8") as f:
        media_entries = json.load(f)

    df = pd.DataFrame(media_entries)
    df["text"] = df["text"].fillna("")
    df["enhanced_text"] = df["text"].apply(lambda x: f"{x} {x.lower()}")

    model = SentenceTransformer(model_name)

    if os.path.exists(index_path) and os.path.exists(embedding_path):
        print("✅ 加载已有的 FAISS 索引和嵌入")
        index = faiss.read_index(index_path)
        with open(embedding_path, "rb") as f:
            embeddings = pickle.load(f)
    else:
        print("⚙️ 生成新的嵌入并创建索引...")
        df["embedding"] = df["enhanced_text"].apply(
            lambda x: model.encode(x, normalize_embeddings=True) if isinstance(x, str) and x.strip() else np.zeros(768)
        )
        embeddings = np.vstack(df["embedding"].values).astype(np.float32)

        index = faiss.IndexFlatL2(embeddings.shape[1])
        index.add(embeddings)

        # 保存文件
        faiss.write_index(index, index_path)
        with open(embedding_path, "wb") as f:
            pickle.dump(embeddings, f)

        print("✅ 嵌入和索引保存完成")

    return df, index, model

# ✅ 脚本独立运行入口
if __name__ == "__main__":
    df, index, model = load_and_embed(
        json_path="data/jino_all_media.json",
        embedding_path="data/text_embeddings.pkl",
        index_path="data/faiss_index.bin"
    )
    print(f"✅ 嵌入完成，共处理 {len(df)} 条数据")
