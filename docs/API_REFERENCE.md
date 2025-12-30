# API Reference Documentation

**Version:** 1.0.0  
**Last Updated:** December 30, 2025  
**Base URL:** `http://localhost:5001`

---

## Overview

The Harmonix Audio Splitter API provides endpoints for audio stem separation, lyrics extraction, and music analysis. This document covers all available endpoints, request/response formats, and authentication requirements.

---

## Authentication

All protected endpoints require an active session. Authentication is handled via session cookies.

### Login

```http
POST /login
Content-Type: application/x-www-form-urlencoded
```

**Request Body:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| email | string | Yes | User email address |
| password | string | Yes | User password |

**Response (Success - 302):**
```
Redirect to /dashboard
Set-Cookie: session=...
```

**Response (Error - 401):**
```json
{
  "error": "Invalid email or password"
}
```

### Register

```http
POST /register
Content-Type: application/x-www-form-urlencoded
```

**Request Body:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | Yes | Full name |
| email | string | Yes | Valid email address |
| password | string | Yes | Min 8 characters |

**Response (Success - 302):**
```
Redirect to /login
```

**Response (Error - 400):**
```json
{
  "error": "Email already registered"
}
```

### Logout

```http
GET /logout
```

**Response (302):**
```
Redirect to /
Session cleared
```

---

## Audio Processing

### Upload File

Upload an audio file for stem separation.

```http
POST /upload
Content-Type: multipart/form-data
Authorization: Session cookie required
```

**Request Body (multipart/form-data):**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| file | File | Yes | Audio file (mp3, wav, flac, m4a, ogg, aac) |
| quality | string | No | "fast", "balanced" (default), "studio" |
| mode | string | No | "grouped" (default), "karaoke", "per_instrument" |
| output_name | string | No | Custom display name |

**Response (200):**
```json
{
  "success": true,
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "message": "Upload successful. Processing started."
}
```

**Response (400):**
```json
{
  "success": false,
  "error": "No file uploaded"
}
```

**Response (403):**
```json
{
  "success": false,
  "error": "Monthly limit exceeded. Please upgrade your plan."
}
```

### Upload from URL

Process audio from a URL (YouTube, SoundCloud, etc.)

```http
POST /upload-url
Content-Type: application/json
Authorization: Session cookie required
```

**Request Body:**
```json
{
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "quality": "balanced",
  "mode": "grouped",
  "output_name": "Rick Astley - Never Gonna Give You Up"
}
```

**Response (200):**
```json
{
  "success": true,
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "downloading",
  "message": "Download started. Processing will begin shortly."
}
```

**Response (400):**
```json
{
  "success": false,
  "error": "Invalid or unsupported URL"
}
```

### Get Job Status

Check the status of a processing job.

```http
GET /status/{job_id}
Authorization: Session cookie required
```

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| job_id | string | UUID of the job |

**Response (200 - Processing):**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "progress": 45,
  "message": "Separating stems...",
  "step": 2,
  "total_steps": 4
}
```

**Response (200 - Completed):**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "progress": 100,
  "message": "Processing complete",
  "filename": "song.mp3",
  "display_name": "My Song",
  "created_at": "2025-12-30T15:00:00Z",
  "stems": {
    "vocals": "/outputs/user123/job123/vocals.wav",
    "drums": "/outputs/user123/job123/drums.wav",
    "bass": "/outputs/user123/job123/bass.wav",
    "other": "/outputs/user123/job123/other.wav"
  },
  "has_lyrics": false,
  "duration": 215.5
}
```

**Response (200 - Failed):**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "failed",
  "progress": 0,
  "message": "Error: Unsupported audio format",
  "error": "FFmpeg could not decode the file"
}
```

**Response (404):**
```json
{
  "error": "Job not found"
}
```

### List Jobs

Get all jobs for the current user.

```http
GET /jobs
Authorization: Session cookie required
```

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| page | integer | 1 | Page number |
| per_page | integer | 20 | Items per page |
| status | string | all | Filter: "all", "completed", "processing", "failed" |

**Response (200):**
```json
{
  "jobs": [
    {
      "job_id": "550e8400-e29b-41d4-a716-446655440000",
      "filename": "song.mp3",
      "display_name": "My Song",
      "status": "completed",
      "created_at": "2025-12-30T15:00:00Z",
      "duration": 215.5,
      "stems": ["vocals", "drums", "bass", "other"],
      "has_lyrics": true,
      "mode": "grouped",
      "quality": "balanced"
    }
  ],
  "total": 15,
  "page": 1,
  "per_page": 20,
  "pages": 1
}
```

### Download Stem

Download a specific stem from a completed job.

```http
GET /download/{job_id}/{stem_name}
Authorization: Session cookie required
```

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| job_id | string | UUID of the job |
| stem_name | string | Stem name: "vocals", "drums", "bass", "other", "guitar", "piano" |

**Response (200):**
```
Content-Type: audio/wav
Content-Disposition: attachment; filename="song_vocals.wav"

[Binary audio data]
```

**Response (404):**
```json
{
  "error": "Stem not found"
}
```

### Download All Stems (ZIP)

Download all stems as a ZIP archive.

```http
GET /download/{job_id}/all
Authorization: Session cookie required
```

**Response (200):**
```
Content-Type: application/zip
Content-Disposition: attachment; filename="song_stems.zip"

[Binary ZIP data]
```

### Delete Job

Delete a job and all associated files.

```http
DELETE /delete/{job_id}
Authorization: Session cookie required
```

**Response (200):**
```json
{
  "success": true,
  "message": "Job deleted successfully"
}
```

**Response (404):**
```json
{
  "error": "Job not found or access denied"
}
```

---

## Lyrics & Analysis

### Extract Lyrics

Extract lyrics from the vocals stem.

```http
POST /extract-lyrics/{job_id}
Content-Type: application/json
Authorization: Session cookie required
```

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| job_id | string | UUID of a completed job |

**Request Body:**
```json
{
  "language": "auto"
}
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| language | string | "auto" | Language code: "auto", "en", "ar", "fr", "es", "de", "ja", etc. |

**Response (200):**
```json
{
  "available": true,
  "language": "en",
  "confidence": 0.94,
  "duration": 215.5,
  "lines": [
    {
      "start": 12.5,
      "end": 15.2,
      "text": "Never gonna give you up",
      "words": [
        {"word": "Never", "start": 12.5, "end": 12.9},
        {"word": "gonna", "start": 12.9, "end": 13.3},
        {"word": "give", "start": 13.3, "end": 13.7},
        {"word": "you", "start": 13.7, "end": 14.0},
        {"word": "up", "start": 14.0, "end": 15.2}
      ]
    },
    {
      "start": 15.3,
      "end": 18.1,
      "text": "Never gonna let you down",
      "words": [...]
    }
  ]
}
```

**Response (400):**
```json
{
  "available": false,
  "error": "Vocals stem not available for this job"
}
```

### Get Lyrics

Get previously extracted lyrics.

```http
GET /lyrics/{job_id}
Authorization: Session cookie required
```

**Response (200):**
```json
{
  "available": true,
  "language": "en",
  "lines": [...]
}
```

**Response (404):**
```json
{
  "available": false,
  "error": "Lyrics not extracted for this job"
}
```

### Analyze Music

Get music analysis (BPM, key, time signature).

```http
GET /analyze/{job_id}
Authorization: Session cookie required
```

**Response (200):**
```json
{
  "tempo": {
    "bpm": 113,
    "confidence": 0.92
  },
  "key": {
    "key": "A",
    "mode": "major",
    "scale": ["A", "B", "C#", "D", "E", "F#", "G#"],
    "confidence": 0.85
  },
  "time_signature": {
    "time_signature": "4/4",
    "confidence": 0.98
  },
  "duration": 215.5,
  "sample_rate": 44100
}
```

---

## User & Account

### Get Current User

Get the current authenticated user's information.

```http
GET /api/user
Authorization: Session cookie required
```

**Response (200):**
```json
{
  "id": "user123",
  "email": "john@example.com",
  "name": "John Doe",
  "role": "user",
  "plan": "creator",
  "created_at": "2025-12-01T10:00:00Z"
}
```

### Get Plan Info

Get current user's plan details and usage.

```http
GET /api/plan-info
Authorization: Session cookie required
```

**Response (200):**
```json
{
  "plan": "creator",
  "plan_details": {
    "name": "Creator",
    "songs_per_month": 50,
    "max_file_size": 209715200,
    "stems": 6,
    "features": ["priority_processing", "lyrics_extraction", "music_analysis"]
  },
  "usage": {
    "used": 12,
    "limit": 50,
    "percentage": 24,
    "reset_date": "2026-01-01",
    "days_until_reset": 2
  },
  "storage": {
    "used_bytes": 2147483648,
    "limit_bytes": 10737418240,
    "used_formatted": "2.0 GB",
    "limit_formatted": "10.0 GB"
  },
  "is_admin": false
}
```

### Update Account

Update user account settings.

```http
PUT /api/user
Content-Type: application/json
Authorization: Session cookie required
```

**Request Body:**
```json
{
  "name": "John Smith",
  "email": "newmail@example.com",
  "current_password": "oldpassword",
  "new_password": "newpassword123"
}
```

**Response (200):**
```json
{
  "success": true,
  "message": "Account updated successfully"
}
```

**Response (400):**
```json
{
  "error": "Current password is incorrect"
}
```

---

## Admin Endpoints

These endpoints require admin role.

### Get All Users

```http
GET /api/admin/users
Authorization: Session cookie required (admin only)
```

**Response (200):**
```json
{
  "users": [
    {
      "id": "user123",
      "email": "john@example.com",
      "name": "John Doe",
      "role": "user",
      "plan": "creator",
      "created_at": "2025-12-01T10:00:00Z",
      "last_login": "2025-12-30T15:00:00Z",
      "usage": {
        "songs_this_month": 12
      }
    }
  ],
  "total": 150
}
```

### Update User

```http
PUT /api/admin/users/{user_id}
Content-Type: application/json
Authorization: Session cookie required (admin only)
```

**Request Body:**
```json
{
  "plan": "studio",
  "role": "user"
}
```

### Get System Stats

```http
GET /api/admin/stats
Authorization: Session cookie required (admin only)
```

**Response (200):**
```json
{
  "users": {
    "total": 150,
    "active_today": 45,
    "new_this_month": 23
  },
  "jobs": {
    "total": 2500,
    "completed": 2350,
    "processing": 5,
    "failed": 145
  },
  "storage": {
    "total_used": "125 GB",
    "average_per_user": "833 MB"
  },
  "plans": {
    "free": 100,
    "creator": 35,
    "studio": 15
  }
}
```

---

## WebSocket Events (Future)

> Note: WebSocket support is planned for real-time progress updates.

### Connection

```javascript
const socket = io('/processing');
socket.emit('subscribe', { job_id: 'job123' });
```

### Events

**progress**
```json
{
  "job_id": "job123",
  "progress": 65,
  "message": "Separating stems..."
}
```

**completed**
```json
{
  "job_id": "job123",
  "status": "completed",
  "stems": {...}
}
```

**error**
```json
{
  "job_id": "job123",
  "error": "Processing failed"
}
```

---

## Error Codes

| HTTP Status | Meaning |
|-------------|---------|
| 200 | Success |
| 201 | Created |
| 302 | Redirect |
| 400 | Bad Request - Invalid input |
| 401 | Unauthorized - Not logged in |
| 403 | Forbidden - Access denied or limit exceeded |
| 404 | Not Found |
| 413 | Payload Too Large - File exceeds limit |
| 429 | Too Many Requests - Rate limited |
| 500 | Internal Server Error |

---

## Rate Limiting

| Endpoint | Limit | Window |
|----------|-------|--------|
| /upload | 10 requests | 1 hour |
| /upload-url | 5 requests | 1 hour |
| /extract-lyrics | 20 requests | 1 hour |
| Other endpoints | 100 requests | 1 minute |

---

## Code Examples

### Python

```python
import requests

BASE_URL = "http://localhost:5001"
session = requests.Session()

# Login
login_response = session.post(f"{BASE_URL}/login", data={
    "email": "user@example.com",
    "password": "password123"
})

# Upload file
with open("song.mp3", "rb") as f:
    upload_response = session.post(f"{BASE_URL}/upload", files={
        "file": f
    }, data={
        "quality": "balanced",
        "mode": "grouped"
    })

job_id = upload_response.json()["job_id"]

# Poll for status
import time
while True:
    status = session.get(f"{BASE_URL}/status/{job_id}").json()
    if status["status"] == "completed":
        break
    elif status["status"] == "failed":
        raise Exception(status["message"])
    time.sleep(5)

# Download stems
for stem in ["vocals", "drums", "bass", "other"]:
    response = session.get(f"{BASE_URL}/download/{job_id}/{stem}")
    with open(f"{stem}.wav", "wb") as f:
        f.write(response.content)
```

### JavaScript

```javascript
async function processAudio(file) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('quality', 'balanced');
    formData.append('mode', 'grouped');

    // Upload
    const uploadRes = await fetch('/upload', {
        method: 'POST',
        body: formData,
        credentials: 'include'
    });
    const { job_id } = await uploadRes.json();

    // Poll for completion
    let status;
    do {
        await new Promise(r => setTimeout(r, 5000));
        const statusRes = await fetch(`/status/${job_id}`, {
            credentials: 'include'
        });
        status = await statusRes.json();
    } while (status.status === 'processing');

    return status;
}
```

### cURL

```bash
# Login (save cookies)
curl -c cookies.txt -X POST http://localhost:5001/login \
  -d "email=user@example.com&password=password123"

# Upload file
curl -b cookies.txt -X POST http://localhost:5001/upload \
  -F "file=@song.mp3" \
  -F "quality=balanced" \
  -F "mode=grouped"

# Check status
curl -b cookies.txt http://localhost:5001/status/JOB_ID

# Download stem
curl -b cookies.txt -o vocals.wav http://localhost:5001/download/JOB_ID/vocals
```

---

**Last Updated:** December 30, 2025  
**© 2025 Harmonix. All rights reserved.**
