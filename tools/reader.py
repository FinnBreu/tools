from dataclasses import dataclass
from array import array
from pathlib import Path

import rosbag2_py
from rclpy.serialization import deserialize_message
from rosidl_runtime_py.utilities import get_message
import yaml


@dataclass(frozen=True)
class BagMessage:
    topic: str
    msg: object
    timestamp_ns: int


class BagReader:
    def __init__(self, bag_path):
        self.bag_path = Path(bag_path)

    def _metadata(self):
        metadata_path = self.bag_path / 'metadata.yaml'
        if not metadata_path.exists():
            return {}
        with metadata_path.open('r', encoding='utf-8') as stream:
            return yaml.safe_load(stream) or {}

    def storage_id(self):
        info = self._metadata().get('rosbag2_bagfile_information', {})
        return info.get('storage_identifier', 'mcap')

    def list_topics(self):
        reader = self._open()
        try:
            return {
                topic.name: topic.type
                for topic in reader.get_all_topics_and_types()
            }
        finally:
            del reader

    def _open(self):
        reader = rosbag2_py.SequentialReader()
        reader.open(
            rosbag2_py.StorageOptions(
                uri=str(self.bag_path),
                storage_id=self.storage_id(),
            ),
            rosbag2_py.ConverterOptions(
                input_serialization_format='cdr',
                output_serialization_format='cdr',
            ),
        )
        return reader

    def messages(self, topics=None):
        selected = set(topics) if topics else None
        reader = self._open()
        try:
            topic_types = {
                topic.name: topic.type
                for topic in reader.get_all_topics_and_types()
            }
            type_cache = {}

            while reader.has_next():
                topic, data, timestamp_ns = reader.read_next()
                if selected is not None and topic not in selected:
                    continue
                if topic not in type_cache:
                    type_cache[topic] = get_message(topic_types[topic])
                msg = deserialize_message(data, type_cache[topic])
                yield BagMessage(topic, msg, timestamp_ns)
        finally:
            del reader

    def topic_messages(self, topic):
        return self.messages(topics=[topic])


def flatten_message(msg, prefix='', output=None):
    if output is None:
        output = {}

    if hasattr(msg, 'get_fields_and_field_types'):
        for field_name in msg.get_fields_and_field_types():
            value = getattr(msg, field_name)
            child_prefix = f'{prefix}.{field_name}' if prefix else field_name
            flatten_message(value, child_prefix, output)
        return output

    if isinstance(msg, (list, tuple, array)) or (
        hasattr(msg, 'tolist') and hasattr(msg, '__iter__')
    ):
        values = msg.tolist() if hasattr(msg, 'tolist') else msg
        for index, value in enumerate(values):
            child_prefix = f'{prefix}.{index}' if prefix else str(index)
            flatten_message(value, child_prefix, output)
        return output

    output[prefix] = msg
    return output
