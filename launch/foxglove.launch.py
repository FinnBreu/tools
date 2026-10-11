from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction
from launch.launch_description_sources import AnyLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch.substitutions import PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare
from launch_ros.actions import Node

from tools.visualization import model_actions, model_arguments, replay_actions


def _foxglove_bridge_action(context):
    vehicle_name = LaunchConfiguration('vehicle_name').perform(context)
    topic_whitelist = (
        f"['^/{vehicle_name}/.*$', '^/tf$', '^/tf_static$', '^/clock$', "
        "'^/rosout$', '^/pool/.*$']"
    )
    foxglove_launch = PathJoinSubstitution([
        FindPackageShare('foxglove_bridge'),
        'launch',
        'foxglove_bridge_launch.xml',
    ])
    return [IncludeLaunchDescription(
        AnyLaunchDescriptionSource(foxglove_launch),
        launch_arguments={
            'port': LaunchConfiguration('port'),
            'address': LaunchConfiguration('address'),
            'use_sim_time': LaunchConfiguration('use_sim_time'),
            'topic_whitelist': topic_whitelist,
        }.items(),
    )]


def generate_launch_description():
    return LaunchDescription([
        *model_arguments(),
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
        *model_actions(),
        *replay_actions(),
        Node(package='hippo_maps', executable='occupancy_grid_bridge',
             parameters=[{'use_sim_time': LaunchConfiguration('use_sim_time')}]),
        OpaqueFunction(function=_foxglove_bridge_action),
    ])
