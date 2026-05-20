import os
from glob import glob

from setuptools import find_packages, setup

package_name = "nitrobot_decision"

setup(
    name=package_name,
    version="0.0.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        ("share/" + package_name + "/launch", ["launch/decision.launch.py"]),
        (os.path.join("lib", package_name), glob("scripts/*.sh")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="root",
    maintainer_email="root@todo.todo",
    description="NitroBot decision node",
    license="TODO: License declaration",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "nitrobot_decision_node = nitrobot_decision.nitrobot_decision_node:main",
        ],
    },
)
