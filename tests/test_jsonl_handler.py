import pytest
import os
import json
import tempfile
from queue import Queue
from watchdog.events import FileSystemEvent
from centaur.jsonl_handler import JSONLHandler  # Replace 'your_module' with the actual module name


@pytest.fixture
def temp_jsonl_file():
    with tempfile.NamedTemporaryFile(delete=False, suffix='.jsonl') as temp_file:
        file_path = temp_file.name
    yield file_path

    if os.path.exists(file_path):
        os.remove(file_path)


@pytest.fixture
def queue():
    return Queue()


def test_on_modified_valid_json(temp_jsonl_file, queue):
    file_id = os.path.basename(temp_jsonl_file).split('.')[0]
    handler = JSONLHandler(file_id, queue)

    valid_data = [{"key": "value"}, {"number": 123}]
    with open(temp_jsonl_file, 'w', encoding='utf-8') as f:
        for item in valid_data:
            f.write(json.dumps(item) + '\n')

    event = FileSystemEvent(temp_jsonl_file)
    handler.on_modified(event)

    for item in valid_data:
        assert queue.get() == item
    assert queue.empty()


def test_on_modified_invalid_json(temp_jsonl_file, queue):
    file_id = os.path.basename(temp_jsonl_file).split('.')[0]
    handler = JSONLHandler(file_id, queue)

    invalid_data = '{"key": "value"\n{"number": 123}'
    with open(temp_jsonl_file, 'w', encoding='utf-8') as f:
        f.write(invalid_data)

    event = FileSystemEvent(temp_jsonl_file)
    handler.on_modified(event)

    assert queue.get() == {"number": 123}
    assert queue.empty()


def test_on_modified_partial_read(temp_jsonl_file, queue):
    file_id = os.path.basename(temp_jsonl_file).split('.')[0]
    handler = JSONLHandler(file_id, queue)

    with open(temp_jsonl_file, 'w', encoding='utf-8') as f:
        f.write('{"key": "value"}\n')
    event = FileSystemEvent(temp_jsonl_file)
    handler.on_modified(event)

    with open(temp_jsonl_file, 'a', encoding='utf-8') as f:
        f.write('{"number": 123}\n')
    handler.on_modified(event)

    assert queue.get() == {"key": "value"}
    assert queue.get() == {"number": 123}
    assert queue.empty()
