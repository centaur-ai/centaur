from flask import Blueprint, Response
from watchdog.observers import Observer
from queue import Queue
import os
import time
import tempfile
from centaur.session import clients
from centaur.jsonl_handler import JSONLHandler

blueprint = Blueprint("evaluate", __name__)


@blueprint.route('/evaluate/<id>')
def evaluate(id):
    def stream():
        queue = Queue()

        file_path = os.path.join(tempfile.gettempdir(), "centaur", f"{id}.jsonl")
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, "w") as file:
            pass

        if id not in clients:
            clients[id] = []
            observer = Observer()
            observer.schedule(JSONLHandler(id), os.path.join(tempfile.gettempdir(), "centaur"), recursive=False)
            observer.start()
        clients[id].append(queue)
        try:
            while True:
                data = queue.get()
                yield data
                time.sleep(0.1)
        except GeneratorExit:
            clients[id].remove(queue)
            if not clients[id]:
                del clients[id]

    return Response(stream(), mimetype='text/event-stream')
