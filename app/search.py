import openai
import numpy as np
import pandas as pd
import os
from dotenv import load_dotenv
from openai import OpenAI  # ✅ 使用新版 API 客户端

load_dotenv()

def extract_keywords(query, api_key):
    client = OpenAI(api_key=api_key)  # ✅ 新写法

    prompt = f"""请从下面的中文问题中提取最核心的搜索关键词：

1. 如果问题是 **"基诺语的X怎么说？"**，你应该只返回 **"X"**，不要返回 "基诺语"。
2. 仅返回一个最相关的关键词。
3. 不要返回句子或多余的解释，只返回关键词。

问题：{query}
关键词："""

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=5
    )
    keyword = response.choices[0].message.content.strip()
    print(f"📝 提取关键词：{keyword}")
    return keyword


def semantic_search(query, df, index, model, top_k=5):
    print(f"🔍 正在搜索：{query}")
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
            "images": [f for f in files if f.endswith((".jpg", ".png", ".webp"))] or ["暂无图片"],
            "audios": [f for f in files if f.endswith((".mp3", ".wav", ".ogg"))] or ["暂无音频"],
        }
    return output


if __name__ == "__main__":
    import pickle
    import faiss
    from sentence_transformers import SentenceTransformer

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("❌ 未在 .env 中找到 OPENAI_API_KEY")

    df = pd.read_json("data/jino_all_media.json", encoding="utf-8")
    index = faiss.read_index("data/faiss_index.bin")
    model = SentenceTransformer("moka-ai/m3e-base")

    query = "基诺语的火怎么说？"
    keyword = extract_keywords(query, api_key)
    results = semantic_search(keyword, df, index, model)
    final = process_results(df, results)

    print("\n🔎 检索结果：")
    for k, v in final.items():
        print(f"\n📝 文本：{k}")
        print(f"🖼️ 图片：{v['images']}")
        print(f"🔊 音频：{v['audios']}")
