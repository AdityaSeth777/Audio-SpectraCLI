import numpy as np
import matplotlib.pyplot as plt
import sounddevice as sd
import queue
import threading
import time

duration = 10
fs = 44100
block_size = 2048
num_blocks = int(duration * fs / block_size)

audio_queue = queue.Queue()


def audio_callback(indata, frames, time, status):
    if status:
        print(status)
    audio_queue.put(indata.copy())


def process_audio():
    freq_bins = np.fft.fftfreq(block_size, 1/fs)
    spectrum = np.zeros(block_size)

    plt.ion()
    fig, ax = plt.subplots()
    x = np.arange(0, block_size)
    line, = ax.plot(freq_bins, spectrum)
    ax.set_xlim(0, 5000)
    ax.set_ylim(0, 0.1)
    ax.set_xlabel('Frequency (Hz)')
    ax.set_ylabel('Magnitude')

    while True:
        audio_block = audio_queue.get()
        spectrum = np.abs(np.fft.fft(audio_block[:, 0], n=block_size))
        max_magnitude = np.max(spectrum)
        if max_magnitude > ax.get_ylim()[1]:
            ax.set_ylim(0, max_magnitude * 1.1)
        line.set_ydata(spectrum)
        fig.canvas.draw()
        fig.canvas.flush_events()


audio_thread = threading.Thread(target=process_audio, daemon=True)
audio_thread.start()

with sd.InputStream(callback=audio_callback, channels=1, samplerate=fs):
    while True:
        time.sleep(1)

audio_thread.join()
