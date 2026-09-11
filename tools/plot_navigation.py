#!/usr/bin/env python3

import argparse
import csv
from pathlib import Path
import sys

def _read_xy(csv_path):
    time_s = []
    x = []
    y = []
    with Path(csv_path).open('r', encoding='utf-8') as stream:
        reader = csv.DictReader(stream)
        required = {'t_rel_s', 'pose.pose.position.x', 'pose.pose.position.y'}
        if not required.issubset(set(reader.fieldnames or [])):
            return time_s, x, y
        for row in reader:
            time_s.append(float(row['t_rel_s']))
            x.append(float(row['pose.pose.position.x']))
            y.append(float(row['pose.pose.position.y']))
    return time_s, x, y


def _find_csv(csv_dir, vehicle_name, topic_suffix):
    candidates = [
        csv_dir / f'{vehicle_name}_{topic_suffix}.csv',
        csv_dir / f'{topic_suffix}.csv',
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    matches = sorted(csv_dir.glob(f'*{topic_suffix}.csv'))
    return matches[0] if matches else None


def plot_navigation(run_dir, vehicle_name, show=False):
    import matplotlib.pyplot as plt

    run_dir = Path(run_dir)
    csv_dir = run_dir / 'csv'
    plots_dir = run_dir / 'plots'
    plots_dir.mkdir(parents=True, exist_ok=True)

    odom_csv = _find_csv(csv_dir, vehicle_name, 'odometry')
    if odom_csv is None:
        raise FileNotFoundError(f'No odometry CSV found in {csv_dir}')

    _, x, y = _read_xy(odom_csv)
    if not x:
        raise ValueError(f'No x/y odometry columns found in {odom_csv}')

    plt.figure()
    plt.plot(x, y, label='odometry')
    plt.xlabel('x [m]')
    plt.ylabel('y [m]')
    plt.axis('equal')
    plt.grid(True)
    plt.legend()
    output_path = plots_dir / 'xy_path.png'
    plt.savefig(output_path, dpi=160, bbox_inches='tight')
    if show:
        plt.show()
    plt.close()
    return output_path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run', required=True)
    parser.add_argument('--vehicle-name', default='uuv02')
    parser.add_argument('--show', action='store_true')
    args = parser.parse_args()

    try:
        output_path = plot_navigation(args.run, args.vehicle_name, args.show)
    except Exception as exc:
        print(f'error: {exc}', file=sys.stderr)
        return 1

    print(f'wrote {output_path}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
