from glob import glob
from setuptools import find_packages
from setuptools import setup

package_name = 'tools'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
         ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', glob('launch/*.launch.py')),
        ('share/' + package_name + '/config', glob('config/*.yaml')),
        ('share/' + package_name + '/rviz', glob('rviz/*')),
        ('share/' + package_name + '/plotjuggler',
         glob('plotjuggler/*.xml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Finn Breuer',
    maintainer_email='finn.breuer@tuhh.de',
    description='Run, logging, analysis, and RViz helpers for the workspace.',
    license='GPLv2',
    entry_points={
        'console_scripts': [
            'export_csv = tools.export_csv:main',
            'create_robot_description = tools.create_robot_description:main',
            'publish_joint_states = tools.publish_joint_states:main',
            'plot_depth = tools.plot_depth:main',
            'plot_navigation = tools.plot_navigation:main',
        ],
    },
)
