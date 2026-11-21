from setuptools import find_packages, setup

package_name = 'patrolbot_ai'

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
    description='Planificateur multicritère (distance, temps, obstacles, risque, énergie)',
    license='MIT',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'ai_planner = patrolbot_ai.ai_planner_node:main',
        ],
    },
)
