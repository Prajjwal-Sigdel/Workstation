from setuptools import setup, find_packages

setup(
    name='face_recognition_models',
    version='0.3.0',
    packages=find_packages(),
    package_data={
        'face_recognition_models': ['models/*.dat']
    },
)