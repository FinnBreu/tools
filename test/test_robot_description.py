from pathlib import Path
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

from tools.create_robot_description import _mesh_paths_to_uris


class RobotDescriptionTest(unittest.TestCase):
    def test_mesh_uris_for_both_viewers(self):
        description = '''<robot name="test"><link name="base_link"><visual><geometry>
            <mesh filename="/opt/ros/jazzy/share/hippo_sim/models/hippo3/meshes/tube.dae"/>
            <mesh filename="package://another_package/mesh.dae"/>
            <mesh filename="/tmp/custom mesh.dae"/>
            </geometry></visual></link></robot>'''
        with patch('tools.create_robot_description.get_package_share_path', return_value=Path(
            '/opt/ros/jazzy/share/hippo_sim',
        )):
            root = ET.fromstring(_mesh_paths_to_uris(description))
        self.assertEqual([mesh.get('filename') for mesh in root.iter('mesh')], [
            'package://hippo_sim/models/hippo3/meshes/tube.dae',
            'package://another_package/mesh.dae',
            'file:///tmp/custom%20mesh.dae',
        ])


if __name__ == '__main__':
    unittest.main()
