#!/usr/bin/env python3

import argparse
import csv
from pathlib import Path
import sys

def _read_series(csv_path, column):
    time_s = []
    values = []
    with Path(csv_path).open('r', encoding='utf-8') as stream:
        reader = csv.DictReader(stream)
        if column not in reader.fieldnames:
            return time_s, values
        for row in reader:
            if row.get(column, '') == '':
                continue
            time_s.append(float(row['t_rel_s']))
            values.append(float(row[column]))
    return time_s, values


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


def plot_depth(run_dir, vehicle_name, show=False):
    import matplotlib.pyplot as plt

    run_dir = Path(run_dir)
    csv_dir = run_dir / 'csv'
    plots_dir = run_dir / 'plots'
    plots_dir.mkdir(parents=True, exist_ok=True)

    odom_csv = _find_csv(csv_dir, vehicle_name, 'odometry')
    baro_csv = _find_csv(csv_dir, vehicle_name, 'barometer_height')
    if odom_csv is None and baro_csv is None:
        raise FileNotFoundError(
            f'No odometry or barometer_height CSV found in {csv_dir}'
        )

    plt.figure()
    if odom_csv is not None:
        time_s, z = _read_series(odom_csv, 'pose.pose.position.z')
        if time_s:
            plt.plot(time_s, z, label='odometry z')
    if baro_csv is not None:
        time_s, z = _read_series(baro_csv, 'point.z')
        if time_s:
            plt.plot(time_s, z, label='barometer height')

    plt.xlabel('time [s]')
    plt.ylabel('z [m]')
    plt.grid(True)
    plt.legend()
    output_path = plots_dir / 'depth.png'
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
        output_path = plot_depth(args.run, args.vehicle_name, args.show)
    except Exception as exc:
        print(f'error: {exc}', file=sys.stderr)
        return 1

    print(f'wrote {output_path}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
