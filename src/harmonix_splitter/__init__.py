"""
Harmonix Audio Splitter
High-fidelity AI-powered audio stem separation with instrument-level analysis.
"""

__version__ = "1.0.0"
__author__ = "Stephan El Khoury"

# Lazy imports to avoid requiring torch/ML libs for dashboard-only deployment
def __getattr__(name):
    if name == "HarmonixSeparator":
        from .core.separator import HarmonixSeparator
        return HarmonixSeparator
    elif name == "InstrumentDetector":
        from .analysis.detector import InstrumentDetector
        return InstrumentDetector
    elif name == "get_settings":
        from .config.settings import get_settings
        return get_settings
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = ["HarmonixSeparator", "InstrumentDetector", "get_settings"]
