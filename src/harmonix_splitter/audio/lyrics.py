"""
Harmonix Lyrics Extractor
High-quality speech-to-text using OpenAI Whisper
Supports Arabic, English, French, and automatic language detection
"""

import logging
from pathlib import Path
from typing import Optional, List, Dict, Union, Tuple
from dataclasses import dataclass, field
import json
import re

logger = logging.getLogger(__name__)


@dataclass
class LyricLine:
    """Single line of lyrics with timing"""
    text: str
    start_time: float  # seconds
    end_time: float  # seconds
    confidence: float = 1.0
    words: List[Dict] = field(default_factory=list)  # Word-level timing
    
    def to_dict(self) -> Dict:
        return {
            'text': self.text,
            'start': self.start_time,
            'end': self.end_time,
            'confidence': self.confidence,
            'words': self.words
        }


@dataclass
class LyricsResult:
    """Complete lyrics extraction result"""
    text: str  # Full text
    lines: List[LyricLine]  # Timed lines
    language: str  # Detected/specified language
    language_confidence: float
    duration: float
    
    def to_lrc(self) -> str:
        """Convert to LRC format for karaoke"""
        lines = []
        for line in self.lines:
            mins = int(line.start_time // 60)
            secs = line.start_time % 60
            lines.append(f"[{mins:02d}:{secs:05.2f}]{line.text}")
        return '\n'.join(lines)
    
    def to_srt(self) -> str:
        """Convert to SRT subtitle format"""
        lines = []
        for i, line in enumerate(self.lines, 1):
            start = self._format_srt_time(line.start_time)
            end = self._format_srt_time(line.end_time)
            lines.append(f"{i}\n{start} --> {end}\n{line.text}\n")
        return '\n'.join(lines)
    
    def _format_srt_time(self, seconds: float) -> str:
        """Format time for SRT"""
        hrs = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hrs:02d}:{mins:02d}:{secs:06.3f}".replace('.', ',')
    
    def to_dict(self) -> Dict:
        return {
            'text': self.text,
            'lines': [line.to_dict() for line in self.lines],
            'language': self.language,
            'language_confidence': self.language_confidence,
            'duration': self.duration
        }


class LyricsExtractor:
    """
    Extract lyrics from audio using OpenAI Whisper
    Supports multiple languages with word-level timing
    """
    
    SUPPORTED_LANGUAGES = {
        'auto': None,  # Auto-detect
        'en': 'english',
        'ar': 'arabic',
        'fr': 'french',
        'es': 'spanish',
        'de': 'german',
        'it': 'italian',
        'pt': 'portuguese',
        'ru': 'russian',
        'ja': 'japanese',
        'ko': 'korean',
        'zh': 'chinese',
    }
    
    MODEL_SIZES = {
        'tiny': 'tiny',
        'base': 'base',
        'small': 'small',
        'medium': 'medium',
        'large': 'large-v3',  # Best quality
    }
    
    def __init__(
        self,
        model_size: str = "medium",
        device: Optional[str] = None
    ):
        """
        Initialize lyrics extractor
        
        Args:
            model_size: Whisper model size (tiny/base/small/medium/large)
            device: Device to use (cuda/cpu/auto)
        """
        self.model_size = self.MODEL_SIZES.get(model_size, model_size)
        self.device = device
        self.model = None
        self._loaded = False
        
    def _load_model(self):
        """Lazy load Whisper model"""
        if self._loaded:
            return
            
        try:
            import whisper
            
            logger.info(f"Loading Whisper model: {self.model_size}")
            
            # Determine device - prefer MPS (Apple Silicon) > CUDA > CPU
            if self.device is None:
                import torch
                if torch.cuda.is_available():
                    self.device = "cuda"
                elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                    # Note: Whisper may have issues with MPS, fallback to CPU if needed
                    try:
                        self.device = "cpu"  # MPS support in whisper is limited, use CPU for stability
                        logger.info("Using CPU for Whisper (MPS support is experimental)")
                    except Exception:
                        self.device = "cpu"
                else:
                    self.device = "cpu"
            
            self.model = whisper.load_model(self.model_size, device=self.device)
            self._loaded = True
            logger.info(f"Whisper model loaded on {self.device}")
            
        except ImportError:
            logger.error("Whisper not installed. Install with: pip install openai-whisper")
            raise ImportError("openai-whisper is required for lyrics extraction")
    
    def extract(
        self,
        audio_path: Union[str, Path],
        language: str = "auto",
        task: str = "transcribe",
        word_timestamps: bool = True
    ) -> LyricsResult:
        """
        Extract lyrics from audio file
        
        Args:
            audio_path: Path to audio file (preferably isolated vocals)
            language: Language code or 'auto' for detection
            task: 'transcribe' or 'translate' (to English)
            word_timestamps: Include word-level timing
            
        Returns:
            LyricsResult with timed lyrics
        """
        self._load_model()
        
        audio_path = Path(audio_path)
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        logger.info(f"Extracting lyrics from: {audio_path}")
        logger.info(f"Language: {language}, Task: {task}")
        
        # Prepare transcription options
        options = {
            'task': task,
            'word_timestamps': word_timestamps,
            'verbose': False,
        }
        
        # Set language if not auto
        if language != 'auto' and language in self.SUPPORTED_LANGUAGES:
            options['language'] = language
        
        # Transcribe
        result = self.model.transcribe(str(audio_path), **options)
        
        # Extract language info
        detected_language = result.get('language', language)
        
        # Process segments into lyrics lines
        lines = []
        for segment in result.get('segments', []):
            # Get word-level timing if available
            words = []
            if 'words' in segment:
                for word in segment['words']:
                    words.append({
                        'word': word.get('word', ''),
                        'start': word.get('start', 0),
                        'end': word.get('end', 0),
                        'confidence': word.get('probability', 1.0)
                    })
            
            line = LyricLine(
                text=segment.get('text', '').strip(),
                start_time=segment.get('start', 0),
                end_time=segment.get('end', 0),
                confidence=segment.get('no_speech_prob', 0),
                words=words
            )
            
            if line.text:  # Only add non-empty lines
                lines.append(line)
        
        # Get full text
        full_text = result.get('text', '').strip()
        
        # Get duration from last segment
        duration = lines[-1].end_time if lines else 0
        
        return LyricsResult(
            text=full_text,
            lines=lines,
            language=detected_language,
            language_confidence=1.0 - result.get('segments', [{}])[0].get('no_speech_prob', 0) if result.get('segments') else 0.5,
            duration=duration
        )
    
    def extract_from_vocals(
        self,
        vocals_path: Union[str, Path],
        language: str = "auto"
    ) -> LyricsResult:
        """
        Extract lyrics from isolated vocals (best quality)
        
        Args:
            vocals_path: Path to isolated vocals stem
            language: Language code or 'auto'
            
        Returns:
            LyricsResult with timed lyrics
        """
        return self.extract(vocals_path, language=language, word_timestamps=True)
    
    def save_lyrics(
        self,
        result: LyricsResult,
        output_dir: Union[str, Path],
        base_name: str,
        formats: List[str] = None
    ) -> Dict[str, Path]:
        """
        Save lyrics in multiple formats
        
        Args:
            result: LyricsResult to save
            output_dir: Output directory
            base_name: Base filename
            formats: List of formats ['txt', 'lrc', 'srt', 'json']
            
        Returns:
            Dictionary mapping format to output path
        """
        if formats is None:
            formats = ['txt', 'lrc', 'srt', 'json']
        
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        outputs = {}
        
        for fmt in formats:
            output_path = output_dir / f"{base_name}_lyrics.{fmt}"
            
            if fmt == 'txt':
                content = result.text
            elif fmt == 'lrc':
                content = result.to_lrc()
            elif fmt == 'srt':
                content = result.to_srt()
            elif fmt == 'json':
                content = json.dumps(result.to_dict(), indent=2, ensure_ascii=False)
            else:
                continue
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            outputs[fmt] = output_path
            logger.info(f"Saved lyrics to: {output_path}")
        
        return outputs


class KaraokeLyrics:
    """
    Specialized lyrics processor for karaoke display
    Provides word-by-word highlighting timing
    """
    
    def __init__(self, lyrics_result: LyricsResult):
        """
        Initialize karaoke lyrics
        
        Args:
            lyrics_result: LyricsResult from LyricsExtractor
        """
        self.result = lyrics_result
        self._build_word_timeline()
    
    def _build_word_timeline(self):
        """Build timeline of all words for karaoke highlighting"""
        self.word_timeline = []
        
        for line_idx, line in enumerate(self.result.lines):
            for word_idx, word in enumerate(line.words):
                self.word_timeline.append({
                    'line_idx': line_idx,
                    'word_idx': word_idx,
                    'word': word.get('word', ''),
                    'start': word.get('start', 0),
                    'end': word.get('end', 0),
                    'line_text': line.text
                })
    
    def get_current_word(self, time: float) -> Optional[Dict]:
        """
        Get the word that should be highlighted at given time
        
        Args:
            time: Current playback time in seconds
            
        Returns:
            Word info dict or None
        """
        for word in self.word_timeline:
            if word['start'] <= time <= word['end']:
                return word
        return None
    
    def get_current_line(self, time: float) -> Optional[LyricLine]:
        """
        Get the line that should be displayed at given time
        
        Args:
            time: Current playback time in seconds
            
        Returns:
            LyricLine or None
        """
        for line in self.result.lines:
            if line.start_time <= time <= line.end_time:
                return line
        return None
    
    def get_display_lines(self, time: float, window: int = 2) -> List[Dict]:
        """
        Get lines to display centered around current time
        
        Args:
            time: Current playback time
            window: Number of lines before/after current
            
        Returns:
            List of line dicts with timing info
        """
        current_idx = -1
        for i, line in enumerate(self.result.lines):
            if line.start_time <= time <= line.end_time:
                current_idx = i
                break
            elif line.start_time > time:
                current_idx = max(0, i - 1)
                break
        
        if current_idx == -1:
            current_idx = len(self.result.lines) - 1
        
        start_idx = max(0, current_idx - window)
        end_idx = min(len(self.result.lines), current_idx + window + 1)
        
        display_lines = []
        for i in range(start_idx, end_idx):
            line = self.result.lines[i]
            display_lines.append({
                'text': line.text,
                'start': line.start_time,
                'end': line.end_time,
                'is_current': i == current_idx,
                'progress': self._calculate_progress(line, time) if i == current_idx else 0,
                'words': line.words
            })
        
        return display_lines
    
    def _calculate_progress(self, line: LyricLine, time: float) -> float:
        """Calculate progress through current line (0-1)"""
        if time < line.start_time:
            return 0
        if time > line.end_time:
            return 1
        duration = line.end_time - line.start_time
        if duration <= 0:
            return 1
        return (time - line.start_time) / duration
    
    def to_karaoke_json(self) -> str:
        """
        Export to JSON format optimized for karaoke display
        """
        data = {
            'language': self.result.language,
            'duration': self.result.duration,
            'lines': []
        }
        
        for line in self.result.lines:
            line_data = {
                'text': line.text,
                'start': line.start_time,
                'end': line.end_time,
                'words': []
            }
            
            for word in line.words:
                line_data['words'].append({
                    'text': word.get('word', ''),
                    'start': word.get('start', 0),
                    'end': word.get('end', 0)
                })
            
            data['lines'].append(line_data)
        
        return json.dumps(data, indent=2, ensure_ascii=False)


def extract_lyrics(
    audio_path: Union[str, Path],
    language: str = "auto",
    model_size: str = "medium"
) -> LyricsResult:
    """
    Convenience function to extract lyrics
    
    Args:
        audio_path: Path to audio file
        language: Language code or 'auto'
        model_size: Whisper model size
        
    Returns:
        LyricsResult
    """
    extractor = LyricsExtractor(model_size=model_size)
    return extractor.extract(audio_path, language=language)
