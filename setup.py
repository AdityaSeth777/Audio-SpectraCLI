from setuptools import setup, find_packages

setup(
    name='Audio_SpectraCLI',
    version='0.2',
    description="""AudioSpectraCLI is a command-line tool that provides real-time FFT visualization of audio spectra. It captures audio input from the microphone and displays the corresponding frequency spectrum directly in the terminal window, allowing users to monitor and analyze audio signals without the need for graphical interfaces.""",
    author="Aditya Seth",
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
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
