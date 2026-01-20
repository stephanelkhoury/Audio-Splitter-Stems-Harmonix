# 📺 YouTube Integration

**Complete guide to processing YouTube videos**

---

## Table of Contents

- [Overview](#overview)
- [URL Processing](#url-processing)
- [Shared Library](#shared-library)
- [Cookies Configuration](#cookies-configuration)
- [Rate Limiting](#rate-limiting)
- [Troubleshooting](#troubleshooting)

---

## Overview

Harmonix integrates with YouTube through `yt-dlp` to:

- 🔗 **Download** audio from YouTube URLs
- 📚 **Cache** processed content in shared library
- 🔄 **Deduplicate** to avoid reprocessing
- 📊 **Preserve** original metadata

---

## URL Processing

### Supported URL Formats

```
✅ Standard videos:
   https://www.youtube.com/watch?v=dQw4w9WgXcQ
   https://youtube.com/watch?v=dQw4w9WgXcQ
   http://www.youtube.com/watch?v=dQw4w9WgXcQ

✅ Short URLs:
   https://youtu.be/dQw4w9WgXcQ

✅ YouTube Shorts:
   https://youtube.com/shorts/dQw4w9WgXcQ

✅ Mobile URLs:
   https://m.youtube.com/watch?v=dQw4w9WgXcQ

✅ With timestamps:
   https://youtube.com/watch?v=dQw4w9WgXcQ&t=120

✅ In playlists:
   https://youtube.com/watch?v=dQw4w9WgXcQ&list=PLxxx
```

### Processing Flow

```
┌──────────────────────────────────────────────────────────────┐
│  YouTube URL Processing Flow                                  │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  1. User submits YouTube URL                                 │
│         ↓                                                    │
│  2. Extract video ID from URL                                │
│         ↓                                                    │
│  3. Check shared library for existing content                │
│         ↓                                                    │
│     ┌───────────────┬───────────────────┐                   │
│     │ Found         │ Not Found          │                   │
│     ↓               ↓                    │                   │
│  4a. Link to       4b. Download audio    │                   │
│      user library       via yt-dlp       │                   │
│         ↓               ↓                │                   │
│  5a. Return        5b. Process stems     │                   │
│      instantly          ↓                │                   │
│                    6b. Save to shared    │                   │
│                        library           │                   │
│                         ↓                │                   │
│                    7b. Return stems      │                   │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### Using the Dashboard

1. Go to the upload page
2. Click "URL" tab
3. Paste YouTube URL
4. Select quality and mode
5. Click "Process"

```
┌────────────────────────────────────────────────────────────┐
│  🔗 Process from URL                                       │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐ │
│  │ https://youtube.com/watch?v=dQw4w9WgXcQ              │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                            │
│  Detected: YouTube Video                                   │
│                                                            │
│  [▶️ Process URL]                                          │
└────────────────────────────────────────────────────────────┘
```

### Using the CLI

```bash
# Process YouTube URL
harmonix process --url "https://youtube.com/watch?v=dQw4w9WgXcQ"

# With options
harmonix process \
    --url "https://youtube.com/watch?v=dQw4w9WgXcQ" \
    --quality studio \
    --mode per_instrument \
    --output ./my-stems
```

### Using the API

```python
import requests

response = requests.post(
    "http://localhost:8000/process/url",
    json={
        "url": "https://youtube.com/watch?v=dQw4w9WgXcQ",
        "quality": "studio",
        "mode": "grouped"
    }
)

result = response.json()
print(f"Job ID: {result['job_id']}")
```

---

## Shared Library

### How It Works

The shared library stores processed YouTube content:

```
data/library/
├── dQw4w9WgXcQ/           # Video ID as folder name
│   ├── metadata.json       # Video information
│   ├── original.mp3        # Downloaded audio
│   ├── vocals.mp3          # Separated stems
│   ├── drums.mp3
│   ├── bass.mp3
│   ├── other.mp3
│   └── analysis.json       # BPM, key, etc.
├── kJQP7kiw5Fk/
│   └── ...
└── ...
```

### Benefits

| Benefit | Description |
|---------|-------------|
| **Instant Access** | Already processed content loads immediately |
| **Bandwidth Savings** | No re-downloading from YouTube |
| **Processing Savings** | No GPU time for duplicates |
| **Shared Across Users** | All users benefit from library |

### Library Metadata

```json
{
    "video_id": "dQw4w9WgXcQ",
    "title": "Rick Astley - Never Gonna Give You Up",
    "channel": "Rick Astley",
    "duration": 212,
    "upload_date": "2009-10-25",
    "processed_at": "2025-12-15T10:30:00Z",
    "quality_mode": "studio",
    "separation_mode": "grouped",
    "stems": ["vocals", "drums", "bass", "other"],
    "analysis": {
        "bpm": 113,
        "key": "A Major",
        "camelot": "11B"
    }
}
```

### Library Management

```python
from harmonix_splitter.library import SharedLibrary

library = SharedLibrary(path="./data/library")

# Check if content exists
if library.has_content("dQw4w9WgXcQ"):
    content = library.get_content("dQw4w9WgXcQ")
    print(f"Found: {content.title}")

# Add new content
library.add_content(
    video_id="kJQP7kiw5Fk",
    metadata=video_metadata,
    stems_path="./processed/stems"
)

# List all content
for content in library.list_all():
    print(f"{content.video_id}: {content.title}")
```

---

## Cookies Configuration

Some YouTube videos require authentication. Use a cookies file:

### Creating cookies.txt

**Option 1: Browser Extension**

Use a browser extension like "Get cookies.txt LOCALLY":
1. Install extension
2. Go to YouTube (logged in)
3. Click extension icon
4. Export cookies as Netscape format
5. Save as `cookies.txt` in project root

**Option 2: Manual Creation**

```
# Netscape HTTP Cookie File
.youtube.com	TRUE	/	TRUE	0	CONSENT	YES+
.youtube.com	TRUE	/	TRUE	0	SID	your_sid_cookie
.youtube.com	TRUE	/	TRUE	0	HSID	your_hsid_cookie
```

### Using Cookies

```bash
# CLI with cookies
harmonix process --url "..." --cookies ./cookies.txt

# Environment variable
export HARMONIX_COOKIES_PATH="./cookies.txt"
```

```python
# Python API
from harmonix_splitter import process_youtube

process_youtube(
    url="https://youtube.com/watch?v=...",
    cookies_path="./cookies.txt"
)
```

### When Cookies Are Needed

- Age-restricted videos
- Region-locked content
- Premium content
- Videos requiring sign-in

---

## Rate Limiting

### YouTube Limits

YouTube may rate limit or block excessive requests:

| Scenario | Symptom |
|----------|---------|
| Too many downloads | "HTTP Error 429" |
| IP blocked | "HTTP Error 403" |
| Bot detection | CAPTCHA required |

### Best Practices

```python
# Built-in protections:
- Shared library avoids re-downloads
- Automatic retry with backoff
- User-Agent rotation
- Request throttling
```

### Configuration

```yaml
# config/config.yaml
youtube:
  rate_limit_delay: 2.0  # Seconds between requests
  max_retries: 3
  retry_delay: 5.0
  user_agent: "Mozilla/5.0 ..."
```

---

## Video Metadata Extraction

### Extracted Information

```python
metadata = {
    "id": "dQw4w9WgXcQ",
    "title": "Rick Astley - Never Gonna Give You Up",
    "description": "Official video...",
    "channel": "Rick Astley",
    "channel_id": "UCuAXFkgsw1L7xaCfnd5JJOw",
    "upload_date": "2009-10-25",
    "duration": 212,
    "view_count": 1500000000,
    "like_count": 15000000,
    "thumbnail": "https://i.ytimg.com/vi/dQw4w9WgXcQ/maxresdefault.jpg",
    "categories": ["Music"],
    "tags": ["rick astley", "never gonna give you up"]
}
```

### Using Metadata

```python
from harmonix_splitter.library import get_video_metadata

metadata = get_video_metadata("dQw4w9WgXcQ")

print(f"Title: {metadata['title']}")
print(f"Duration: {metadata['duration']} seconds")
print(f"Views: {metadata['view_count']:,}")
```

---

## Audio Quality

### Download Options

```python
# yt-dlp audio extraction settings
ydl_opts = {
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '320',  # 320 kbps
    }],
    'outtmpl': '%(id)s.%(ext)s',
}
```

### Quality Levels

| Source Quality | Downloaded As |
|----------------|---------------|
| Highest available | 320 kbps MP3 |
| 256 kbps | 256 kbps MP3 |
| 128 kbps | 128 kbps MP3 |

---

## Troubleshooting

### Common Errors

**"Video unavailable"**
```
Cause: Video is private, deleted, or region-locked
Solution: 
- Use VPN for region issues
- Add cookies for private videos
- Verify video exists
```

**"Unable to extract video data"**
```
Cause: yt-dlp needs update
Solution:
pip install -U yt-dlp
```

**"HTTP Error 429"**
```
Cause: Rate limited by YouTube
Solution:
- Wait 1-24 hours
- Use different IP/VPN
- Add cookies file
```

**"Sign in to confirm age"**
```
Cause: Age-restricted video
Solution:
- Add cookies from logged-in session
```

**"This video is not available"**
```
Cause: Geographic restriction
Solution:
- Use VPN to allowed region
- Add cookies file
```

### Debug Mode

```bash
# Enable verbose yt-dlp logging
export HARMONIX_DEBUG=true
harmonix process --url "..." --verbose
```

### Manual Testing

```bash
# Test yt-dlp directly
yt-dlp -F "https://youtube.com/watch?v=dQw4w9WgXcQ"

# Download audio only
yt-dlp -x --audio-format mp3 "https://youtube.com/watch?v=..."
```

---

## Privacy & Legal

### Data Handling

- Downloaded audio stored locally only
- Metadata stored in library
- No data sent to third parties
- User responsible for usage rights

### Terms of Service

⚠️ **Important:** Downloading YouTube content may violate YouTube's Terms of Service. Use this feature responsibly and only for:

- Content you own
- Content with explicit permission
- Fair use purposes
- Educational purposes

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `HARMONIX_COOKIES_PATH` | Path to cookies file | `./cookies.txt` |
| `HARMONIX_LIBRARY_PATH` | Shared library location | `./data/library` |
| `HARMONIX_YT_RATE_LIMIT` | Delay between requests | `2.0` |
| `HARMONIX_YT_MAX_RETRIES` | Download retry attempts | `3` |

---

## Related Documentation

- [Installation](./INSTALLATION.md) - Installing yt-dlp
- [Dashboard](./DASHBOARD.md) - Web interface
- [CLI Guide](./CLI_GUIDE.md) - Command-line usage
- [Configuration](./CONFIGURATION.md) - Settings

---

*YouTube integration documentation last updated: January 2026*
