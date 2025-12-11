"""
Tests for Harmonix API
"""

import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import io

from harmonix_splitter.api.main import app


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


class TestAPIEndpoints:
    """Test API endpoints"""
    
    def test_root(self, client):
        """Test root endpoint"""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert data["service"] == "Harmonix Audio Splitter"
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
    
    def test_get_models(self, client):
        """Test get available models"""
        response = client.get("/api/models")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "quality_modes" in data
        assert "separation_modes" in data
        assert "supported_instruments" in data
        assert "fast" in data["quality_modes"]
        assert "vocals" in data["supported_instruments"]
    
    def test_list_jobs_empty(self, client):
        """Test listing jobs when none exist"""
        response = client.get("/api/jobs")
        
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "jobs" in data


@pytest.mark.integration
class TestAPIIntegration:
    """Integration tests for API"""
    
    @pytest.fixture
    def test_audio_file(self, tmp_path):
        """Create test audio file"""
        import soundfile as sf
        import numpy as np
        
        sample_rate = 44100
        duration = 3
        t = np.linspace(0, duration, sample_rate * duration)
        audio = np.sin(2 * np.pi * 440 * t)
        audio_stereo = np.stack([audio, audio])
        
        test_file = tmp_path / "test.wav"
        sf.write(test_file, audio_stereo.T, sample_rate)
        
        return test_file
    
    def test_split_audio_upload(self, client, test_audio_file):
        """Test uploading audio for separation"""
        with open(test_audio_file, "rb") as f:
            response = client.post(
                "/api/split",
                files={"file": ("test.wav", f, "audio/wav")},
                params={"quality": "fast", "mode": "grouped"}
            )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "job_id" in data
        assert data["status"] == "queued"
        assert "created_at" in data
        
        return data["job_id"]
    
    def test_get_job_status(self, client, test_audio_file):
        """Test getting job status"""
        # First create a job
        with open(test_audio_file, "rb") as f:
            create_response = client.post(
                "/api/split",
                files={"file": ("test.wav", f, "audio/wav")},
                params={"quality": "fast"}
            )
        
        job_id = create_response.json()["job_id"]
        
        # Then check status
        status_response = client.get(f"/api/status/{job_id}")
        
        assert status_response.status_code == 200
        data = status_response.json()
        assert data["job_id"] == job_id
        assert "status" in data
        assert "progress" in data
    
    def test_analysis_endpoint(self, client, test_audio_file):
        """Test analysis endpoint"""
        with open(test_audio_file, "rb") as f:
            response = client.post(
                "/api/analysis",
                files={"file": ("test.wav", f, "audio/wav")}
            )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "instruments" in data
        assert "detected" in data
        assert "recommendations" in data
        assert isinstance(data["instruments"], dict)
        assert isinstance(data["detected"], list)


class TestAPIValidation:
    """Test API validation"""
    
    def test_invalid_file_format(self, client, tmp_path):
        """Test uploading invalid file format"""
        # Create a text file
        invalid_file = tmp_path / "test.txt"
        invalid_file.write_text("not an audio file")
        
        with open(invalid_file, "rb") as f:
            response = client.post(
                "/api/split",
                files={"file": ("test.txt", f, "text/plain")}
            )
        
        assert response.status_code == 400
    
    def test_nonexistent_job(self, client):
        """Test getting status of nonexistent job"""
        response = client.get("/api/status/nonexistent-job-id")
        assert response.status_code == 404
    
    def test_invalid_quality_parameter(self, client, tmp_path):
        """Test invalid quality parameter"""
        # Note: FastAPI validation will catch this
        # The endpoint expects specific enum values
        pass


@pytest.mark.asyncio
class TestAsyncEndpoints:
    """Test async functionality"""
    
    async def test_concurrent_jobs(self, client, test_audio_file):
        """Test handling multiple concurrent jobs"""
        # This would test the background task processing
        pass
