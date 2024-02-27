from setuptools import setup, find_packages

setup(
    name='Audio_SpectraCLI',
    version='0.1',
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

)
