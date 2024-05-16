```
    _             _ _            ____                  _              ____ _     ___
   / \  _   _  __| (_) ___      / ___| _ __   ___  ___| |_ _ __ __ _ / ___| |   |_ _|
  / _ \| | | |/ _` | |/ _ \ ____\___ \| '_ \ / _ \/ __| __| '__/ _` | |   | |    | |
 / ___ \ |_| | (_| | | (_) |_____|__) | |_) |  __/ (__| |_| | | (_| | |___| |___ | |
/_/   \_\__,_|\__,_|_|\___/     |____/| .__/ \___|\___|\__|_|  \__,_|\____|_____|___|
                                      |_|
```

Audio Spectrum Visualization is a Python project that visualizes real-time audio input as a spectrum using Fast Fourier Transform (FFT). It provides an interactive CLI interface for users to start the visualization and exit the program.

## Current Features (with respect to 3.2)

- Real-time visualization of Fast Fourier Transform (FFT) spectrum of audio input.
- Support for adjusting parameters such as duration, sampling rate, and block size.
- Seamless integration with SoundDevice for audio input capture.
- Customizable Frequency Range: Allow users to specify the frequency range to display in the spectrum.
- Color Customization: Provide options for users to customize the colors used in the spectrum visualization.

## Packaging

```
Audio-SpectraCLI/

│   CODE_OF_CONDUCT.md
│   Contributing.md
│   Dockerfile
│   LICENSE
│   Readme.md
│   requirements.txt
│   setup.cfg
│   setup.py
│
├───.github
│   └───workflows
│           python-publish.yml
│
├───Audio_SpectraCLI
│       main.py
│       __init__.py
│
└───tests
        main.py
```

## Installation Types:

├───Using PIP <br>
├───Using Docker <br>
└───Using Docker locally <br>

## Installation & Usage (Using PIP)

1. Install using pip

```
pip install Audio-SpectraCLI
```

2. Import and use modules

- Create a Python file.
- You can use [Example.py](https://github.com/AdityaSeth777/Audio-SpectraCLI/blob/main/tests/main.py) as a reference or use the following code :

```
from Audio_SpectraCLI import AudioSpectrumVisualizer

# Creating an instance of AudioSpectrumVisualizer with custom parameters.
audio_visualizer = AudioSpectrumVisualizer(
    duration=5, frequency_range=(50, 5000), color='red')

# Starting the audio spectrum visualization
audio_visualizer.start_visualization()
```

Once you have activated the audio_visualizer instance, feel free to use it wherever in the program. It consists of several parameters (which gives more control to the user), so make sure to configure and add those before using it in your code.

---

## Installation & Usage (Using Docker)

1. Prerequisites
   You should have docker installed on your machine. You can download and install Docker from [here](https://www.docker.com/products/docker-desktop).
2. Pulling the Docker Image

You can pull the pre-built Docker image from Docker Hub using the following command:

```sh
docker pull adityaseth777/audio-spectra-cli
```

3. Running the Docker Container
   To run the Docker container, use the following command:

```
docker run --rm -it adityaseth777/audio-spectra-cli:latest
```

4. You can use [Example.py](https://github.com/AdityaSeth777/Audio-SpectraCLI/blob/main/tests/main.py) as a reference or use the following code :

```
from Audio_SpectraCLI import AudioSpectrumVisualizer

# Creating an instance of AudioSpectrumVisualizer with custom parameters.
audio_visualizer = AudioSpectrumVisualizer(
    duration=5, frequency_range=(50, 5000), color='red')

# Starting the audio spectrum visualization
audio_visualizer.start_visualization()
```

Once you have activated the audio_visualizer instance, feel free to use it wherever in the program. It consists of several parameters (which gives more control to the user), so make sure to configure and add those before using it in your code.

---

## Building the Docker Image Locally

If you prefer to build the Docker image locally, follow these steps:

1. Clone the repository :

```sh
git clone https://github.com/AdityaSeth777/Audio-SpectraCLI.git
cd Audio-SpectraCLI
```

2. Build the Docker image:

```sh
docker build -t audio-spectra-cli .
```

3. Run the Docker container:

```sh
docker run --rm -it audio-spectra-cli
```

4. You can use [Example.py](https://github.com/AdityaSeth777/Audio-SpectraCLI/blob/main/tests/main.py) as a reference or use the following code :

```
from Audio_SpectraCLI import AudioSpectrumVisualizer

# Creating an instance of AudioSpectrumVisualizer with custom parameters.
audio_visualizer = AudioSpectrumVisualizer(
    duration=5, frequency_range=(50, 5000), color='red')

# Starting the audio spectrum visualization
audio_visualizer.start_visualization()
```

Once you have activated the audio_visualizer instance, feel free to use it wherever in the program. It consists of several parameters (which gives more control to the user), so make sure to configure and add those before using it in your code.

## Upcoming Features

- CLI endpoints.
- Option to choose between CLI/GUI.
- Save and Export: Implement functionality to save the generated spectrum as an image file or export data for further analysis.
- Additional Audio Effects: Integrate additional audio effects or processing options to enhance the visualization.

---

## For contributing

Check the [Contributing page.](https://github.com/AdityaSeth777/Audio-SpectraCLI/blob/main/Contributing.md)
Make sure to PR your changes in the development branch.

## .env file

This file contains various environment variables that you can configure.

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
