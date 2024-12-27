from flask import Blueprint, Response, jsonify, request
from watchdog.observers import Observer
from queue import Queue
import os
import time
import json
import tempfile
import subprocess
from centaur.session import clients
from centaur.jsonl_handler import JSONLHandler

blueprint = Blueprint("evaluate", __name__)

pwl_path = os.getenv("PWL_PATH", "/home/ubuntu/PWL")


@blueprint.route('/evaluate', methods=['POST'])
def stream():
    data = request.get_json()

    if "id" in data:
        id = data["id"]
    else:
        return jsonify({"error": "id_not_found"}), 400

    if "description" in data:
        description = data["description"]
    else:
        return jsonify({"error": "description_not_found"}), 400

    if "file" in data:
        file = data["file"]
    else:
        return jsonify({"error": "file_not_found"}), 400

    file_path = os.path.join(
        tempfile.gettempdir(), "centaur", f"{id}.jsonl")
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    with open(file_path, "w") as f:
        f.write(json.dumps({"type": "system", "event": "stream_start", "description": description}) + "\n")
        f.close()

    if id not in clients:
        clients[id] = True
        subprocess.Popen(f"{pwl_path}/pwl_reasoner_dbg {file} --id {id}", shell=True, cwd=pwl_path)
        return jsonify({"id": id}), 200
    else:
        return jsonify({"error": "already_processed"}), 400


@blueprint.route('/evaluate/<id>', methods=['GET'])
def init(id):
    def stream():
        queue = Queue()
        observer = Observer()
        observer.schedule(
            JSONLHandler(id, queue),
            os.path.join(tempfile.gettempdir(), "centaur"),
            recursive=False)
        observer.start()

        try:
            while True:
                if not queue.empty():
                    data = queue.get()
                    if ("event" in data
                            and "type" in data
                            and data["type"] == "system"
                            and data["event"] == "stream_end"):
                        observer.stop()
                        break
                    else:
                        yield f"data: {json.dumps(data)}\n\n"
                time.sleep(0.1)
        except GeneratorExit:
            observer.stop()

    return Response(stream(), mimetype='text/event-stream')
