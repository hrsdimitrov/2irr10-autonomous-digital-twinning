from setuptools import setup
import os
from glob import glob

package_name = 'nitrobot_sim'

setup(
    name=package_name,
    version='0.0.1',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'),
            glob('launch/*.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='mia',
    maintainer_email='mia@tue.nl',
    description='Nitrobot farm simulation',
    license='MIT',
    entry_points={
        'console_scripts': [
            'zone_state_node = nitrobot_sim.zone_state_node:main',
            'autonomous_decision = nitrobot_sim.autonomous_decision:main',
            'status_node = nitrobot_sim.status_node:main',
        ],
    },
)