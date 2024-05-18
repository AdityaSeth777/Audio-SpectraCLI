```
    _             _ _            ____                  _              ____ _     ___
   / \  _   _  __| (_) ___      / ___| _ __   ___  ___| |_ _ __ __ _ / ___| |   |_ _|
  / _ \| | | |/ _` | |/ _ \ ____\___ \| '_ \ / _ \/ __| __| '__/ _` | |   | |    | |
 / ___ \ |_| | (_| | | (_) |_____|__) | |_) |  __/ (__| |_| | | (_| | |___| |___ | |
/_/   \_\__,_|\__,_|_|\___/     |____/| .__/ \___|\___|\__|_|  \__,_|\____|_____|___|
                                      |_|
```

## Audio Spectrum Visualization is a Python project that visualizes real-time audio input as a spectrum using Fast Fourier Transform (FFT). It provides an interactive CLI interface for users to start the visualization and exit the program.

#### Notable point : From v4.0, I have implemented a whole new code using PyQt5, which you will find evident here in the new main default code - ['main.py'](./Audio_SpectraCLI/main.py) and the ['test.py'](./tests/test.py) case supporting that.

#### The ['main-old.py'](./Audio_SpectraCLI/main-old.py), which is the code for the main file for v3.2, and the ['test-old.py'](./tests/test-old.py) case supporting that, is DEPRECATED.

## Current Features (with respect to 4.0)

- Real-time visualization of Fast Fourier Transform (FFT) spectrum of audio input.
- Support for adjusting parameters such as duration, sampling rate, and block size.
- Seamless integration with SoundDevice for audio input capture.
- Customizable Frequency Range: Allow users to specify the frequency range to display in the spectrum.
- Color Customization: Provide options for users to customize the colors used in the spectrum visualization.
- Added PyQt5 modules that enables user input for Duration (in seconds), Sampling Rate (in Hz), and Block Size.
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

```
from Audio_SpectraCLI import AudioSpectrumVisualizer
from PyQt5.QtWidgets import QApplication

# Creating an instance of AudioSpectrumVisualizer with custom parameters
app = QApplication([])
audio_visualizer = AudioSpectrumVisualizer(
    duration=10, fs=22050, block_size=8192, frequency_range=(2000, 5000), color='green')

# Starting the audio spectrum visualization
audio_visualizer.show()
audio_visualizer.start_visualization()
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

```
from Audio_SpectraCLI import AudioSpectrumVisualizer
from PyQt5.QtWidgets import QApplication

# Creating an instance of AudioSpectrumVisualizer with custom parameters
app = QApplication([])
audio_visualizer = AudioSpectrumVisualizer(
    duration=10, fs=22050, block_size=8192, frequency_range=(2000, 5000), color='green')

# Starting the audio spectrum visualization
audio_visualizer.show()
audio_visualizer.start_visualization()
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

```
from Audio_SpectraCLI import AudioSpectrumVisualizer
from PyQt5.QtWidgets import QApplication

# Creating an instance of AudioSpectrumVisualizer with custom parameters
app = QApplication([])
audio_visualizer = AudioSpectrumVisualizer(
    duration=10, fs=22050, block_size=8192, frequency_range=(2000, 5000), color='green')

# Starting the audio spectrum visualization
audio_visualizer.show()
audio_visualizer.start_visualization()
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

Contact: [contact@adityaseth.in]

## 🙋‍♂️ Support

💙 If you like this project, give it a ⭐ and share it with friends!`<br><br>`
[☕ Buy me a coffee](https://www.buymeacoffee.com/adityaseth)

---

Made with ❤️
