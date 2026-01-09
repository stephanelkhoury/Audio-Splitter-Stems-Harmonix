"""Harmonix core processing modules"""

# Lazy imports to avoid requiring torch for dashboard-only deployment
def __getattr__(name):
    if name == "HarmonixSeparator":
        from .separator import HarmonixSeparator
        return HarmonixSeparator
    elif name == "create_separator":
        from .separator import create_separator
        return create_separator
    elif name == "AudioPreprocessor":
        from .preprocessor import AudioPreprocessor
        return AudioPreprocessor
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = ["HarmonixSeparator", "create_separator", "AudioPreprocessor"]
