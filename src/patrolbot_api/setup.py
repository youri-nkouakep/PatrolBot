from setuptools import find_packages, setup

package_name = 'patrolbot_api'

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
    description='API REST et WebSocket (FastAPI) pour piloter les missions de livraison',
    license='MIT',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'api_server = patrolbot_api.api_server_node:main',
        ],
    },
)
