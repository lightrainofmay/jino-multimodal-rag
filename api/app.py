from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import os
from dotenv import load_dotenv

from app.embedder import load_and_embed, create_embeddings_and_index
from app.search import extract_keywords, semantic_search, process_results

# Load .env environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Get OpenAI API key from environment
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "your_key_here")

# Initialize embeddings and index
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

        print(f"User query: {query}")

        keyword = extract_keywords(query, OPENAI_API_KEY)
        print(f"Extracted keyword: {keyword}")

        text_results = semantic_search(keyword, df, faiss_index, model)
        print(f"Number of semantic search results: {len(text_results)}")

        media = process_results(df, text_results)
        print(f"Final returned media items: {len(media)}")

        return jsonify({"query": query, "search_results": media})

    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/", methods=["GET"])
def index():
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Jino Traditional Knowledge Multimodal RAG System</title>
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
        <h2>Jino Traditional Knowledge Multimodal RAG System</h2>
        <p>Please enter a question, e.g., "How do you say 'fire' in the Jino language?"</p>
        <input type="text" id="userInput" placeholder="Enter your query..." size="40">
        <button onclick="search()">Search</button>

        <div id="loading">
            <span class="loader"></span> AI is thinking, please wait...
        </div>

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
                        container.innerHTML = "<p>No relevant content found</p>";
                        return;
                    }

                    const header = document.createElement("h3");
                    header.textContent = `Query: ${data.query}`;
                    container.appendChild(header);

                    for (const [text, media] of Object.entries(data.search_results)) {
                        const card = document.createElement("div");
                        card.className = "entry";

                        const title = document.createElement("h4");
                        title.textContent = `Text: ${text}`;
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
                    container.innerHTML = `<p>Request failed: ${err.message}</p>`;
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

        print("Refreshing data and index...")
        crawl_all_pages(output_path=json_path)

        global df, faiss_index, model
        df, faiss_index, model = create_embeddings_and_index(
            json_path=json_path,
            embedding_path=embedding_path,
            index_path=index_path
        )

        print("Data refresh completed")
        return jsonify({"status": "Data refreshed successfully"})
    except Exception as e:
        print(f"Refresh failed: {str(e)}")
        return jsonify({"error": str(e)}), 500
