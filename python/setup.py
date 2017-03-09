from setuptools import setup, find_packages

setup(
    name='grpcio-opentracing',
    version='1.0',
    description='Python OpenTracing Extensions for gRPC',
    long_description='',
    author='LightStep',
    license='',
    install_requires=[
        'opentracing>=1.2.2',
        'grpcio>=1.1.3',
        'six>=1.10'
    ],
    setup_requires=['pytest-runner'],
    tests_require=['pytest'],
    keywords=['opentracing'],
    classifiers=[
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
    ],
    packages=find_packages(exclude=['docs*', 'tests*', 'examples*'])
)
