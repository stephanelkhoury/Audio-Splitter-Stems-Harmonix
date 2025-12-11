"""
Harmonix Audio Splitter - FastAPI Application
REST API for audio stem separation and analysis
"""

from fastapi import FastAPI, File, UploadFile, BackgroundTasks, HTTPException, Query
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from pathlib import Path
import uuid
import logging
from datetime import datetime
import asyncio
import shutil

from ..core.separator import HarmonixSeparator, QualityMode, SeparationMode, SeparationConfig
from ..analysis.detector import InstrumentDetector
from ..core.preprocessor import AudioPreprocessor
from ..config.settings import Settings

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Harmonix Audio Splitter API",
    description="AI-powered audio stem separation and instrument detection",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load settings
settings = Settings()

# Job storage (use Redis/database in production)
jobs: Dict[str, Dict] = {}


# Pydantic models
class SplitRequest(BaseModel):
    """Request model for stem separation"""
    quality: str = Field("balanced", description="Quality mode: fast, balanced, studio")
    mode: str = Field("grouped", description="Mode: grouped (4-stem) or per_instrument")
    target_instruments: Optional[List[str]] = Field(None, description="Specific instruments to extract")
    return_urls: bool = Field(True, description="Return file URLs instead of base64")
    

class JobStatus(BaseModel):
    """Job status response"""
    job_id: str
    status: str
    progress: float
    message: Optional[str] = None
    result: Optional[Dict] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


class StemInfo(BaseModel):
    """Information about a stem"""
    name: str
    url: Optional[str] = None
    duration: float
    confidence: float
    metadata: Dict


class SplitResponse(BaseModel):
    """Response for completed split job"""
    job_id: str
    status: str
    stems: List[StemInfo]
    processing_time: float
    metadata: Dict


class AnalysisResponse(BaseModel):
    """Response for audio analysis"""
    instruments: Dict[str, float]
    detected: List[str]
    recommendations: Dict
    metadata: Dict


class ModelsResponse(BaseModel):
    """Available models and configurations"""
    quality_modes: List[str]
    separation_modes: List[str]
    supported_instruments: List[str]
    supported_formats: List[str]


# Helper functions
def get_upload_path() -> Path:
    """Get upload directory path"""
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir


def get_output_path(job_id: str) -> Path:
    """Get output directory for job"""
    output_dir = Path(settings.output_dir) / job_id
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def cleanup_job_files(job_id: str):
    """Clean up temporary files for a job"""
    try:
        output_dir = Path(settings.output_dir) / job_id
        if output_dir.exists():
            shutil.rmtree(output_dir)
        logger.info(f"Cleaned up files for job {job_id}")
    except Exception as e:
        logger.error(f"Failed to cleanup job {job_id}: {e}")


async def process_separation_job(
    job_id: str,
    audio_path: Path,
    config: SeparationConfig
):
    """
    Background task to process stem separation
    
    Args:
        job_id: Unique job identifier
        audio_path: Path to input audio file
        config: Separation configuration
    """
    try:
        # Update job status
        jobs[job_id]["status"] = "processing"
        jobs[job_id]["progress"] = 0.1
        
        logger.info(f"Job {job_id}: Starting separation")
        
        # Initialize separator
        separator = HarmonixSeparator(config)
        
        jobs[job_id]["progress"] = 0.3
        
        # Get output directory
        output_dir = get_output_path(job_id)
        
        # Perform separation
        start_time = datetime.now()
        stems = separator.separate(audio_path, output_dir)
        processing_time = (datetime.now() - start_time).total_seconds()
        
        jobs[job_id]["progress"] = 0.9
        
        # Prepare result
        stem_infos = []
        for name, stem in stems.items():
            stem_info = {
                "name": name,
                "url": f"/api/stems/{job_id}/{name}.wav",
                "duration": len(stem.audio[0]) / stem.sample_rate,
                "confidence": stem.confidence,
                "metadata": stem.metadata or {}
            }
            stem_infos.append(stem_info)
        
        # Update job with results
        jobs[job_id].update({
            "status": "completed",
            "progress": 1.0,
            "completed_at": datetime.now(),
            "result": {
                "stems": stem_infos,
                "processing_time": processing_time,
                "metadata": {
                    "quality": config.quality.value,
                    "mode": config.mode.value,
                    "sample_rate": config.sample_rate
                }
            }
        })
        
        logger.info(f"Job {job_id}: Completed in {processing_time:.2f}s")
        
    except Exception as e:
        logger.error(f"Job {job_id}: Failed - {e}")
        jobs[job_id].update({
            "status": "failed",
            "message": str(e),
            "completed_at": datetime.now()
        })


# API Endpoints

@app.get("/", tags=["General"])
async def root():
    """API root endpoint"""
    return {
        "service": "Harmonix Audio Splitter",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "split": "/api/split",
            "analysis": "/api/analysis",
            "models": "/api/models",
            "docs": "/docs"
        }
    }


@app.get("/health", tags=["General"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/split", response_model=JobStatus, tags=["Separation"])
async def split_audio(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    quality: str = Query("balanced", description="Quality: fast, balanced, studio"),
    mode: str = Query("grouped", description="Mode: grouped or per_instrument"),
    target_instruments: Optional[str] = Query(None, description="Comma-separated instrument list")
):
    """
    Submit audio file for stem separation
    
    Returns job ID for status tracking
    """
    # Validate file format
    if not file.filename.endswith(tuple(settings.allowed_formats)):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format. Allowed: {settings.allowed_formats}"
        )
    
    # Generate job ID
    job_id = str(uuid.uuid4())
    
    try:
        # Save uploaded file
        upload_path = get_upload_path() / f"{job_id}_{file.filename}"
        with upload_path.open("wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        logger.info(f"Job {job_id}: File uploaded - {file.filename}")
        
        # Validate and preprocess audio
        preprocessor = AudioPreprocessor()
        validation = preprocessor.validate_audio(upload_path)
        
        if not validation["valid"]:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid audio: {validation.get('error')}"
            )
        
        # Parse target instruments
        target_inst_list = None
        if target_instruments:
            target_inst_list = [i.strip() for i in target_instruments.split(",")]
        
        # Create separation config
        config = SeparationConfig(
            quality=QualityMode(quality),
            mode=SeparationMode(mode),
            target_instruments=target_inst_list,
            use_gpu=settings.use_gpu
        )
        
        # Create job record
        jobs[job_id] = {
            "job_id": job_id,
            "status": "queued",
            "progress": 0.0,
            "created_at": datetime.now(),
            "filename": file.filename,
            "config": {
                "quality": quality,
                "mode": mode,
                "target_instruments": target_inst_list
            }
        }
        
        # Schedule background processing
        background_tasks.add_task(
            process_separation_job,
            job_id,
            upload_path,
            config
        )
        
        return JobStatus(
            job_id=job_id,
            status="queued",
            progress=0.0,
            message="Job queued for processing",
            created_at=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Failed to create job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/status/{job_id}", response_model=JobStatus, tags=["Separation"])
async def get_job_status(job_id: str):
    """
    Get status of a separation job
    
    Args:
        job_id: Job identifier
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    
    return JobStatus(
        job_id=job_id,
        status=job["status"],
        progress=job["progress"],
        message=job.get("message"),
        result=job.get("result"),
        created_at=job["created_at"],
        completed_at=job.get("completed_at")
    )


@app.get("/api/result/{job_id}", response_model=SplitResponse, tags=["Separation"])
async def get_job_result(job_id: str):
    """
    Get results of completed separation job
    
    Args:
        job_id: Job identifier
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    
    if job["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Job not completed. Status: {job['status']}"
        )
    
    result = job["result"]
    
    return SplitResponse(
        job_id=job_id,
        status="completed",
        stems=[StemInfo(**stem) for stem in result["stems"]],
        processing_time=result["processing_time"],
        metadata=result["metadata"]
    )


@app.get("/api/stems/{job_id}/{stem_name}", tags=["Files"])
async def download_stem(job_id: str, stem_name: str):
    """
    Download a specific stem file
    
    Args:
        job_id: Job identifier
        stem_name: Stem filename (e.g., vocals.wav)
    """
    stem_path = Path(settings.output_dir) / job_id / stem_name
    
    if not stem_path.exists():
        raise HTTPException(status_code=404, detail="Stem file not found")
    
    return FileResponse(
        stem_path,
        media_type="audio/wav",
        filename=stem_name
    )


@app.post("/api/analysis", response_model=AnalysisResponse, tags=["Analysis"])
async def analyze_audio(file: UploadFile = File(...)):
    """
    Analyze audio file to detect instruments without separation
    
    Args:
        file: Audio file to analyze
        
    Returns:
        Detected instruments and recommendations
    """
    try:
        # Save uploaded file temporarily
        temp_id = str(uuid.uuid4())
        temp_path = get_upload_path() / f"analysis_{temp_id}_{file.filename}"
        
        with temp_path.open("wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        logger.info(f"Analyzing: {file.filename}")
        
        # Initialize detector
        detector = InstrumentDetector()
        
        # Perform analysis
        detected, scores = detector.detect_instruments(temp_path, mode="per_instrument")
        
        # Get routing plan
        routing_plan = detector.get_routing_plan(detected, mode="per_instrument")
        
        # Cleanup temp file
        temp_path.unlink()
        
        return AnalysisResponse(
            instruments=scores,
            detected=detected,
            recommendations=routing_plan,
            metadata={
                "filename": file.filename,
                "analyzed_at": datetime.now().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/models", response_model=ModelsResponse, tags=["Information"])
async def get_available_models():
    """
    Get information about available models and configurations
    """
    return ModelsResponse(
        quality_modes=["fast", "balanced", "studio"],
        separation_modes=["grouped", "per_instrument"],
        supported_instruments=[
            "vocals", "drums", "bass", "guitar", "piano",
            "strings", "synth", "brass", "woodwinds", "fx"
        ],
        supported_formats=settings.allowed_formats
    )


@app.delete("/api/jobs/{job_id}", tags=["Jobs"])
async def delete_job(job_id: str):
    """
    Delete a job and cleanup its files
    
    Args:
        job_id: Job identifier
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Cleanup files
    cleanup_job_files(job_id)
    
    # Remove from jobs dict
    del jobs[job_id]
    
    return {"message": f"Job {job_id} deleted successfully"}


@app.get("/api/jobs", tags=["Jobs"])
async def list_jobs(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, description="Maximum number of jobs to return")
):
    """
    List all jobs, optionally filtered by status
    
    Args:
        status: Filter by job status (queued, processing, completed, failed)
        limit: Maximum number of jobs to return
    """
    job_list = list(jobs.values())
    
    if status:
        job_list = [j for j in job_list if j["status"] == status]
    
    # Sort by creation time (newest first)
    job_list.sort(key=lambda x: x["created_at"], reverse=True)
    
    # Limit results
    job_list = job_list[:limit]
    
    return {
        "total": len(job_list),
        "jobs": job_list
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
