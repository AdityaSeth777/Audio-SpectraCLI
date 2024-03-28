from setuptools import setup, find_packages

setup(
    name='Audio_SpectraCLI',
    version='3.0',
    author="Aditya Seth",
    long_description=open('Readme.md', encoding='utf-8').read(),
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
