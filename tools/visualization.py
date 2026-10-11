"""Shared model and replay setup for simulation and visualization launchers."""

from ament_index_python.packages import get_package_share_path
from launch.actions import DeclareLaunchArgument, ExecuteProcess, GroupAction, OpaqueFunction
from launch.conditions import IfCondition
from launch.substitutions import Command, LaunchConfiguration, PythonExpression
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def model_arguments(simulation=False):
    return [
        DeclareLaunchArgument(
            'vehicle_name', default_value='uuv00',
            choices=['uuv00'] if simulation else ['uuv00', 'uuv02'],
            description='uuv00 for simulation, uuv02 for the real Hippo.',
        ),
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='true' if simulation else PythonExpression([
                "'true' if '", LaunchConfiguration('vehicle_name'),
                "' == 'uuv00' else 'false'",
            ]),
            choices=['true'] if simulation else ['true', 'false'],
            description='Use /clock; override to true for real-vehicle bag playback.',
        ),
        DeclareLaunchArgument(
            'publish_models', default_value='true', choices=['true', 'false'],
            description='Publish model descriptions and visualization TF helpers.',
        ),
        DeclareLaunchArgument(
            'publish_joint_states', default_value='true', choices=['true', 'false'],
            description='Publish zero thruster joint states when publishing models.',
        ),
        DeclareLaunchArgument(
            'publish_pool_model', default_value='true', choices=['true', 'false'],
            description='Include the pool description and map TF when publishing models.',
        ),
        DeclareLaunchArgument(
            'use_vertical_camera', default_value='false', choices=['true', 'false'],
            description='Include the vertical camera in the Hippo model.',
        ),
        DeclareLaunchArgument(
            'use_acoustic_modem', default_value='false', choices=['true', 'false'],
            description='Include the acoustic modem in the Hippo model.',
        ),
    ]


def _robot_description(model_path, mappings):
    command = ['ros2 run tools create_robot_description --input ', str(model_path)]
    if mappings:
        command.append(' --mappings')
        for key, value in mappings.items():
            command.extend([' ', key, '=', value])
    return ParameterValue(Command(command), value_type=str)


def model_actions():
    hippo_sim_path = get_package_share_path('hippo_sim')
    vehicle_name = LaunchConfiguration('vehicle_name')
    use_sim_time = ParameterValue(LaunchConfiguration('use_sim_time'), value_type=bool)
    vehicle_description = _robot_description(
        hippo_sim_path / 'models/hippo3/urdf/hippo3.xacro',
        {
            'vehicle_name': vehicle_name,
            'use_vertical_camera': LaunchConfiguration('use_vertical_camera'),
            'use_front_camera': 'False',
            'use_range_sensor': 'False',
            'use_acoustic_modem': LaunchConfiguration('use_acoustic_modem'),
        },
    )
    return [GroupAction(
        condition=IfCondition(LaunchConfiguration('publish_models')),
        actions=[
            Node(
                package='robot_state_publisher', executable='robot_state_publisher',
                namespace=vehicle_name, name='robot_state_publisher',
                parameters=[{
                    'use_sim_time': use_sim_time,
                    'frame_prefix': ParameterValue([vehicle_name, '/'], value_type=str),
                    'robot_description': vehicle_description,
                }], output='screen',
            ),
            Node(
                package='tools', executable='publish_joint_states',
                namespace=vehicle_name, name='joint_state_publisher',
                parameters=[{'use_sim_time': use_sim_time}], output='screen',
                condition=IfCondition(LaunchConfiguration('publish_joint_states')),
            ),
            Node(
                package='robot_state_publisher', executable='robot_state_publisher',
                namespace='pool', name='robot_state_publisher',
                parameters=[{
                    'use_sim_time': use_sim_time,
                    'frame_prefix': 'pool/',
                    'robot_description': _robot_description(
                        hippo_sim_path / 'models/pool/urdf/pool.xacro', {},
                    ),
                }], output='screen',
                condition=IfCondition(LaunchConfiguration('publish_pool_model')),
            ),
            Node(
                package='tf2_ros', executable='static_transform_publisher',
                arguments=[
                    '--x', '1.0', '--y', '2.0', '--z', '-1.5',
                    '--roll', '0.0', '--pitch', '0.0', '--yaw', '0.0',
                    '--frame-id', 'map', '--child-frame-id', 'pool/base_link',
                ],
                parameters=[{'use_sim_time': use_sim_time}],
                condition=IfCondition(LaunchConfiguration('publish_pool_model')),
            ),
        ],
    )]


def _bag_play_action(context):
    bag = LaunchConfiguration('bag').perform(context)
    if not bag:
        return []
    cmd = [
        'ros2', 'bag', 'play', bag, '--clock', '--rate',
        LaunchConfiguration('bag_rate').perform(context),
    ]
    if LaunchConfiguration('bag_loop').perform(context) == 'true':
        cmd.append('--loop')
    return [ExecuteProcess(cmd=cmd, output='screen', emulate_tty=True)]


def replay_actions():
    return [
        DeclareLaunchArgument('bag', default_value='', description='Optional bag to replay.'),
        DeclareLaunchArgument('bag_rate', default_value='1.0'),
        DeclareLaunchArgument('bag_loop', default_value='false', choices=['true', 'false']),
        OpaqueFunction(function=_bag_play_action),
    ]
