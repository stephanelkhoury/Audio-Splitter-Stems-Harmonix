#!/usr/bin/env python3
"""
RunPod Serverless Handler for Harmonix Audio Splitter
Deploy as a serverless GPU endpoint for cost-effective processing
"""

import os
import sys
import tempfile
import urllib.request
import base64

# Add the src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import runpod


def download_file(url: str, dest_path: str) -> str:
    """Download file from URL to local path."""
    urllib.request.urlretrieve(url, dest_path)
    return dest_path


def handler(job: dict) -> dict:
    """
    RunPod serverless handler for audio stem separation.
    
    Input:
        - audio_url: URL to download audio file from
        - audio_base64: Base64 encoded audio (alternative to URL)
        - quality: "fast" or "studio" (default: "fast")
        - format: "wav" or "mp3" (default: "wav")
        - stems: List of stems to extract (default: all)
    
    Returns:
        - stems: Dict of stem names to base64-encoded audio
        - metadata: Processing information
    """
    try:
        from harmonix_splitter.core.separator import AudioSeparator
        from harmonix_splitter.core.orchestrator import ProcessingOrchestrator
        
        job_input = job.get("input", {})
        
        # Get audio input
        audio_url = job_input.get("audio_url")
        audio_base64 = job_input.get("audio_base64")
        quality = job_input.get("quality", "fast")
        output_format = job_input.get("format", "wav")
        requested_stems = job_input.get("stems", None)
        
        if not audio_url and not audio_base64:
            return {"error": "Either audio_url or audio_base64 is required"}
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Get input file
            if audio_url:
                input_path = os.path.join(temp_dir, "input_audio")
                download_file(audio_url, input_path)
            else:
                # Decode base64
                input_path = os.path.join(temp_dir, "input_audio")
                audio_bytes = base64.b64decode(audio_base64)
                with open(input_path, 'wb') as f:
                    f.write(audio_bytes)
            
            # Initialize separator
            separator = AudioSeparator(quality_mode=quality)
            
            # Process audio
            output_dir = os.path.join(temp_dir, "output")
            os.makedirs(output_dir, exist_ok=True)
            
            result = separator.separate(
                input_path=input_path,
                output_dir=output_dir,
                output_format=output_format
            )
            
            # Encode output files as base64
            stems_output = {}
            for stem_name, stem_path in result.get("stems", {}).items():
                if requested_stems and stem_name not in requested_stems:
                    continue
                if os.path.exists(stem_path):
                    with open(stem_path, 'rb') as f:
                        stems_output[stem_name] = base64.b64encode(f.read()).decode('utf-8')
            
            return {
                "status": "success",
                "stems": stems_output,
                "metadata": {
                    "quality": quality,
                    "format": output_format,
                    "stems_extracted": list(stems_output.keys()),
                    "processing_time": result.get("processing_time", 0)
                }
            }
            
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "error_type": type(e).__name__
        }


if __name__ == "__main__":
    runpod.serverless.start({"handler": handler})
