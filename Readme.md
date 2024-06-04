```
    _             _ _            ____                  _              ____ _     ___
   / \  _   _  __| (_) ___      / ___| _ __   ___  ___| |_ _ __ __ _ / ___| |   |_ _|
  / _ \| | | |/ _` | |/ _ \ ____\___ \| '_ \ / _ \/ __| __| '__/ _` | |   | |    | |
 / ___ \ |_| | (_| | | (_) |_____|__) | |_) |  __/ (__| |_| | | (_| | |___| |___ | |
/_/   \_\__,_|\__,_|_|\___/     |____/| .__/ \___|\___|\__|_|  \__,_|\____|_____|___|
                                      |_|
```

## Audio Spectrum Visualization is a Python project that visualizes real-time audio input as a spectrum using Fast Fourier Transform (FFT). It provides an interactive and dynamic interface for users to start the visualization and exit the program.

 <p>

![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat)
[![Visitors](https://api.visitorbadge.io/api/visitors?path=https%3A%2F%2Fgithub.com%2FAdityaSeth777%2FAudio-SpectraCLI&label=Visitors&countColor=%23263759&style=plastic)](https://visitorbadge.io/status?path=https%3A%2F%2Fgithub.com%2FAdityaSeth777%2FAudio-SpectraCLI)
![GitHub forks](https://img.shields.io/github/forks/AdityaSeth777/Audio-SpectraCLI)
![GitHub Repo stars](https://img.shields.io/github/stars/AdityaSeth777/Audio-SpectraCLI)
![GitHub last commit](https://img.shields.io/github/last-commit/AdityaSeth777/Audio-SpectraCLI)
![GitHub repo size](https://img.shields.io/github/repo-size/AdityaSeth777/Audio-SpectraCLI)
![GitHub issues](https://img.shields.io/github/issues/AdityaSeth777/Audio-SpectraCLI)
![GitHub closed issues](https://img.shields.io/github/issues-closed-raw/AdityaSeth777/Audio-SpectraCLI)
![GitHub pull requests](https://img.shields.io/github/issues-pr/AdityaSeth777/Audio-SpectraCLI)
![GitHub closed pull requests](https://img.shields.io/github/issues-pr-closed/AdityaSeth777/Audio-SpectraCLI)

 </p>

<a href="https://www.producthunt.com/posts/audio-spectracli?utm_source=badge-featured&utm_medium=badge&utm_souce=badge-audio&#0045;spectracli" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/featured.svg?post_id=458166&theme=light" alt="Audio&#0045;SpectraCLI - Visualizing&#0032;real&#0045;time&#0032;audio&#0032;input&#0032;as&#0032;a&#0032;spectrum&#0032;using&#0032;FFT | Product Hunt" style="width: 250px; height: 54px;" width="250" height="54" /></a>

### Notable point : From v4.0, I have implemented a whole new code using PyQt5, which you will find evident here in the new main default code - [&#39;main.py&#39;](./Audio_SpectraCLI/main.py) and the [&#39;test.py&#39;](./tests/test.py) case supporting that.

### The [&#39;main-old.py&#39;](./Audio_SpectraCLI/main-old.py), which is the code for the main file for v3.2, and the [&#39;test-old.py&#39;](./tests/test-old.py) case supporting that, is DEPRECATED.

## Current Features (with respect to 4.0.1)

- Real-time visualization of Fast Fourier Transform (FFT) spectrum of audio input.
- Support for adjusting parameters such as duration, sampling rate, and block size.
- Seamless integration with SoundDevice for audio input capture.
- Customizable Frequency Range: Allow users to specify the frequency range to display in the spectrum.
- Color Customization: Provide options for users to customize the colors used in the spectrum visualization.
- Added PyQt5 modules and a Gaussian filter that enables user input for Duration (in seconds), Sampling Rate (in Hz), Block Size, and also smoothens the output.
- Might need to keep in mind that the Gaussian filter is too strong and it won't recognise any noise and display it's spectra. Only actual input through mic such as conversations and music are displayed which can be categorised as real inputs or audio, and of course in real time.
- Much more dynamic and user-controlled interface.

## Packaging

```
Audio-SpectraCLI/

├── .gitignore
├── CODE_OF_CONDUCT.md
├── Contributing.md
├── Dockerfile
├── LICENSE
├── Readme.md
├── requirements.txt
├── setup.cfg
├── setup.py
├── .github/
│   └── workflows/
│       ├── docker-publish.yml
│       ├── label.yml
│       └── python-publish.yml
├── Audio_SpectraCLI/
│   ├── main-old.py
│   ├── main.py
│   └── __init__.py
└── tests/
    ├── test-old.py
    └── test.py
```

## Installation & Usage (Using PIP)

1. Install using pip

```
pip install Audio-SpectraCLI
```

2. Import and use modules

- Create a Python file.
- You can use [Example.py](https://github.com/AdityaSeth777/Audio-SpectraCLI/blob/main/tests/test.py) as a reference or use the following code :

```python
from Audio_SpectraCLI import AudioSpectrumVisualizer
from PyQt5.QtWidgets import QApplication

# Creating an instance of AudioSpectrumVisualizer with custom parameters
app = QApplication([])
audio_visualizer = AudioSpectrumVisualizer(
    duration=5, fs=22050, block_size=1024, frequency_range=(1000, 5000), color='red')

# Starting the audio spectrum visualization
audio_visualizer.show()
app.exec_()
```

Once you have activated the audio_visualizer instance, feel free to use it wherever in the program. It consists of several parameters (which gives more control to the user), so make sure to configure and add those before using it in your code. Also, the user can modify (wrt [v4.0](https://github.com/AdityaSeth777/Audio-SpectraCLI/tree/4.0)) the Duration (in seconds), Sampling Rate (in Hz), and Block Size.

---

## Examining & Usage for fun :D (Using Docker)

1. Prerequisites
   You should have docker installed on your machine. You can download and install Docker from [here](https://www.docker.com/products/docker-desktop).
2. Pulling the Docker Image

You can pull the pre-built Docker image from Docker Hub using the following command:

```sh
docker pull adityaseth777/audio-spectracli
```

3. Viewing Files Inside the Docker Container
   For seeing the files inside the Docker container for debugging purposes, you can run an interactive shell session:

```sh
docker run --rm -it --entrypoint /bin/bash audio-spectracli
```

4. Use the 'ls' command to view the files and get a proper understanding of the file structure :

```sh
ls
```

5. You can use [Example.py](https://github.com/AdityaSeth777/Audio-SpectraCLI/blob/main/tests/test.py) as a reference or use the following code :

```python
from Audio_SpectraCLI import AudioSpectrumVisualizer
from PyQt5.QtWidgets import QApplication

# Creating an instance of AudioSpectrumVisualizer with custom parameters
app = QApplication([])
audio_visualizer = AudioSpectrumVisualizer(
    duration=5, fs=22050, block_size=1024, frequency_range=(1000, 5000), color='red')

# Starting the audio spectrum visualization
audio_visualizer.show()
app.exec_()
```

Once you have activated the audio_visualizer instance, feel free to use it wherever in the program. It consists of several parameters (which gives more control to the user), so make sure to configure and add those before using it in your code. Also, the user can modify (wrt [v4.0](https://github.com/AdityaSeth777/Audio-SpectraCLI/tree/4.0)) the Duration (in seconds), Sampling Rate (in Hz), and Block Size.

---

## Building the Docker Image Locally (for fun :D)

If you prefer to build the Docker image locally, follow these steps:

1. Clone the repository :

```sh
git clone https://github.com/AdityaSeth777/Audio-SpectraCLI.git
cd Audio-SpectraCLI
```

2. Build the Docker image:

```sh
docker build -t audio-spectracli .
```

3. Viewing Files Inside the Docker Container
   For seeing the files inside the Docker container for debugging purposes, you can run an interactive shell session:

```sh
docker run --rm -it --entrypoint /bin/bash audio-spectracli
```

4. Use the 'ls' command to view the files and get a proper understanding of the file structure :

```sh
ls
```

5. You can use [Example.py](https://github.com/AdityaSeth777/Audio-SpectraCLI/blob/main/tests/test.py) as a reference or use the following code :

```python
from Audio_SpectraCLI import AudioSpectrumVisualizer
from PyQt5.QtWidgets import QApplication

# Creating an instance of AudioSpectrumVisualizer with custom parameters
app = QApplication([])
audio_visualizer = AudioSpectrumVisualizer(
    duration=5, fs=22050, block_size=1024, frequency_range=(1000, 5000), color='red')

# Starting the audio spectrum visualization
audio_visualizer.show()
app.exec_()
```

Once you have activated the audio_visualizer instance, feel free to use it wherever in the program. It consists of several parameters (which gives more control to the user), so make sure to configure and add those before using it in your code. Also, the user can modify (wrt [v4.0](https://github.com/AdityaSeth777/Audio-SpectraCLI/tree/4.0)) the Duration (in seconds), Sampling Rate (in Hz), and Block Size.

## Upcoming Features

- Save and Export: Implement functionality to save the generated spectrum as an image file or export data for further analysis.
- CLI endpoints.
- Option to choose between CLI/GUI.

---

## For contributing

Check the [Contributing page.](https://github.com/AdityaSeth777/Audio-SpectraCLI/blob/main/Contributing.md)

## License

[MIT © Aditya Seth](https://github.com/AdityaSeth777/Audio-SpectraCLI/blob/main/LICENSE)

## What next?

I will be improving this project.

## Where to contact ?

Contact: [contact@adityaseth.in](mailto:contact@adityaseth.in?subject=Email%20owing%20to%20adityaseth.in&body=Greetings%2C%0AI%20am%20%5Bname%5D.%20I%20just%20came%20across%20your%20website%20and%20was%20hoping%20to%20talk%20to%20you%20about%20something.)

## 🙋‍♂️ Support

💙 If you like this project, give it a ⭐ and share it with friends! <br><br>

[<img width="200" height="70" src="https://i.postimg.cc/R0cqPmDf/bmc-button.png" alt="buymeacoffee">](https://www.buymeacoffee.com/adityaseth)

---

# Made with <img width="40" height="40" src="https://img.icons8.com/clouds/100/love-circled.png" alt="love-circled"/> and <img width="40" height="40" src="https://img.icons8.com/clouds/100/python.png" alt="python"/>
