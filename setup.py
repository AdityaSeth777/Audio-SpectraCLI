from setuptools import setup, find_packages

setup(
    name='Audio_SpectraCLI',
    version='2.1',
    author="Aditya Seth",
    long_description=open('Readme.md').read(),
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
        'pyaudio'
    ],
    license="MIT",
    url="https://github.com/AdityaSeth777/Audio-SpectraCLI",
)
