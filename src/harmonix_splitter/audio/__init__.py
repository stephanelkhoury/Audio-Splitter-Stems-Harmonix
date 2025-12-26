"""
Harmonix Audio Processing Module
High-quality audio manipulation, pitch shifting, and lyrics extraction
"""

from harmonix_splitter.audio.processor import (
    AudioProcessor,
    PitchShiftConfig,
    pitch_shift_audio
)

from harmonix_splitter.audio.lyrics import (
    LyricsExtractor,
    LyricsResult,
    LyricLine,
    KaraokeLyrics,
    extract_lyrics
)

__all__ = [
    'AudioProcessor',
    'PitchShiftConfig',
    'pitch_shift_audio',
    'LyricsExtractor',
    'LyricsResult',
    'LyricLine',
    'KaraokeLyrics',
    'extract_lyrics'
]
