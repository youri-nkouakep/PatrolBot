from setuptools import find_packages, setup

package_name = 'patrolbot_perception'

setup(
    name=package_name,
    version='1.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Youri Nkouakep',
    maintainer_email='yourinkouakep@gmail.com',
    description='Densité d\'obstacles par secteur à partir du LiDAR',
    license='MIT',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'obstacle_detector = patrolbot_perception.obstacle_detector_node:main',
        ],
    },
)
