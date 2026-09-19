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
    version='4.1.0',
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
    extras_require={
        # MIDI-out is optional: python-rtmidi is a C-extension package that
        # some environments can't build, and it's not needed unless you
        # actually check the "Send dominant frequency as MIDI" box. The GUI
        # detects its absence and disables the feature with a clear message
        # instead of failing to import at all.
        'midi': ['mido', 'python-rtmidi'],
    },
    license="Apache License 2.0",
    url="https://github.com/AdityaSeth777/Audio-SpectraCLI",
)
