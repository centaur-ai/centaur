from flask import Blueprint, Response, jsonify, request
from watchdog.observers import Observer
from queue import Queue
import os
import time
import json
import tempfile
import subprocess
import uuid
from centaur.session import clients
from centaur.jsonl_handler import JSONLHandler

blueprint = Blueprint("evaluate", __name__)

pwl_path = os.getenv("PWL_PATH", "/home/ubuntu/qa/PWL")


@blueprint.route('/evaluate', methods=['POST'])
def stream():
    data = request.get_json()
    evaluate_id = uuid.uuid4()

    if "query" in data:
        query =  data["query"]
    else:
        query = None

    if "description" in data:
        description = data["description"]
    else:
        return jsonify({"error": "description_not_found"}), 400

    if "file" in data:
        file = data["file"]
    else:
        file = os.path.join(pwl_path, f"{evaluate_id}.txt")
        with open(file, "w") as f:
            f.write(description)
            f.close()

    stream_path = os.path.join(
        tempfile.gettempdir(), "centaur", f"{evaluate_id}.jsonl")
    os.makedirs(os.path.dirname(stream_path), exist_ok=True)

    with open(stream_path, "w") as f:
        f.write(json.dumps({"type": "system", "event": "stream_start", "description": description, "query": query}) + "\n")
        f.close()

    if evaluate_id not in clients:
        clients[evaluate_id] = True
        subprocess.Popen(f"{pwl_path}/stream.sh {file} {id}", shell=True, cwd=pwl_path)
        return jsonify({"id": evaluate_id}), 200
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

        proofs = {}

        try:
            while True:
                if not queue.empty():
                    data = queue.get()

                    if ("id" in data
                            and "proof_id" in data
                            and "type" in data
                            and data["type"] == "logical_form"):
                        proof_id = data["proof_id"]
                        proofs[proof_id] = data
                    elif ("id" in data
                            and "type" in data
                            and data["type"] == "proof"):
                        proof_id = data["id"]
                        if proof_id in proofs:
                            logical_form = proofs[proof_id]
                            logical_form["proof"] = data
                            yield f"data: {json.dumps(logical_form)}\n\n"
                            del proofs[proof_id]
                    elif "type" in data and data["type"] == "stream_end":
                        observer.stop()
                    else:
                        yield f"data: {json.dumps(data)}\n\n"

                time.sleep(0.1)
        except GeneratorExit:
            observer.stop()

    return Response(stream(), mimetype='text/event-stream')
