from ament_index_python.packages import get_package_share_path
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import EqualsSubstitution, LaunchConfiguration

from tools.visualization import model_actions, model_arguments


def generate_launch_description():
    hippo_sim_path = get_package_share_path('hippo_sim')
    tools_path = get_package_share_path('tools')

    viewers = []
    for viewer in ('rviz', 'foxglove'):
        viewers.append(GroupAction(
            condition=IfCondition(EqualsSubstitution(LaunchConfiguration('visualization'), viewer)),
            actions=[IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    str(tools_path / 'launch' / f'{viewer}.launch.py')
                ),
                launch_arguments={
                    'vehicle_name': LaunchConfiguration('vehicle_name'),
                    'use_sim_time': LaunchConfiguration('use_sim_time'),
                    'publish_models': 'false',
                }.items(),
            )],
        ))

    return LaunchDescription([
        *model_arguments(simulation=True),
        DeclareLaunchArgument(
            'visualization', default_value='rviz', choices=['rviz', 'foxglove', 'none'],
            description='Viewer to start; none also supports an already running viewer.',
        ),
        DeclareLaunchArgument(
            'start_gazebo_gui', default_value='false', choices=['true', 'false'],
            description='Start the Gazebo GUI.',
        ),
        DeclareLaunchArgument(
            'spawn_apriltags', default_value='false', choices=['true', 'false'],
            description='Spawn the configured AprilTag floor in Gazebo.',
        ),
        DeclareLaunchArgument(
            'world_file', default_value=str(hippo_sim_path / 'models/world/empty.sdf'),
            description='Gazebo world file.',
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                str(hippo_sim_path / 'launch/start_gazebo.launch.py')
            ),
            launch_arguments={
                'start_gui': LaunchConfiguration('start_gazebo_gui'),
                'world_file': LaunchConfiguration('world_file'),
            }.items(),
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                str(hippo_sim_path / 'launch/spawn_apriltag_floor.launch.py')
            ),
            condition=IfCondition(LaunchConfiguration('spawn_apriltags')),
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                str(hippo_sim_path / 'launch/spawn_hippocampus.launch.py')
            ),
            launch_arguments={
                name: LaunchConfiguration(name) for name in (
                    'vehicle_name', 'use_sim_time', 'use_vertical_camera', 'use_acoustic_modem',
                )
            }.items(),
        ),
        *model_actions(),
        *viewers,
    ])
