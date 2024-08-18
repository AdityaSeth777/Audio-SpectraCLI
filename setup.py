import os
from setuptools import setup, find_packages

this_directory = os.path.abspath(os.path.dirname(__file__))
try:
    with open(os.path.join(this_directory, 'Readme.md'), encoding='utf-8') as f:
        long_description = f.read()
except FileNotFoundError:
    long_description = 'Long description not found.'

setup(
    name='Audio_SpectraCLI',
    version='4.0.1',
    author="Aditya Seth",
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=find_packages(),
    install_requires=[
        'numpy',
        'matplotlib',
        'sounddevice',
        'tabulate',
        'setuptools',
        'twine',
        'wheel',
        'pyqt5',
        'scipy',
        'pyaudio'
    ],
    license="Apache License 2.0",
    url="https://github.com/AdityaSeth777/Audio-SpectraCLI",
)
