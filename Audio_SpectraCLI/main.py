import numpy as np
import matplotlib.pyplot as plt
import sounddevice as sd
import queue
import threading
import time


class AudioSpectrumVisualizer:
    def __init__(self, duration=10, fs=44100, block_size=2048, frequency_range=(20, 20000), color='blue'):
        self.duration = duration
        self.fs = fs
        self.block_size = block_size
        self.num_blocks = int(duration * fs / block_size)
        self.frequency_range = frequency_range
        self.color = color
        self.audio_queue = queue.Queue()

    def audio_callback(self, indata, frames, time, status):
        if status:
            print(status)
        self.audio_queue.put(indata.copy())

    def process_audio(self):
        freq_bins = np.fft.fftfreq(self.block_size, 1/self.fs)
        spectrum = np.zeros(self.block_size)

        plt.ion()
        fig, ax = plt.subplots()
        x = np.arange(0, self.block_size)
        line, = ax.plot(freq_bins, spectrum, color=self.color)
        ax.set_xlim(self.frequency_range)
        ax.set_ylim(0, 0.1)
        ax.set_xlabel('Frequency (Hz)')
        ax.set_ylabel('Magnitude')

        while True:
            audio_block = self.audio_queue.get()
            spectrum = np.abs(np.fft.fft(audio_block[:, 0], n=self.block_size))
            max_magnitude = np.max(spectrum)
            if max_magnitude > ax.get_ylim()[1]:
                ax.set_ylim(0, max_magnitude * 1.1)
            line.set_ydata(spectrum)
            fig.canvas.draw()
            fig.canvas.flush_events()

    def start_visualization(self):
        audio_thread = threading.Thread(target=self.process_audio, daemon=True)
        audio_thread.start()

        with sd.InputStream(callback=self.audio_callback, channels=1, samplerate=self.fs):
            while True:
                time.sleep(1)

        audio_thread.join()


# List of functions available for use:
__all__ = ['AudioSpectrumVisualizer']
