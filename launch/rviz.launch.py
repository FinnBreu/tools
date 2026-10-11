from pathlib import Path
import re
import tempfile

from ament_index_python.packages import get_package_share_path
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

from tools.visualization import model_actions, model_arguments, replay_actions


def _as_bool(value):
    return str(value).lower() in ('1', 'true', 'yes', 'on')


def _rviz_env(context):
    platform = LaunchConfiguration('rviz_qt_platform').perform(context)
    env = {'QT_X11_NO_MITSHM': '1'}
    if platform != 'auto':
        env['QT_QPA_PLATFORM'] = platform
    if _as_bool(LaunchConfiguration('rviz_software_rendering').perform(context)):
        env['LIBGL_ALWAYS_SOFTWARE'] = '1'
    return env


def _wslg_client_origin():
    weston_log = Path('/mnt/wslg/weston.log')
    if not weston_log.exists():
        return None

    pattern = re.compile(r'client origin \(0,0\) is \(([-0-9]+),([-0-9]+)\)')
    origin = None
    for line in weston_log.read_text(encoding='utf-8', errors='ignore').splitlines():
        match = pattern.search(line)
        if match:
            origin = (int(match.group(1)), int(match.group(2)))
    return origin


def _replace_geometry_value(config_text, key, value):
    return re.sub(
        rf'(\n  {key}:\s*)[-0-9]+',
        rf'\g<1>{value}',
        config_text,
        count=1,
    )


def _apply_window_geometry(config_text, context):
    x = LaunchConfiguration('rviz_window_x').perform(context)
    y = LaunchConfiguration('rviz_window_y').perform(context)

    if x == 'auto' or y == 'auto':
        origin = _wslg_client_origin()
        if origin is not None:
            origin_x, origin_y = origin
            if x == 'auto':
                x = str(origin_x + 80)
            if y == 'auto':
                y = str(origin_y + 80)

    if x != 'auto':
        config_text = _replace_geometry_value(config_text, 'X', x)
    if y != 'auto':
        config_text = _replace_geometry_value(config_text, 'Y', y)
    return config_text


def _rviz_action(context):
    package_path = get_package_share_path('tools')
    vehicle_name = LaunchConfiguration('vehicle_name').perform(context)
    rviz_config = LaunchConfiguration('rviz_config').perform(context)
    safe_vehicle_name = ''.join(
        char if char.isalnum() or char in ('_', '-') else '_'
        for char in vehicle_name
    )

    if rviz_config == 'environment':
        template_path = package_path / 'rviz/hippo_environment.rviz.in'
        config_text = template_path.read_text(encoding='utf-8').format(
            vehicle_name=vehicle_name
        )
    else:
        template_path = package_path / 'rviz/hippo.rviz'
        config_text = template_path.read_text(encoding='utf-8').replace(
            '__VEHICLE_NAME__', vehicle_name
        )
    config_text = _apply_window_geometry(config_text, context)

    generated_config = Path(tempfile.gettempdir()) / (
        f'hippo_{rviz_config}_{safe_vehicle_name}.rviz'
    )
    generated_config.write_text(config_text, encoding='utf-8')

    return [
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            arguments=['-d', str(generated_config)],
            parameters=[{
                'use_sim_time': _as_bool(
                    LaunchConfiguration('use_sim_time').perform(context)
                )
            }],
            additional_env=_rviz_env(context),
            output='screen',
        )
    ]


def generate_launch_description():
    return LaunchDescription([
        *model_arguments(),
        DeclareLaunchArgument(
            'rviz_config', default_value='environment', choices=['environment', 'simple'],
            description='RViz display configuration.',
        ),
        DeclareLaunchArgument(
            'rviz_qt_platform', default_value='xcb', choices=['auto', 'wayland', 'xcb'],
            description='Qt platform for RViz. Use xcb on WSLg.',
        ),
        DeclareLaunchArgument(
            'rviz_software_rendering', default_value='true', choices=['true', 'false'],
            description='Use Mesa software rendering for RViz.',
        ),
        DeclareLaunchArgument(
            'rviz_window_x', default_value='auto',
            description='RViz window X position. auto uses WSLg primary origin.',
        ),
        DeclareLaunchArgument(
            'rviz_window_y', default_value='auto',
            description='RViz window Y position. auto uses WSLg primary origin.',
        ),
        *model_actions(),
        *replay_actions(),
        OpaqueFunction(function=_rviz_action),
    ])
