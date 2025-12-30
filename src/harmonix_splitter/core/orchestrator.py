"""
Harmonix Orchestrator
Routes audio through analysis and separation pipelines
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Union
from dataclasses import dataclass
import time

from ..analysis.detector import InstrumentDetector
from ..core.separator import HarmonixSeparator, SeparationConfig, QualityMode, SeparationMode
from ..core.preprocessor import AudioPreprocessor
from ..config.settings import Settings

logger = logging.getLogger(__name__)


@dataclass
class ProcessingResult:
    """Result from complete processing pipeline"""
    job_id: str
    status: str
    stems: Dict[str, any]
    detected_instruments: List[str]
    instrument_scores: Dict[str, float]
    processing_time: float
    metadata: Dict


class HarmonixOrchestrator:
    """
    Orchestrates the complete audio processing pipeline:
    1. Preprocessing & validation
    2. Instrument detection & analysis
    3. Routing decision
    4. Stem separation
    5. Post-processing & export
    """
    
    def __init__(
        self,
        settings: Optional[Settings] = None,
        auto_route: bool = True
    ):
        """
        Initialize orchestrator
        
        Args:
            settings: Application settings
            auto_route: Automatically select best routing based on analysis
        """
        self.settings = settings or Settings()
        self.auto_route = auto_route
        
        # Initialize components
        self.preprocessor = AudioPreprocessor(
            target_sr=self.settings.sample_rate,
            max_duration=self.settings.max_duration
        )
        self.detector = InstrumentDetector(
            thresholds=self.settings.detection_thresholds
        )
        
        logger.info("Harmonix Orchestrator initialized")
    
    def process(
        self,
        audio_path: Union[str, Path],
        job_id: str,
        quality: Optional[str] = None,
        mode: Optional[str] = None,
        target_instruments: Optional[List[str]] = None,
        output_dir: Optional[Union[str, Path]] = None,
        custom_name: Optional[str] = None
    ) -> ProcessingResult:
        """
        Process audio file through complete pipeline
        
        Args:
            audio_path: Path to input audio
            job_id: Unique job identifier
            quality: Quality mode (fast/balanced/studio)
            mode: Separation mode (grouped/per_instrument)
            target_instruments: Specific instruments to extract
            output_dir: Output directory for stems
            
        Returns:
            ProcessingResult with all outputs and metadata
        """
        audio_path = Path(audio_path)
        start_time = time.time()
        
        logger.info(f"[{job_id}] Starting orchestration for: {audio_path.name}")
        
        try:
            # Stage 1: Validation & Preprocessing
            logger.info(f"[{job_id}] Stage 1: Validation")
            validation = self.preprocessor.validate_audio(audio_path)
            
            if not validation[0]:
                raise ValueError(f"Invalid audio: {validation[1]}")
            
            # Stage 2: Instrument Detection & Analysis
            logger.info(f"[{job_id}] Stage 2: Instrument Detection")
            detected, scores = self.detector.detect_instruments(
                audio_path,
                mode=mode or "per_instrument"
            )
            
            logger.info(f"[{job_id}] Detected instruments: {detected}")
            
            # Stage 3: Routing Decision
            logger.info(f"[{job_id}] Stage 3: Routing Decision")
            routing_plan = self._create_routing_plan(
                detected=detected,
                scores=scores,
                quality=quality,
                mode=mode,
                target_instruments=target_instruments
            )
            
            logger.info(
                f"[{job_id}] Routing: {routing_plan['mode']} mode, "
                f"{routing_plan['quality']} quality"
            )
            
            # Stage 4: Stem Separation
            logger.info(f"[{job_id}] Stage 4: Stem Separation")
            
            # Create job-specific output directory
            job_output_dir = Path(output_dir or self.settings.output_dir) / job_id
            
            stems = self._execute_separation(
                audio_path=audio_path,
                routing_plan=routing_plan,
                output_dir=job_output_dir,
                custom_name=custom_name
            )
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            logger.info(
                f"[{job_id}] Complete in {processing_time:.2f}s - "
                f"{len(stems)} stems extracted"
            )
            
            # Create result
            result = ProcessingResult(
                job_id=job_id,
                status="completed",
                stems=stems,
                detected_instruments=detected,
                instrument_scores=scores,
                processing_time=processing_time,
                metadata={
                    "filename": audio_path.name,
                    "routing": routing_plan,
                    "stages_completed": 4
                }
            )
            
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"[{job_id}] Failed after {processing_time:.2f}s: {e}")
            
            return ProcessingResult(
                job_id=job_id,
                status="failed",
                stems={},
                detected_instruments=[],
                instrument_scores={},
                processing_time=processing_time,
                metadata={"error": str(e)}
            )
    
    def _create_routing_plan(
        self,
        detected: List[str],
        scores: Dict[str, float],
        quality: Optional[str],
        mode: Optional[str],
        target_instruments: Optional[List[str]]
    ) -> Dict:
        """
        Create routing plan based on detection and user preferences
        
        Args:
            detected: Detected instruments
            scores: Confidence scores
            quality: User-specified quality
            mode: User-specified mode
            target_instruments: User-specified targets
            
        Returns:
            Routing plan dictionary
        """
        # Use detector's routing recommendations if auto-routing
        if self.auto_route and not mode:
            plan = self.detector.get_routing_plan(detected, mode="per_instrument")
            recommended_mode = plan.get("mode", "grouped")
        else:
            recommended_mode = mode or self.settings.default_mode
        
        # Determine quality
        if not quality:
            # Auto-select based on complexity
            complexity = len(detected) * sum(scores.values()) / len(scores)
            if complexity > 4.0:
                quality = "fast"  # Complex mix - prioritize speed
            else:
                quality = "balanced"
        
        # Determine target instruments
        if not target_instruments:
            if recommended_mode == "per_instrument":
                target_instruments = detected
            elif recommended_mode == "karaoke":
                target_instruments = ["vocals", "instrumental"]
            else:
                target_instruments = ["vocals", "drums", "bass", "other"]
        
        return {
            "mode": recommended_mode,
            "quality": quality,
            "target_instruments": target_instruments,
            "detected_count": len(detected),
            "avg_confidence": sum(scores.values()) / len(scores) if scores else 0
        }
    
    def _execute_separation(
        self,
        audio_path: Path,
        routing_plan: Dict,
        output_dir: Union[str, Path],
        custom_name: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Execute stem separation based on routing plan
        
        Args:
            audio_path: Input audio path
            routing_plan: Routing plan from analysis
            output_dir: Output directory
            custom_name: Optional custom name for output files
            
        Returns:
            Dictionary of separated stems
        """
        # Create separation config with quality settings
        config = SeparationConfig(
            quality=QualityMode(routing_plan["quality"]),
            mode=SeparationMode(routing_plan["mode"]),
            target_instruments=routing_plan.get("target_instruments"),
            use_gpu=self.settings.use_gpu,
            # Quality preservation settings
            preserve_sample_rate=True,  # Keep native sample rate
            output_format="wav",        # Lossless WAV output
            bit_depth=24,               # 24-bit studio quality
        )
        
        # Initialize separator
        separator = HarmonixSeparator(config)
        
        # Perform separation
        stems = separator.separate(audio_path, output_dir, custom_name)
        
        return stems
    
    def analyze_only(
        self,
        audio_path: Union[str, Path]
    ) -> Dict:
        """
        Perform only analysis without separation
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Analysis results
        """
        audio_path = Path(audio_path)
        
        # Validate
        validation = self.preprocessor.validate_audio(audio_path)
        if not validation[0]:
            raise ValueError(f"Invalid audio: {validation[1]}")
        
        # Detect instruments
        detected, scores = self.detector.detect_instruments(
            audio_path,
            mode="per_instrument"
        )
        
        # Get recommendations
        routing_plan = self.detector.get_routing_plan(detected, mode="per_instrument")
        
        return {
            "detected_instruments": detected,
            "confidence_scores": scores,
            "recommendations": routing_plan,
            "metadata": {
                "filename": audio_path.name,
                "analysis_only": True
            }
        }
    
    def batch_process(
        self,
        audio_paths: List[Union[str, Path]],
        base_job_id: str,
        **kwargs
    ) -> List[ProcessingResult]:
        """
        Process multiple audio files
        
        Args:
            audio_paths: List of audio file paths
            base_job_id: Base identifier for jobs
            **kwargs: Additional arguments for process()
            
        Returns:
            List of processing results
        """
        results = []
        
        for idx, audio_path in enumerate(audio_paths):
            job_id = f"{base_job_id}_{idx}"
            
            try:
                result = self.process(
                    audio_path=audio_path,
                    job_id=job_id,
                    **kwargs
                )
                results.append(result)
                
            except Exception as e:
                logger.error(f"Batch job {job_id} failed: {e}")
                results.append(ProcessingResult(
                    job_id=job_id,
                    status="failed",
                    stems={},
                    detected_instruments=[],
                    instrument_scores={},
                    processing_time=0.0,
                    metadata={"error": str(e)}
                ))
        
        logger.info(
            f"Batch processing complete: {sum(1 for r in results if r.status == 'completed')}/{len(results)} succeeded"
        )
        
        return results


def create_orchestrator(
    auto_route: bool = True,
    settings: Optional[Settings] = None
) -> HarmonixOrchestrator:
    """
    Factory function to create orchestrator
    
    Args:
        auto_route: Enable automatic routing
        settings: Custom settings
        
    Returns:
        Configured HarmonixOrchestrator
    """
    return HarmonixOrchestrator(
        settings=settings,
        auto_route=auto_route
    )
