from pathlib import Path
import re
import tempfile

from ament_index_python.packages import get_package_share_path
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.actions import ExecuteProcess
from launch.actions import IncludeLaunchDescription
from launch.actions import OpaqueFunction
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command
from launch.substitutions import LaunchConfiguration
from launch.substitutions import PythonExpression
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


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


def _robot_description(model_path, mappings):
    command = [
        'ros2 run tools create_robot_description',
        ' --input ',
        str(model_path),
    ]
    if mappings:
        command.append(' --mappings')
        for key, value in mappings.items():
            command.extend([' ', key, '=', value])
    return ParameterValue(Command(command), value_type=str)


def _vehicle_description(hippo_sim_path):
    model_path = hippo_sim_path / 'models/hippo3/urdf/hippo3.xacro'
    return _robot_description(
        model_path,
        {
            'vehicle_name': LaunchConfiguration('vehicle_name'),
            'use_vertical_camera': LaunchConfiguration('use_vertical_camera'),
            'use_front_camera': 'False',
            'use_range_sensor': 'False',
            'use_acoustic_modem': LaunchConfiguration('use_acoustic_modem'),
        },
    )


def _pool_description(hippo_sim_path):
    model_path = hippo_sim_path / 'models/pool/urdf/pool.xacro'
    return _robot_description(model_path, {})


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


def _bag_play_action(context):
    bag = LaunchConfiguration('bag').perform(context)
    if not bag:
        return []

    cmd = [
        'ros2',
        'bag',
        'play',
        bag,
        '--clock',
        '--rate',
        LaunchConfiguration('bag_rate').perform(context),
    ]
    if _as_bool(LaunchConfiguration('bag_loop').perform(context)):
        cmd.append('--loop')

    return [ExecuteProcess(cmd=cmd, output='screen', emulate_tty=True)]


def generate_launch_description():
    hippo_sim_path = get_package_share_path('hippo_sim')
    world_file = hippo_sim_path / 'models/world/empty.sdf'

    launch_sim = LaunchConfiguration('launch_sim')
    spawn_apriltags = LaunchConfiguration('spawn_apriltags')
    vehicle_name = LaunchConfiguration('vehicle_name')
    use_sim_time = ParameterValue(
        LaunchConfiguration('use_sim_time'),
        value_type=bool,
    )
    frame_prefix = ParameterValue([vehicle_name, '/'], value_type=str)

    sim_condition = IfCondition(launch_sim)
    spawn_tags_condition = IfCondition(
        PythonExpression(
            [
                "'",
                launch_sim,
                "' in ['1', 'true', 'yes', 'on'] and '",
                spawn_apriltags,
                "' in ['1', 'true', 'yes', 'on']",
            ]
        )
    )

    start_gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            str(hippo_sim_path / 'launch/start_gazebo.launch.py')
        ),
        launch_arguments={
            'start_gui': LaunchConfiguration('start_gazebo_gui'),
            'world_file': LaunchConfiguration('world_file'),
        }.items(),
        condition=sim_condition,
    )

    spawn_tags = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            str(hippo_sim_path / 'launch/spawn_apriltag_floor.launch.py')
        ),
        condition=spawn_tags_condition,
    )

    spawn_hippocampus = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            str(hippo_sim_path / 'launch/spawn_hippocampus.launch.py')
        ),
        launch_arguments={
            'vehicle_name': vehicle_name,
            'use_sim_time': LaunchConfiguration('use_sim_time'),
            'use_vertical_camera': LaunchConfiguration('use_vertical_camera'),
            'use_acoustic_modem': LaunchConfiguration('use_acoustic_modem'),
        }.items(),
        condition=sim_condition,
    )

    vehicle_model = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        namespace=vehicle_name,
        name='robot_state_publisher',
        parameters=[
            {
                'use_sim_time': use_sim_time,
                'frame_prefix': frame_prefix,
                'robot_description': _vehicle_description(hippo_sim_path),
            }
        ],
        output='screen',
        condition=IfCondition(LaunchConfiguration('publish_models')),
    )

    joint_states = Node(
        package='tools',
        executable='publish_joint_states',
        namespace=vehicle_name,
        name='joint_state_publisher',
        parameters=[
            {
                'use_sim_time': use_sim_time,
            }
        ],
        output='screen',
        condition=IfCondition(LaunchConfiguration('publish_joint_states')),
    )

    pool_model = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        namespace='pool',
        name='robot_state_publisher',
        parameters=[
            {
                'use_sim_time': use_sim_time,
                'frame_prefix': 'pool/',
                'robot_description': _pool_description(hippo_sim_path),
            }
        ],
        output='screen',
        condition=IfCondition(LaunchConfiguration('publish_pool_model')),
    )

    pool_tf = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        arguments=[
            '--x',
            '1.0',
            '--y',
            '2.0',
            '--z',
            '-1.5',
            '--roll',
            '0.0',
            '--pitch',
            '0.0',
            '--yaw',
            '0.0',
            '--frame-id',
            'map',
            '--child-frame-id',
            'pool/base_link',
        ],
        condition=IfCondition(LaunchConfiguration('publish_pool_model')),
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                'vehicle_name',
                default_value='uuv00',
                description='uuv02 for the real robot, uuv00 for simulation.',
            ),
            DeclareLaunchArgument(
                'use_sim_time',
                default_value='true',
                choices=['true', 'false'],
                description='Use true for simulation or bag playback.',
            ),
            DeclareLaunchArgument(
                'launch_sim',
                default_value='false',
                choices=['true', 'false'],
                description='Start Gazebo and spawn the simulated Hippo.',
            ),
            DeclareLaunchArgument(
                'start_gazebo_gui',
                default_value='false',
                choices=['true', 'false'],
                description='Start the Gazebo GUI.',
            ),
            DeclareLaunchArgument(
                'bag',
                default_value='',
                description='Optional bag directory to replay while RViz runs.',
            ),
            DeclareLaunchArgument('bag_rate', default_value='1.0'),
            DeclareLaunchArgument(
                'bag_loop',
                default_value='false',
                choices=['true', 'false'],
            ),
            DeclareLaunchArgument(
                'rviz_config',
                default_value='environment',
                choices=['environment', 'simple'],
                description='RViz display configuration.',
            ),
            DeclareLaunchArgument(
                'rviz_qt_platform',
                default_value='xcb',
                choices=['auto', 'wayland', 'xcb'],
                description='Qt platform for RViz. Use xcb on WSLg.',
            ),
            DeclareLaunchArgument(
                'rviz_software_rendering',
                default_value='true',
                choices=['true', 'false'],
                description='Use Mesa software rendering for RViz.',
            ),
            DeclareLaunchArgument(
                'rviz_window_x',
                default_value='auto',
                description='RViz window X position. auto uses WSLg primary origin.',
            ),
            DeclareLaunchArgument(
                'rviz_window_y',
                default_value='auto',
                description='RViz window Y position. auto uses WSLg primary origin.',
            ),
            DeclareLaunchArgument(
                'publish_models',
                default_value='true',
                choices=['true', 'false'],
                description='Publish Hippo robot_description for RViz.',
            ),
            DeclareLaunchArgument(
                'publish_joint_states',
                default_value='true',
                choices=['true', 'false'],
                description='Publish zero thruster joint states for RViz TF.',
            ),
            DeclareLaunchArgument(
                'publish_pool_model',
                default_value='true',
                choices=['true', 'false'],
                description='Publish the pool robot description and map TF.',
            ),
            DeclareLaunchArgument(
                'spawn_apriltags',
                default_value='false',
                choices=['true', 'false'],
                description='Spawn the configured AprilTag floor in Gazebo.',
            ),
            DeclareLaunchArgument(
                'use_vertical_camera',
                default_value='false',
                choices=['true', 'false'],
                description='Include the vertical camera in the Hippo model.',
            ),
            DeclareLaunchArgument(
                'use_acoustic_modem',
                default_value='false',
                choices=['true', 'false'],
                description='Include the acoustic modem in the Hippo model.',
            ),
            DeclareLaunchArgument(
                'world_file',
                default_value=str(world_file),
                description='Gazebo world file used when launch_sim is true.',
            ),
            start_gazebo,
            spawn_tags,
            spawn_hippocampus,
            vehicle_model,
            joint_states,
            pool_model,
            pool_tf,
            OpaqueFunction(function=_bag_play_action),
            OpaqueFunction(function=_rviz_action),
        ]
    )
