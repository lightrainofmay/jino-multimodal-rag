from api.app import app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

from flask import render_template_string

@app.route("/", methods=["GET"])
def index():
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Multimodal Semantic Search Test</title>
        <style>
            body { font-family: sans-serif; padding: 20px; }
            input, button { padding: 8px; margin: 5px; }
            pre { background: #f0f0f0; padding: 10px; white-space: pre-wrap; }
        </style>
    </head>
    <body>
        <h2>Multimodal Semantic Search Test</h2>
        <input type="text" id="userInput" placeholder="Enter your query..." size="40">
        <button onclick="search()">Search</button>
        <pre id="result"></pre>

        <script>
            async function search() {
                const query = document.getElementById("userInput").value;
                const res = await fetch("/chat", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ message: query })
                });
                const data = await res.json();
                document.getElementById("result").textContent = JSON.stringify(data, null, 2);
            }
        </script>
    </body>
    </html>
    """)
