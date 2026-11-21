from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'patrolbot_world'

setup(
    name=package_name,
    version='1.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'worlds'),
            glob('worlds/*.world')),
        (os.path.join('share', package_name, 'launch'),
            glob('launch/*.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Youri Nkouakep',
    maintainer_email='yourinkouakep@gmail.com',
    description='Monde Gazebo urbain pour PatrolBot',
    license='MIT',
    entry_points={
        'console_scripts': [],
    },
)
