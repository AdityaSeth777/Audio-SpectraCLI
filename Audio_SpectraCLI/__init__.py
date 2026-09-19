# __init__.py

# AudioSpectrumVisualizer (main.py) depends on PyQt5, but engine.py is meant
# to be usable standalone (e.g. by headless.py) without that dependency.
# Lazy attribute access keeps `from Audio_SpectraCLI import AudioSpectrumVisualizer`
# working for GUI use without forcing PyQt5 to be installed for headless use.


def __getattr__(name):
    if name == "AudioSpectrumVisualizer":
        from .main import AudioSpectrumVisualizer

        return AudioSpectrumVisualizer
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
