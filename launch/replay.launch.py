from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.actions import ExecuteProcess
from launch.actions import OpaqueFunction
from launch.substitutions import LaunchConfiguration


def _as_bool(value):
    return str(value).lower() in ('1', 'true', 'yes', 'on')


def _play_process(context):
    bag = LaunchConfiguration('bag').perform(context)
    rate = LaunchConfiguration('rate').perform(context)
    clock = _as_bool(LaunchConfiguration('clock').perform(context))
    loop = _as_bool(LaunchConfiguration('loop').perform(context))

    cmd = ['ros2', 'bag', 'play', bag, '--rate', rate]
    if clock:
        cmd.append('--clock')
    if loop:
        cmd.append('--loop')

    return [ExecuteProcess(cmd=cmd, output='screen', emulate_tty=True)]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            'bag',
            description='Path to the bag directory, usually data/runs/<run>/bag.',
        ),
        DeclareLaunchArgument('rate', default_value='1.0'),
        DeclareLaunchArgument('clock', default_value='true'),
        DeclareLaunchArgument('loop', default_value='false'),
        OpaqueFunction(function=_play_process),
    ])
