"""Resolve the real launch tree without starting ROS nodes or GUI processes."""

from pathlib import Path
import unittest
from unittest.mock import patch

import yaml
from launch import LaunchContext
from launch.actions import ExecuteProcess
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command
from launch.utilities import perform_substitutions


LAUNCH_DIR = Path(__file__).resolve().parents[1] / 'launch'


def resolve_launch(name, **arguments):
    context = LaunchContext()
    context.launch_configurations.update(arguments)
    processes = []

    def capture(process, context):
        cmd = [perform_substitutions(context, part) for part in process.cmd]
        params = {}
        for index, part in enumerate(cmd[:-1]):
            if part == '--params-file':
                content = yaml.safe_load(Path(cmd[index + 1]).read_text())
                for node in content.values():
                    params.update(node.get('ros__parameters', {}))
        processes.append((cmd, params))
        return []

    def visit(entity):
        for child in entity.visit(context) or []:
            visit(child)

    source = PythonLaunchDescriptionSource(str(LAUNCH_DIR / f'{name}.launch.py'))
    with patch.object(ExecuteProcess, 'execute', capture), patch.object(
        Command, 'perform', return_value='<robot name="test"><link name="base_link"/></robot>',
    ):
        visit(source.get_launch_description(context))
    return processes


class VisualizationLaunchTest(unittest.TestCase):
    def test_sim_viewer_selection_and_single_model_publishers(self):
        for viewer in ('rviz', 'foxglove', 'none'):
            with self.subTest(viewer=viewer):
                processes = resolve_launch('sim', visualization=viewer)
                executables = [Path(cmd[0]).name for cmd, _ in processes]
                self.assertEqual(executables.count('rviz2'), int(viewer == 'rviz'))
                self.assertEqual(executables.count('foxglove_bridge'), int(viewer == 'foxglove'))
                self.assertEqual(executables.count('robot_state_publisher'), 2)
                self.assertEqual(executables.count('publish_joint_states'), 1)
                gazebo = [cmd for cmd, _ in processes if cmd[0] == 'gz']
                self.assertEqual(len(gazebo), 1)
                self.assertIn('-s', gazebo[0])
                for _, params in processes:
                    if 'use_sim_time' in params:
                        self.assertIs(params['use_sim_time'], True)

    def test_standalone_vehicle_clock_defaults(self):
        for viewer in ('rviz', 'foxglove'):
            for vehicle, clock in (('uuv00', True), ('uuv02', False)):
                with self.subTest(viewer=viewer, vehicle=vehicle):
                    processes = resolve_launch(viewer, vehicle_name=vehicle)
                    self.assertFalse(any(cmd[0] == 'gz' for cmd, _ in processes))
                    self.assertEqual(len(processes), 6 if viewer == 'foxglove' else 5)
                    for _, params in processes:
                        self.assertIs(params['use_sim_time'], clock)
                    prefixes = [p['frame_prefix'] for _, p in processes if 'frame_prefix' in p]
                    self.assertIn(f'{vehicle}/', prefixes)

    def test_attach_without_model_publishers(self):
        for viewer in ('rviz', 'foxglove'):
            with self.subTest(viewer=viewer):
                self.assertEqual(len(resolve_launch(viewer, publish_models='false')),
                                 2 if viewer == 'foxglove' else 1)

    def test_bag_playback_clock_override(self):
        for viewer in ('rviz', 'foxglove'):
            with self.subTest(viewer=viewer):
                processes = resolve_launch(
                    viewer, vehicle_name='uuv02', use_sim_time='true',
                    bag='/tmp/example-bag', bag_rate='0.5', bag_loop='true',
                )
                playback = [cmd for cmd, _ in processes if cmd[:3] == ['ros2', 'bag', 'play']]
                self.assertEqual(playback, [[
                    'ros2', 'bag', 'play', '/tmp/example-bag', '--clock', '--rate', '0.5', '--loop',
                ]])
                for _, params in processes:
                    if 'use_sim_time' in params:
                        self.assertIs(params['use_sim_time'], True)

    def test_sim_rejects_invalid_configuration(self):
        for args in ({'visualization': 'invalid'}, {'vehicle_name': 'uuv02'}, {'use_sim_time': 'false'}):
            with self.subTest(args=args), self.assertRaises(RuntimeError):
                resolve_launch('sim', **args)


if __name__ == '__main__':
    unittest.main()
