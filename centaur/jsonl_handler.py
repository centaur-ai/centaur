from watchdog.events import FileSystemEventHandler
import json
from centaur.session import clients

class JSONLHandler(FileSystemEventHandler):
    def __init__(self, file_id):
        self.file_id = file_id

    def on_modified(self, event):
        if event.src_path.endswith(self.file_id + ".jsonl"):
            with open(event.src_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        if data["type"] == "data":
                            if self.file_id in clients:
                                for client in clients[self.file_id]:
                                    client.queue.put(f"data: {json.dumps(data)}\n\n")
                        elif data["type"] == "system" and data["event"] == "stream_end":
                            if self.file_id in clients:
                                for client in clients[self.file_id]:
                                    client.queue.put("event: stream_end\n\n")
                                    client.close()
                                del clients[self.file_id]
                                break
                    except json.JSONDecodeError:
                        pass
