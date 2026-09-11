#!/usr/bin/env python3

import argparse
import re
import subprocess
import sys


def _mesh_paths_to_file_uris(robot_description):
    return re.sub(
        r'(<mesh\s+filename=")(/[^"]+)(")',
        r'\1file://\2\3',
        robot_description,
    )


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
    return _mesh_paths_to_file_uris(result.stdout)


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
