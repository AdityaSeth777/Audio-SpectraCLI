from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

with open("requirements.txt") as f:
    required = f.read().splitlines()

setup(
    name='Audio_SpectraCLI',
    version='1.0',
    author="Aditya Seth",
    description=""""AudioSpectraCLI is a command-line tool that provides real-time FFT visualization of audio spectra. It captures audio input from the microphone and displays the corresponding frequency spectrum directly in the terminal window, allowing users to monitor and analyze audio signals without the need for graphical interfaces.""",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=[
        'numpy',
        'matplotlib',
        'sounddevice',
        'tabulate',
        'setuptools',
        'twine',
        'wheel'
    ],
    license="MIT",
    url="https://github.com/AdityaSeth777/Audio-SpectraCLI",
)
