"""
Harmonix Audio Splitter
High-fidelity AI-powered audio stem separation with instrument-level analysis.
"""

__version__ = "1.0.0"
__author__ = "Stephan El Khoury"

from .core.splitter import AudioSplitter
from .analysis.detector import InstrumentDetector
from .config.settings import get_settings

__all__ = ["AudioSplitter", "InstrumentDetector", "get_settings"]
