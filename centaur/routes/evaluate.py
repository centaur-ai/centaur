from flask import Blueprint, Response, jsonify
from watchdog.observers import Observer
from queue import Queue
import os
import time
import json
import tempfile
from centaur.session import clients
from centaur.jsonl_handler import JSONLHandler

blueprint = Blueprint("evaluate", __name__)


@blueprint.route('/evaluate/<id>')
def evaluate(id):
    def stream():
        file_path = os.path.join(
            tempfile.gettempdir(), "centaur", f"{id}.jsonl")
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, "w"):
            pass

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

    if id not in clients:
        clients[id] = True
        return Response(stream(), mimetype='text/event-stream')
    else:
        return jsonify({"error": "already_processed"}), 400
