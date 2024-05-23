from Audio_SpectraCLI import AudioSpectrumVisualizer

# Create an instance of AudioSpectrumVisualizer with custom parameters
audio_visualizer = AudioSpectrumVisualizer(
    duration=5, frequency_range=(50, 5000), color='red')

# Start the audio spectrum visualization
audio_visualizer.start_visualization()
