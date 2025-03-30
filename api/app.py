from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import os
from dotenv import load_dotenv

from app.embedder import load_and_embed, create_embeddings_and_index
from app.search import extract_keywords, semantic_search, process_results

# ✅ 加载 .env 文件
load_dotenv()

app = Flask(__name__)
CORS(app)

# ✅ 获取 OpenAI API KEY
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "your_key_here")

# ✅ 初始化载入嵌入和索引
json_path = "data/jino_all_media.json"
embedding_path = "data/text_embeddings.pkl"
index_path = "data/faiss_index.bin"

df, faiss_index, model = load_and_embed(
    json_path=json_path,
    embedding_path=embedding_path,
    index_path=index_path
)

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.json
        query = data.get("message", "").strip()

        if not query:
            return jsonify({"error": "Message cannot be empty"}), 400

        print(f"🟡 用户输入的查询内容: {query}")

        keyword = extract_keywords(query, OPENAI_API_KEY)
        print(f"🟠 提取关键词: {keyword}")

        text_results = semantic_search(keyword, df, faiss_index, model)
        print(f"🔵 语义搜索结果数量: {len(text_results)}")

        media = process_results(df, text_results)
        print(f"🟢 最终返回的媒体内容: {len(media)}")

        return jsonify({"query": query, "search_results": media})

    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/", methods=["GET"])
def index():
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="zh">
    <head>
        <meta charset="UTF-8">
        <title>基诺传统知识多模态RAG系统</title>
        <style>
            body { font-family: sans-serif; padding: 20px; }
            input, button { padding: 8px; margin: 5px; }
            .entry { border: 1px solid #ccc; padding: 10px; margin-top: 10px; border-radius: 5px; background-color: #f9f9f9; }
            img { max-width: 200px; margin: 5px; }
            audio { display: block; margin-top: 5px; }
            .loader {
                border: 4px solid #f3f3f3;
                border-top: 4px solid #888;
                border-radius: 50%;
                width: 24px;
                height: 24px;
                animation: spin 1s linear infinite;
                display: inline-block;
                margin-right: 10px;
                vertical-align: middle;
            }
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            #loading {
                display: none;
                margin-top: 15px;
                color: #666;
                font-size: 16px;
            }
        </style>
    </head>
   <body>
    <h2>🔍 基诺传统知识多模态RAG系统<br>🔍 Jino Traditional Knowledge Multimodal RAG System</h2>

    <p>请输入一个问题，例如：“基诺语的火怎么说？”<br>
       Please enter a question, e.g., "How do you say 'fire' in the Jino language?"</p>

    <input type="text" id="userInput" placeholder="请输入查询内容... / Enter your query..." size="40">
    <button onclick="search()">搜索 / Search</button>

    <div id="loading">
        <span class="loader"></span> 🤖 AI 正在思考中，请稍候...<br>
        🤖 AI is thinking, please wait...
    </div>
</body>


        <div id="results"></div>

        <script>
            async function search() {
                const query = document.getElementById("userInput").value;
                const loading = document.getElementById("loading");
                const container = document.getElementById("results");

                loading.style.display = "block";
                container.innerHTML = "";

                try {
                    const res = await fetch("/chat", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ message: query })
                    });

                    const data = await res.json();

                    if (!data.search_results || Object.keys(data.search_results).length === 0) {
                        container.innerHTML = "<p>❌ 未找到任何相关内容</p>";
                        return;
                    }

                    const header = document.createElement("h3");
                    header.textContent = `🔎 查询内容：${data.query}`;
                    container.appendChild(header);

                    for (const [text, media] of Object.entries(data.search_results)) {
                        const card = document.createElement("div");
                        card.className = "entry";

                        const title = document.createElement("h4");
                        title.textContent = `📝 ${text}`;
                        card.appendChild(title);

                        if (media.images) {
                            const imgWrapper = document.createElement("div");
                            media.images.forEach(url => {
                                const img = document.createElement("img");
                                img.src = url;
                                img.loading = "lazy";
                                imgWrapper.appendChild(img);
                            });
                            card.appendChild(imgWrapper);
                        }

                        if (media.audios) {
                            const audioWrapper = document.createElement("div");
                            media.audios.forEach(url => {
                                const audio = document.createElement("audio");
                                audio.controls = true;
                                audio.src = url;
                                audioWrapper.appendChild(audio);
                            });
                            card.appendChild(audioWrapper);
                        }

                        container.appendChild(card);
                    }
                } catch (err) {
                    container.innerHTML = `<p>❌ 请求失败：${err.message}</p>`;
                } finally {
                    loading.style.display = "none";
                }
            }

            document.getElementById("userInput").addEventListener("keydown", function(event) {
                if (event.key === "Enter") {
                    search();
                }
            });
        </script>
    </body>
    </html>
    """)


@app.route("/refresh", methods=["GET"])
def refresh_data():
    try:
        from app.crawler import crawl_all_pages

        print("🔁 开始刷新数据和索引...")
        crawl_all_pages(output_path=json_path)

        global df, faiss_index, model
        df, faiss_index, model = create_embeddings_and_index(
            json_path=json_path,
            embedding_path=embedding_path,
            index_path=index_path
        )

        print("✅ 数据刷新完毕")
        return jsonify({"status": "✅ 数据刷新成功"})
    except Exception as e:
        print(f"❌ 刷新失败: {str(e)}")
        return jsonify({"error": str(e)}), 500
