from datetime import datetime
from pathlib import Path
import subprocess

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.actions import ExecuteProcess
from launch.actions import OpaqueFunction
from launch.substitutions import LaunchConfiguration
import yaml


def _as_bool(value):
    return str(value).lower() in ('1', 'true', 'yes', 'on')


def _git_commit():
    try:
        result = subprocess.run(
            ['git', 'rev-parse', 'HEAD'],
            cwd=Path.cwd(),
            check=True,
            capture_output=True,
            text=True,
        )
    except Exception:
        return ''
    return result.stdout.strip()


def _load_topic_profile(profile, vehicle_name):
    package_share = Path(get_package_share_directory('tools'))
    profile_path = package_share / 'config' / f'topics_{profile}.yaml'
    with profile_path.open('r', encoding='utf-8') as stream:
        config = yaml.safe_load(stream) or {}

    topics = [
        topic.replace('<vehicle>', vehicle_name)
        for topic in config.get('topics', [])
    ]
    return config, topics


def _record_process(context):
    vehicle_name = LaunchConfiguration('vehicle_name').perform(context)
    scenario = LaunchConfiguration('scenario').perform(context)
    profile = LaunchConfiguration('profile').perform(context)
    output_root = Path(LaunchConfiguration('output_root').perform(context))
    use_sim_time = _as_bool(
        LaunchConfiguration('use_sim_time').perform(context)
    )
    if vehicle_name == 'uuv00' and not use_sim_time:
        raise RuntimeError('uuv00 is the simulated robot; set use_sim_time:=true.')
    if vehicle_name == 'uuv02' and use_sim_time:
        raise RuntimeError('uuv02 is the real robot; set use_sim_time:=false.')
    source = 'sim' if use_sim_time else 'real'

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    run_id = f'{timestamp}_{vehicle_name}_{source}_{scenario}'
    run_dir = output_root / run_id
    bag_dir = run_dir / 'bag'
    csv_dir = run_dir / 'csv'
    plots_dir = run_dir / 'plots'
    for path in (bag_dir, csv_dir, plots_dir):
        path.mkdir(parents=True, exist_ok=True)
    (run_dir / 'notes.md').touch(exist_ok=True)

    profile_config, topics = _load_topic_profile(profile, vehicle_name)
    manifest = {
        'run_id': run_id,
        'created_at': datetime.now().isoformat(timespec='seconds'),
        'vehicle_type': 'hippo',
        'vehicle_name': vehicle_name,
        'source': source,
        'scenario': scenario,
        'profile': profile,
        'use_sim_time': use_sim_time,
        'storage_id': 'mcap',
        'git_commit': _git_commit(),
        'bag': str(bag_dir),
        'csv': str(csv_dir),
        'plots': str(plots_dir),
        'topics': topics,
    }
    with (run_dir / 'manifest.yaml').open('w', encoding='utf-8') as stream:
        yaml.safe_dump(manifest, stream, sort_keys=False)

    cmd = [
        'ros2',
        'bag',
        'record',
        '--storage',
        'mcap',
        '--output',
        str(bag_dir),
    ]
    if use_sim_time:
        cmd.append('--use-sim-time')
    if profile_config.get('all', False):
        cmd.append('--all')
        exclude_regex = profile_config.get('exclude_regex', '')
        if exclude_regex:
            cmd.extend(['--exclude-regex', exclude_regex])
    else:
        cmd.append('--topics')
        cmd.extend(topics)

    return [
        ExecuteProcess(
            cmd=cmd,
            output='screen',
            emulate_tty=True,
        )
    ]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            'vehicle_name',
            default_value='uuv02',
            description='uuv02 for the real robot, uuv00 for simulation.',
        ),
        DeclareLaunchArgument(
            'scenario',
            default_value='manual',
            description='Short scenario name used in the run directory.',
        ),
        DeclareLaunchArgument(
            'profile',
            default_value='control',
            description='Topic profile name without the topics_ prefix.',
        ),
        DeclareLaunchArgument(
            'output_root',
            default_value='data/runs',
            description='Directory where run folders are created.',
        ),
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            choices=['true', 'false'],
            description='Record using /clock. Use true for simulation.',
        ),
        OpaqueFunction(function=_record_process),
    ])
