from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

with open("requirements.txt") as f:
    required = f.read().splitlines()

setup(
    name='Audio_SpectraCLI',
    version='1.0',
    author="Aditya Seth",
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
