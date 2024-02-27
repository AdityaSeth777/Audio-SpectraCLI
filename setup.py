from setuptools import setup, find_packages

setup(
    name='Audio_SpectraCLI',
    version='0.2',
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

)
