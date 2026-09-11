#!/usr/bin/env python3

import argparse
import csv
from pathlib import Path
import re
import sys

from ament_index_python.packages import get_package_share_directory
import yaml

from tools.reader import BagReader
from tools.reader import flatten_message


def _load_yaml(path):
    with Path(path).open('r', encoding='utf-8') as stream:
        return yaml.safe_load(stream) or {}


def _sanitize_topic(topic):
    name = topic.strip('/').replace('/', '_')
    name = re.sub(r'[^A-Za-z0-9_.-]+', '_', name)
    return name or 'root'


def _field_sort_key(name):
    parts = re.split(r'(\d+)', name)
    return [int(part) if part.isdigit() else part for part in parts]


def _topic_profile(profile, vehicle_name):
    package_share = Path(get_package_share_directory('tools'))
    profile_path = package_share / 'config' / f'topics_{profile}.yaml'
    config = _load_yaml(profile_path)
    if config.get('all', False):
        return None
    return [
        topic.replace('<vehicle>', vehicle_name)
        for topic in config.get('topics', [])
    ]


def _resolve_paths(args):
    if args.run:
        run_dir = Path(args.run)
        manifest_path = run_dir / 'manifest.yaml'
        manifest = _load_yaml(manifest_path) if manifest_path.exists() else {}
        bag = Path(args.bag) if args.bag else Path(manifest.get('bag', run_dir / 'bag'))
        out = Path(args.out) if args.out else Path(manifest.get('csv', run_dir / 'csv'))
        vehicle_name = args.vehicle_name or manifest.get('vehicle_name', 'uuv02')
        profile = args.profile or manifest.get('profile')
        return bag, out, vehicle_name, profile

    if not args.bag:
        raise ValueError('Either --run or --bag is required.')
    return (
        Path(args.bag),
        Path(args.out or 'csv'),
        args.vehicle_name or 'uuv02',
        args.profile,
    )


def _selected_topics(args, reader, vehicle_name, profile):
    available = set(reader.list_topics())
    if args.topics:
        requested = args.topics
    elif profile:
        requested = _topic_profile(profile, vehicle_name)
    else:
        requested = sorted(
            topic for topic in available
            if topic not in ('/tf', '/tf_static', '/rosout')
        )

    if requested is None:
        return None

    missing = [topic for topic in requested if topic not in available]
    for topic in missing:
        print(f'warning: topic not in bag: {topic}', file=sys.stderr)
    return [topic for topic in requested if topic in available]


def export_csv(bag_path, out_dir, topics=None):
    reader = BagReader(bag_path)
    out_dir.mkdir(parents=True, exist_ok=True)

    writers = {}
    files = {}
    rows_written = {}
    t0_ns = None

    try:
        for bag_msg in reader.messages(topics=topics):
            if t0_ns is None:
                t0_ns = bag_msg.timestamp_ns

            values = flatten_message(bag_msg.msg)
            row = {
                't_ros_ns': bag_msg.timestamp_ns,
                't_rel_s': (bag_msg.timestamp_ns - t0_ns) * 1e-9,
                'topic': bag_msg.topic,
                **values,
            }

            if bag_msg.topic not in writers:
                csv_path = out_dir / f'{_sanitize_topic(bag_msg.topic)}.csv'
                file_handle = csv_path.open('w', newline='', encoding='utf-8')
                fieldnames = (
                    ['t_ros_ns', 't_rel_s', 'topic']
                    + sorted(values, key=_field_sort_key)
                )
                writer = csv.DictWriter(file_handle, fieldnames=fieldnames)
                writer.writeheader()
                writers[bag_msg.topic] = writer
                files[bag_msg.topic] = file_handle
                rows_written[bag_msg.topic] = 0

            writers[bag_msg.topic].writerow(row)
            rows_written[bag_msg.topic] += 1
    finally:
        for file_handle in files.values():
            file_handle.close()

    return rows_written


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run', help='Run directory below data/runs.')
    parser.add_argument('--bag', help='Bag directory. Overrides manifest bag.')
    parser.add_argument('--out', help='CSV output directory.')
    parser.add_argument('--vehicle-name', help='Vehicle namespace in the bag.')
    parser.add_argument('--profile', help='Topic profile name.')
    parser.add_argument('--topics', nargs='+', help='Explicit topic list.')
    args = parser.parse_args()

    try:
        bag, out, vehicle_name, profile = _resolve_paths(args)
        reader = BagReader(bag)
        topics = _selected_topics(args, reader, vehicle_name, profile)
        rows = export_csv(bag, out, topics)
    except Exception as exc:
        print(f'error: {exc}', file=sys.stderr)
        return 1

    for topic, count in sorted(rows.items()):
        print(f'{topic}: {count} rows')
    print(f'wrote CSV files to {out}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
