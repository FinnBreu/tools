#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState


DEFAULT_JOINT_NAMES = [
    'port_top_thruster_hull_joint',
    'port_top_thruster_propeller_joint',
    'starboard_top_thruster_hull_joint',
    'starboard_top_thruster_propeller_joint',
    'starboard_bot_thruster_hull_joint',
    'starboard_bot_thruster_propeller_joint',
    'port_bot_thruster_hull_joint',
    'port_bot_thruster_propeller_joint',
]


class JointStatePublisher(Node):
    def __init__(self):
        super().__init__('joint_state_publisher')
        self.declare_parameter('joint_names', DEFAULT_JOINT_NAMES)
        self.declare_parameter('publish_rate', 10.0)

        self.joint_names = [
            str(name)
            for name in self.get_parameter('joint_names').value
        ]
        publish_rate = self.get_parameter('publish_rate').value

        self.publisher = self.create_publisher(JointState, 'joint_states', 10)
        self.timer = self.create_timer(1.0 / publish_rate, self._publish)

    def _publish(self):
        msg = JointState()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.name = self.joint_names
        msg.position = [0.0] * len(self.joint_names)
        self.publisher.publish(msg)


def main():
    rclpy.init()
    node = JointStatePublisher()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
