from watchdog.events import FileSystemEventHandler
import json


class JSONLHandler(FileSystemEventHandler):
    def __init__(self, file_id, queue):
        self.file_id = file_id
        self.queue = queue
        self.last_read_position = 0

    def on_modified(self, event):
        if event.src_path.endswith(self.file_id + ".jsonl"):
            with open(event.src_path, 'r', encoding='utf-8') as f:
                f.seek(self.last_read_position)
                while line := f.readline():
                    try:
                        data = json.loads(line)
                        self.queue.put(data)
                    except json.JSONDecodeError:
                        continue
                self.last_read_position = f.tell()
