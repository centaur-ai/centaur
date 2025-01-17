from watchdog.events import FileSystemEventHandler
import json
import tempfile
import os


class JSONLHandler(FileSystemEventHandler):
    def __init__(self, file_id, queue):
        self.file_id = file_id
        self.queue = queue
        self.last_read_position = 0

        with open(os.path.join(tempfile.gettempdir(), "centaur", self.file_id + ".jsonl"), 'r', encoding='utf-8') as f:
            while line := f.readline():
                try:
                    data = json.loads(line)
                    self.queue.put(data)
                except json.JSONDecodeError:
                    print("Error decoding JSON in stream")
                    continue
            self.last_read_position = f.tell()

    def on_modified(self, event):
        if event.src_path.endswith(self.file_id + ".jsonl"):
            with open(event.src_path, 'r', encoding='utf-8') as f:
                f.seek(self.last_read_position)
                while line := f.readline():
                    try:
                        data = json.loads(line)
                        self.queue.put(data)
                    except json.JSONDecodeError:
                        print("Error decoding JSON in stream")
                        continue
                self.last_read_position = f.tell()
