#!/usr/bin/env python3
"""
Harmonix CLI - Command-line interface for audio stem separation
Usage: harmonix-split input.mp3 --mode studio --quality per_instrument
"""

import argparse
import sys
import logging
from pathlib import Path
from typing import Optional, List

from harmonix_splitter.core.orchestrator import create_orchestrator
from harmonix_splitter.config.settings import Settings

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


def parse_args():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        description="Harmonix Audio Splitter - AI-powered stem separation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage with defaults
  harmonix-split song.mp3

  # Studio quality with per-instrument separation
  harmonix-split song.mp3 --quality studio --mode per_instrument

  # Fast processing with specific output directory
  harmonix-split song.mp3 --quality fast --output ./stems

  # Target specific instruments
  harmonix-split song.mp3 --instruments vocals,drums,bass

  # Analysis only (no separation)
  harmonix-split song.mp3 --analyze-only

  # Batch process multiple files
  harmonix-split *.mp3 --output ./batch_stems
        """
    )
    
    # Input
    parser.add_argument(
        'input',
        nargs='+',
        type=str,
        help='Input audio file(s) to process'
    )
    
    # Output
    parser.add_argument(
        '-o', '--output',
        type=str,
        default='./harmonix_output',
        help='Output directory for stems (default: ./harmonix_output)'
    )
    
    # Quality
    parser.add_argument(
        '-q', '--quality',
        choices=['fast', 'balanced', 'studio'],
        default='balanced',
        help='Processing quality mode (default: balanced)'
    )
    
    # Mode
    parser.add_argument(
        '-m', '--mode',
        choices=['grouped', 'per_instrument'],
        default='grouped',
        help='Separation mode: grouped (4-stem) or per_instrument (default: grouped)'
    )
    
    # Target instruments
    parser.add_argument(
        '-i', '--instruments',
        type=str,
        help='Comma-separated list of target instruments (e.g., vocals,drums,bass)'
    )
    
    # GPU
    parser.add_argument(
        '--cpu-only',
        action='store_true',
        help='Force CPU processing (disable GPU)'
    )
    
    # Analysis
    parser.add_argument(
        '--analyze-only',
        action='store_true',
        help='Only analyze audio without separation'
    )
    
    # Auto-routing
    parser.add_argument(
        '--no-auto-route',
        action='store_true',
        help='Disable automatic routing based on detection'
    )
    
    # Verbose
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    # Version
    parser.add_argument(
        '--version',
        action='version',
        version='Harmonix Audio Splitter 1.0.0'
    )
    
    return parser.parse_args()


def setup_logging(verbose: bool):
    """Configure logging level"""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled")


def validate_inputs(input_paths: List[str]) -> List[Path]:
    """
    Validate input file paths
    
    Args:
        input_paths: List of input path strings
        
    Returns:
        List of validated Path objects
    """
    validated = []
    
    for path_str in input_paths:
        path = Path(path_str)
        if not path.exists():
            logger.error(f"File not found: {path}")
            continue
        
        if not path.is_file():
            logger.error(f"Not a file: {path}")
            continue
        
        validated.append(path)
    
    if not validated:
        logger.error("No valid input files found")
        sys.exit(1)
    
    return validated


def analyze_audio(orchestrator, audio_path: Path):
    """
    Perform analysis only
    
    Args:
        orchestrator: HarmonixOrchestrator instance
        audio_path: Path to audio file
    """
    logger.info(f"\n{'='*60}")
    logger.info(f"Analyzing: {audio_path.name}")
    logger.info(f"{'='*60}")
    
    try:
        result = orchestrator.analyze_only(audio_path)
        
        logger.info("\nDetected Instruments:")
        for inst in result['detected_instruments']:
            confidence = result['confidence_scores'].get(inst, 0)
            logger.info(f"  • {inst.capitalize()}: {confidence:.1%} confidence")
        
        logger.info("\nRecommendations:")
        recs = result['recommendations']
        logger.info(f"  Mode: {recs.get('mode', 'N/A')}")
        logger.info(f"  Complexity: {len(result['detected_instruments'])} instruments detected")
        
        logger.info(f"\n{'='*60}\n")
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")


def process_audio(
    orchestrator,
    audio_path: Path,
    output_dir: Path,
    quality: str,
    mode: str,
    instruments: Optional[List[str]]
):
    """
    Process audio file for stem separation
    
    Args:
        orchestrator: HarmonixOrchestrator instance
        audio_path: Path to audio file
        output_dir: Output directory
        quality: Quality mode
        mode: Separation mode
        instruments: Target instruments
    """
    logger.info(f"\n{'='*60}")
    logger.info(f"Processing: {audio_path.name}")
    logger.info(f"{'='*60}")
    logger.info(f"Quality: {quality}")
    logger.info(f"Mode: {mode}")
    if instruments:
        logger.info(f"Targets: {', '.join(instruments)}")
    logger.info("")
    
    # Create job ID from filename
    job_id = audio_path.stem
    
    # Create output subdirectory for this file
    file_output_dir = output_dir / audio_path.stem
    file_output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Process
        result = orchestrator.process(
            audio_path=audio_path,
            job_id=job_id,
            quality=quality,
            mode=mode,
            target_instruments=instruments,
            output_dir=file_output_dir
        )
        
        if result.status == "completed":
            logger.info(f"\n✓ Success! Processing time: {result.processing_time:.2f}s")
            logger.info(f"\nExtracted stems ({len(result.stems)}):")
            for stem_name in result.stems.keys():
                stem_path = file_output_dir / f"{audio_path.stem}_{stem_name}.wav"
                logger.info(f"  • {stem_name}.wav")
            
            logger.info(f"\nOutput location: {file_output_dir}")
            logger.info(f"{'='*60}\n")
            
        else:
            logger.error(f"\n✗ Failed: {result.metadata.get('error', 'Unknown error')}")
            logger.info(f"{'='*60}\n")
            
    except Exception as e:
        logger.error(f"\n✗ Processing failed: {e}")
        logger.info(f"{'='*60}\n")


def main():
    """Main CLI entry point"""
    args = parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    
    # Validate inputs
    input_paths = validate_inputs(args.input)
    
    logger.info("=" * 60)
    logger.info("Harmonix Audio Splitter v1.0.0")
    logger.info("=" * 60)
    
    # Create settings
    settings = Settings()
    if args.cpu_only:
        settings.use_gpu = False
        logger.info("GPU disabled - using CPU only")
    
    # Create orchestrator
    orchestrator = create_orchestrator(
        auto_route=not args.no_auto_route,
        settings=settings
    )
    
    # Parse target instruments
    target_instruments = None
    if args.instruments:
        target_instruments = [i.strip() for i in args.instruments.split(',')]
    
    # Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Process files
    if args.analyze_only:
        # Analysis mode
        for audio_path in input_paths:
            analyze_audio(orchestrator, audio_path)
    else:
        # Separation mode
        for audio_path in input_paths:
            process_audio(
                orchestrator=orchestrator,
                audio_path=audio_path,
                output_dir=output_dir,
                quality=args.quality,
                mode=args.mode,
                instruments=target_instruments
            )
    
    logger.info("All processing complete!")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\nFatal error: {e}")
        sys.exit(1)
