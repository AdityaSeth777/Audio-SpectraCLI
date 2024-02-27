from setuptools import setup, find_packages

setup(
    name='Audio_SpectraCLI',
    version='1.0',
    author="Aditya Seth",
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
