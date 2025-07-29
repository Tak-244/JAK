from flask import Flask, request, Response, send_from_directory, jsonify
import os
import time

app = Flask(__name__)
CLOUD_PATH = "cloud.txt"

@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('.', filename)

@app.route('/api_sse.php')
def stream_logs():
    url = request.args.get('url', '').lower()
    if not url:
        return Response("event: error\ndata: {\"message\": \"URL não fornecida.\"}\n\n", mimetype='text/event-stream')

    def event_stream():
        start = time.time()
        total_found = 0

        if not os.path.exists(CLOUD_PATH):
            yield f"event: error\ndata: {{\"message\": \"Arquivo cloud.txt não encontrado.\"}}\n\n"
            return

        with open(CLOUD_PATH, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if url in line.lower():
                    parts = line.strip().split(":", 2)
                    if len(parts) == 3:
                        result = {
                            "url": parts[0],
                            "user": parts[1],
                            "pass": parts[2]
                        }
                        yield f"event: found_result\ndata: {result.__str__().replace(\"'\", '\"')}\n\n"
                        total_found += 1
                        time.sleep(0.01)

        duration = f"{time.time() - start:.2f}s"
        done_payload = {
            "total_encontrados": total_found,
            "tempo_de_busca": duration
        }
        yield f"event: done\ndata: {done_payload.__str__().replace(\"'\", '\"')}\n\n"

    return Response(event_stream(), mimetype='text/event-stream')

@app.route('/api_sse.php?action=dashboard')
def dashboard_info():
    if not os.path.exists(CLOUD_PATH):
        return jsonify({
            "total_files": 1,
            "total_lines": 0,
            "total_size_gb": "0.00",
            "history": { "h24": 0, "d3": 0, "d7": 0, "d30": 0 }
        })

    with open(CLOUD_PATH, "r", encoding="utf-8", errors="ignore") as f:
        linhas = f.readlines()
    
    size_bytes = os.path.getsize(CLOUD_PATH)
    return jsonify({
        "total_files": 1,
        "total_lines": len(linhas),
        "total_size_gb": f"{size_bytes / (1024**3):.2f}",
        "history": {
            "h24": len(linhas),
            "d3": len(linhas),
            "d7": len(linhas),
            "d30": len(linhas)
        }
    })

if __name__ == "__main__":
    app.run(debug=True, port=8000, threaded=True)
