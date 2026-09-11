from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import AnyLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch.substitutions import PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    foxglove_launch = PathJoinSubstitution([
        FindPackageShare('foxglove_bridge'),
        'launch',
        'foxglove_bridge_launch.xml',
    ])

    return LaunchDescription([
        DeclareLaunchArgument(
            'port',
            default_value='8765',
            description='Foxglove WebSocket port.',
        ),
        DeclareLaunchArgument(
            'address',
            default_value='0.0.0.0',
            description='Foxglove WebSocket bind address.',
        ),
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            choices=['true', 'false'],
            description='Use /clock as the bridge time source.',
        ),
        IncludeLaunchDescription(
            AnyLaunchDescriptionSource(foxglove_launch),
            launch_arguments={
                'port': LaunchConfiguration('port'),
                'address': LaunchConfiguration('address'),
                'use_sim_time': LaunchConfiguration('use_sim_time'),
            }.items(),
        ),
    ])
