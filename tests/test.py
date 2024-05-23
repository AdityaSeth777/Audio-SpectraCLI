from Audio_SpectraCLI import AudioSpectrumVisualizer
from PyQt5.QtWidgets import QApplication

# Creating an instance of AudioSpectrumVisualizer with custom parameters
app = QApplication([])
audio_visualizer = AudioSpectrumVisualizer(
    duration=5, fs=22050, block_size=1024, frequency_range=(1000, 5000), color='red')

# Starting the audio spectrum visualization
audio_visualizer.show()
app.exec_()
