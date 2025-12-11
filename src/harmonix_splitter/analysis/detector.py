"""Instrument detection and analysis module."""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import librosa
import numpy as np
import tensorflow as tf
from scipy import signal

logger = logging.getLogger(__name__)


class InstrumentDetector:
    """
    Analyzes audio to detect instruments and route processing.
    
    This module performs multi-label instrument classification and
    determines which instruments are present in the mix.
    """
    
    SUPPORTED_INSTRUMENTS = [
        "vocals",
        "drums",
        "bass",
        "guitar",
        "piano",
        "strings",
        "synth",
        "brass",
        "woodwinds",
        "fx"
    ]
    
    def __init__(
        self,
        model_path: Optional[Path] = None,
        thresholds: Optional[Dict[str, float]] = None,
        sample_rate: int = 44100,
        analysis_duration: int = 30
    ):
        """
        Initialize the instrument detector.
        
        Args:
            model_path: Path to the trained classifier model
            thresholds: Confidence thresholds per instrument
            sample_rate: Target sample rate for analysis
            analysis_duration: Seconds of audio to analyze
        """
        self.model_path = model_path
        self.sample_rate = sample_rate
        self.analysis_duration = analysis_duration
        
        # Default thresholds
        self.thresholds = thresholds or {
            "vocals": 0.5,
            "drums": 0.5,
            "bass": 0.5,
            "guitar": 0.5,
            "piano": 0.5,
            "strings": 0.6,
            "synth": 0.7,
            "brass": 0.65,
            "woodwinds": 0.65,
            "fx": 0.7
        }
        
        # Load model if available
        self.model = None
        if model_path and model_path.exists():
            try:
                self.model = tf.keras.models.load_model(model_path)
                logger.info(f"Loaded instrument detection model from {model_path}")
            except Exception as e:
                logger.warning(f"Could not load model: {e}. Using fallback analysis.")
    
    def analyze(self, audio_path: Path) -> Dict[str, float]:
        """
        Analyze audio file and return instrument confidence scores.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Dictionary mapping instrument names to confidence scores (0-1)
        """
        logger.info(f"Analyzing audio: {audio_path}")
        
        # Load audio
        y, sr = librosa.load(
            audio_path,
            sr=self.sample_rate,
            duration=self.analysis_duration,
            mono=False
        )
        
        # Convert to mono if stereo
        if y.ndim == 2:
            y = librosa.to_mono(y)
        
        # Extract features
        features = self._extract_features(y, sr)
        
        # Get predictions
        if self.model:
            scores = self._predict_with_model(features)
        else:
            scores = self._fallback_detection(features, y, sr)
        
        logger.info(f"Detection scores: {scores}")
        return scores
    
    def detect_instruments(
        self,
        audio_path: Path,
        mode: str = "grouped"
    ) -> Tuple[List[str], Dict[str, float]]:
        """
        Detect which instruments are present above threshold.
        
        Args:
            audio_path: Path to audio file
            mode: 'grouped' for 4-stem or 'per_instrument' for individual
            
        Returns:
            Tuple of (detected_instruments, confidence_scores)
        """
        scores = self.analyze(audio_path)
        
        if mode == "grouped":
            # Always return core 4-stem instruments
            detected = ["vocals", "drums", "bass", "other"]
        else:
            # Return instruments above threshold
            detected = [
                inst for inst, score in scores.items()
                if score >= self.thresholds.get(inst, 0.5)
            ]
            
            # Always include vocals, drums, bass if detected at all
            for core_inst in ["vocals", "drums", "bass"]:
                if scores.get(core_inst, 0) > 0.3 and core_inst not in detected:
                    detected.append(core_inst)
        
        return detected, scores
    
    def _extract_features(self, y: np.ndarray, sr: int) -> Dict[str, np.ndarray]:
        """Extract audio features for classification."""
        features = {}
        
        # Mel spectrogram
        mel_spec = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=128)
        features["mel_spec"] = librosa.power_to_db(mel_spec, ref=np.max)
        
        # MFCC
        features["mfcc"] = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=20)
        
        # Spectral features
        features["spectral_centroid"] = librosa.feature.spectral_centroid(y=y, sr=sr)
        features["spectral_bandwidth"] = librosa.feature.spectral_bandwidth(y=y, sr=sr)
        features["spectral_rolloff"] = librosa.feature.spectral_rolloff(y=y, sr=sr)
        
        # Zero crossing rate
        features["zcr"] = librosa.feature.zero_crossing_rate(y)
        
        # Chroma features
        features["chroma"] = librosa.feature.chroma_stft(y=y, sr=sr)
        
        # Harmonic-percussive separation
        y_harmonic, y_percussive = librosa.effects.hpss(y)
        features["harmonic_ratio"] = np.mean(np.abs(y_harmonic)) / (
            np.mean(np.abs(y)) + 1e-8
        )
        features["percussive_ratio"] = np.mean(np.abs(y_percussive)) / (
            np.mean(np.abs(y)) + 1e-8
        )
        
        # Onset detection
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        features["onset_density"] = len(librosa.onset.onset_detect(
            onset_envelope=onset_env, sr=sr
        )) / (len(y) / sr)
        
        return features
    
    def _predict_with_model(self, features: Dict[str, np.ndarray]) -> Dict[str, float]:
        """Use trained model for prediction."""
        # Prepare input for model
        # This is a placeholder - actual implementation depends on model architecture
        mel_spec = features["mel_spec"]
        
        # Reshape for model input
        input_data = np.expand_dims(mel_spec, axis=0)
        
        # Get predictions
        predictions = self.model.predict(input_data, verbose=0)[0]
        
        # Map to instrument names
        scores = {
            inst: float(predictions[i])
            for i, inst in enumerate(self.SUPPORTED_INSTRUMENTS[:len(predictions)])
        }
        
        return scores
    
    def _fallback_detection(
        self,
        features: Dict[str, np.ndarray],
        y: np.ndarray,
        sr: int
    ) -> Dict[str, float]:
        """
        Fallback detection using heuristics when model not available.
        
        This uses spectral and temporal features to estimate instrument presence.
        """
        scores = {}
        
        # Vocals detection (high spectral centroid, harmonic content)
        vocal_score = 0.0
        if features["harmonic_ratio"] > 0.6:
            centroid_mean = np.mean(features["spectral_centroid"])
            if 1000 < centroid_mean < 4000:
                vocal_score = min(0.8, features["harmonic_ratio"])
        scores["vocals"] = vocal_score
        
        # Drums detection (high percussive content, high onset density)
        drum_score = min(1.0, features["percussive_ratio"] * 1.5)
        if features["onset_density"] > 5:
            drum_score = min(1.0, drum_score * 1.2)
        scores["drums"] = drum_score
        
        # Bass detection (low frequency energy)
        bass_spec = np.abs(librosa.stft(y))[:20, :]  # Low frequency bins
        bass_energy = np.mean(bass_spec)
        scores["bass"] = min(1.0, bass_energy * 2.0)
        
        # Guitar detection (moderate spectral centroid, harmonic)
        guitar_score = 0.0
        if features["harmonic_ratio"] > 0.5:
            centroid_mean = np.mean(features["spectral_centroid"])
            if 500 < centroid_mean < 2000:
                guitar_score = 0.6
        scores["guitar"] = guitar_score
        
        # Piano detection (high harmonic content, chromatic features)
        chroma_std = np.std(features["chroma"])
        piano_score = 0.0
        if features["harmonic_ratio"] > 0.7 and chroma_std > 0.3:
            piano_score = 0.5
        scores["piano"] = piano_score
        
        # Strings detection (very harmonic, sustained)
        strings_score = 0.0
        if features["harmonic_ratio"] > 0.8 and features["onset_density"] < 3:
            strings_score = 0.4
        scores["strings"] = strings_score
        
        # Synth detection (variable spectral content)
        bandwidth_std = np.std(features["spectral_bandwidth"])
        synth_score = min(0.7, bandwidth_std / 1000.0) if bandwidth_std > 500 else 0.0
        scores["synth"] = synth_score
        
        # Brass/Woodwinds (mid-high harmonic content)
        scores["brass"] = 0.0
        scores["woodwinds"] = 0.0
        
        # FX (noise, complex spectrum)
        scores["fx"] = 0.0
        
        return scores
    
    def get_routing_plan(
        self,
        detected_instruments: List[str],
        mode: str = "grouped"
    ) -> Dict[str, any]:
        """
        Create a processing routing plan based on detected instruments.
        
        Args:
            detected_instruments: List of detected instrument names
            mode: Processing mode
            
        Returns:
            Routing plan with stages and targets
        """
        plan = {
            "mode": mode,
            "stages": [],
            "target_stems": []
        }
        
        if mode == "grouped":
            # Stage 1: Core 4-stem separation
            plan["stages"].append({
                "name": "primary_separation",
                "model": "htdemucs",
                "outputs": ["vocals", "drums", "bass", "other"]
            })
            plan["target_stems"] = ["vocals", "drums", "bass", "other"]
        
        else:  # per_instrument
            # Stage 1: Core separation
            plan["stages"].append({
                "name": "primary_separation",
                "model": "htdemucs",
                "outputs": ["vocals", "drums", "bass", "other"]
            })
            
            # Stage 2: Instrument refinement from "other"
            refinement_targets = [
                inst for inst in detected_instruments
                if inst not in ["vocals", "drums", "bass"]
            ]
            
            if refinement_targets:
                plan["stages"].append({
                    "name": "instrument_refinement",
                    "input": "other",
                    "targets": refinement_targets
                })
            
            plan["target_stems"] = detected_instruments
        
        return plan
