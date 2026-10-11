#!/usr/bin/env python3

import argparse
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

from ament_index_python.packages import get_package_share_path


def _mesh_paths_to_uris(robot_description):
    root = ET.fromstring(robot_description)
    package_path = get_package_share_path('hippo_sim')
    for mesh in root.iter('mesh'):
        path = Path(mesh.get('filename', ''))
        if not path.is_absolute():
            continue
        if path.is_relative_to(package_path):
            uri = 'package://hippo_sim/' + path.relative_to(package_path).as_posix()
        else:
            uri = path.as_uri()
        mesh.set('filename', uri)
    return ET.tostring(root, encoding='unicode')


def create_robot_description(input_path, mappings):
    cmd = [
        'ros2',
        'run',
        'hippo_sim',
        'create_robot_description.py',
        '--input',
        input_path,
    ]
    if mappings:
        cmd.append('--mappings')
        cmd.extend(mappings)

    result = subprocess.run(
        cmd,
        check=True,
        capture_output=True,
        text=True,
    )
    return _mesh_paths_to_uris(result.stdout)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True)
    parser.add_argument(
        '--mappings',
        nargs='*',
        default=[],
        help='space separated list of mappings in the form of arg_name=value',
    )
    args = parser.parse_args()

    try:
        print(
            create_robot_description(args.input, args.mappings),
            end='',
        )
    except subprocess.CalledProcessError as exc:
        if exc.stderr:
            print(exc.stderr, file=sys.stderr, end='')
        return exc.returncode
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
