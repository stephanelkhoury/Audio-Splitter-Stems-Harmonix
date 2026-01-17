# Harmonix Shared Content Library

## Overview

The Shared Content Library is a powerful deduplication system that stores processed audio stems in a central location. When any user processes a YouTube video, the stems are stored once in the library and can be instantly accessed by any other user who requests the same content.

## Benefits

### ⚡ Instant Access
- **Skip the wait**: If a song has already been processed by anyone, you get instant access (< 1 second)
- **No re-processing**: The AI separation is only performed once per unique video
- **Bandwidth savings**: Audio is downloaded and processed just once

### 💾 Storage Efficiency
- **Deduplicated storage**: Only one copy of each processed song is stored
- **Shared across all users**: Every user benefits from the shared library
- **Reduced server load**: Less CPU/GPU usage, faster response times

### 🎵 Consistent Quality
- **Same stems for everyone**: All users get the same high-quality separation
- **Preserved metadata**: BPM, Key, Time Signature stored with each track
- **Video synchronization**: YouTube video ID maintained for karaoke playback

## How It Works

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     User Request Flow                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  User A submits YouTube URL                                      │
│        │                                                         │
│        ▼                                                         │
│  ┌─────────────────┐     ┌─────────────────┐                    │
│  │ Extract Video   │────▶│ Check Library   │                    │
│  │ ID (cNGjD0VG4R8)│     │ Exists?         │                    │
│  └─────────────────┘     └────────┬────────┘                    │
│                                   │                              │
│              ┌────────────────────┴────────────────────┐        │
│              │                                          │        │
│              ▼ NO                                       ▼ YES    │
│  ┌─────────────────────┐              ┌─────────────────────┐   │
│  │ Download & Process  │              │ Instant Link        │   │
│  │ (2-5 minutes)       │              │ (< 1 second)        │   │
│  └──────────┬──────────┘              └──────────┬──────────┘   │
│             │                                     │              │
│             ▼                                     │              │
│  ┌─────────────────────┐                         │              │
│  │ Save to Library     │                         │              │
│  │ /data/library/{id}/ │                         │              │
│  └──────────┬──────────┘                         │              │
│             │                                     │              │
│             └─────────────┬───────────────────────┘              │
│                           ▼                                      │
│               ┌─────────────────────┐                           │
│               │ Link to User's      │                           │
│               │ Library Links       │                           │
│               └──────────┬──────────┘                           │
│                          │                                       │
│                          ▼                                       │
│               ┌─────────────────────┐                           │
│               │ User sees stems in  │                           │
│               │ their dashboard     │                           │
│               └─────────────────────┘                           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Directory Structure

```
data/
├── library/                          # Shared library (deduped content)
│   ├── cNGjD0VG4R8/                 # YouTube video ID
│   │   ├── metadata.json            # Track info, BPM, Key, etc.
│   │   ├── Song_Name_original.mp3   # Original audio
│   │   ├── Song_Name_vocals.mp3     # Isolated vocals
│   │   └── Song_Name_instrumental.mp3
│   │
│   ├── dQw4w9WgXcQ/                 # Another video
│   │   ├── metadata.json
│   │   └── ...
│   │
│   └── ...
│
└── outputs/
    └── users/
        ├── user1/
        │   ├── library_links.json    # Links to library content
        │   └── {job_id}/             # User's uploaded files (not from library)
        │
        └── user2/
            ├── library_links.json
            └── ...
```

### Library Links File

Each user has a `library_links.json` file that tracks which library items they've accessed:

```json
{
  "links": {
    "cNGjD0VG4R8": {
      "youtube_id": "cNGjD0VG4R8",
      "display_name": "Ed_Sheeran_-_Perfect",
      "linked_at": "2026-01-15T18:20:19.636006",
      "is_library_link": true,
      "source_url": "https://youtu.be/cNGjD0VG4R8",
      "quality": "balanced",
      "mode": "karaoke"
    }
  },
  "created_at": "2026-01-15T18:20:19.635989",
  "updated_at": "2026-01-15T18:35:00.000000"
}
```

### Library Metadata

Each library item has a `metadata.json` with full track information:

```json
{
  "youtube_id": "cNGjD0VG4R8",
  "title": "Ed Sheeran - Perfect",
  "display_name": "Ed_Sheeran_-_Perfect",
  "duration": 264,
  "is_youtube": true,
  "has_video": true,
  "source_url": "https://youtu.be/cNGjD0VG4R8",
  "quality": "balanced",
  "mode": "karaoke",
  "created_at": "2026-01-15T18:15:49.693415",
  "processed_at": "2026-01-15T18:15:56.268328",
  "processing_time": 235.26,
  "usage_count": 5,
  "music_info": {
    "tempo": { "bpm": 95.7, "confidence": 0.23 },
    "key": { "key": "G#", "scale": "Major", "confidence": 0.98, "camelot": "4B" },
    "time_signature": "4/4",
    "duration": 263.69
  },
  "stems": ["vocals", "instrumental", "original"]
}
```

## API Endpoints

### Check Library Status

Before processing, the system checks if content exists:

```python
# Internal function
metadata = shared_library.check_library_exists(youtube_id)
if metadata:
    # Content exists - instant link!
    shared_library.link_to_user_library(username, youtube_id, job_id)
else:
    # Need to process - download and separate
    process_and_save_to_library(url, youtube_id)
```

### Serve Library Stems

```
GET /library/{youtube_id}/{stem_name}
```

- `youtube_id`: The YouTube video ID (e.g., `cNGjD0VG4R8`)
- `stem_name`: One of `vocals`, `instrumental`, `original`, `drums`, `bass`, etc.

### User's Library Links

The `/jobs` endpoint automatically includes library-linked content in the user's song list.

## User Experience

### For First-Time Content

1. User submits YouTube URL
2. System checks library → Not found
3. Download begins (10-30 seconds depending on video length)
4. AI processing starts (2-5 minutes)
5. Stems saved to library
6. User gets link to their library
7. Content appears in dashboard

**Total time: 2-5 minutes**

### For Already-Processed Content

1. User submits YouTube URL
2. System checks library → **Found!**
3. Instant link created to user's library
4. Content appears in dashboard

**Total time: < 1 second** ⚡

### Visual Indicator

Library-linked content shows a special badge in the dashboard:
- 📚 **Library** badge indicates shared content
- Shows "Instant" instead of processing time

## Admin Features

### Library Statistics

Admins can view library statistics in the admin panel:
- Total library items
- Most popular tracks (by usage count)
- Total storage used
- Recent additions

### Library Management

Admins can:
- View all library items
- See usage statistics per item
- Archive unused content
- Delete problematic items

## Technical Details

### Thread Safety

All library operations use a mutex lock (`library_lock`) to prevent race conditions:

```python
from threading import Lock
library_lock = Lock()

def link_to_user_library(...):
    with library_lock:
        # Safe modification
        links_data["links"][job_id] = {...}
        save_user_links(username, links_data)
```

### Usage Tracking

Each library item tracks how many users have linked to it:

```python
def update_library_usage(youtube_id: str, increment: bool = True):
    metadata = get_library_metadata(youtube_id)
    if metadata:
        if increment:
            metadata['usage_count'] = metadata.get('usage_count', 0) + 1
        else:
            metadata['usage_count'] = max(0, metadata.get('usage_count', 1) - 1)
        save_library_metadata(youtube_id, metadata)
```

### Archival System

When no users are linked to a library item, it can be archived:

```python
def archive_library_item(youtube_id: str):
    """Move unused library item to archive"""
    source = LIBRARY_DIR / youtube_id
    dest = ARCHIVE_DIR / youtube_id
    if source.exists():
        shutil.move(source, dest)
```

## Configuration

### Environment Variables

```bash
# Library location (default: ./data/library)
HARMONIX_LIBRARY_DIR=/path/to/library

# Archive location (default: ./data/archive)
HARMONIX_ARCHIVE_DIR=/path/to/archive

# Max library size (optional, for cleanup)
HARMONIX_LIBRARY_MAX_GB=100
```

### Settings

In `config/config.yaml`:

```yaml
library:
  enabled: true
  auto_cleanup: true
  cleanup_threshold_days: 90  # Archive items unused for 90 days
  max_size_gb: 100
```

## Migration Guide

### From Per-User Storage to Shared Library

If upgrading from an older version without shared library:

1. **Automatic migration**: On startup, the system scans for existing YouTube-sourced content
2. **Manual migration**: Run the migration script:

```bash
python -m harmonix_splitter.migrate_to_library
```

This will:
- Find all YouTube-sourced jobs
- Move unique content to library
- Update user links
- Remove duplicate files

## Troubleshooting

### Content Not Appearing

1. **Check library exists**: 
   ```bash
   ls data/library/{youtube_id}/
   ```

2. **Check user link**:
   ```bash
   cat data/outputs/users/{username}/library_links.json
   ```

3. **Restart server** to rescan library

### Broken Links

If a user's library link points to non-existent content:

```bash
# Remove broken link
# Edit library_links.json and remove the broken entry
```

### Library Corruption

If metadata is corrupted:

```bash
# Regenerate metadata from files
python -m harmonix_splitter.repair_library --youtube-id {id}
```

## Best Practices

1. **Regular backups**: Backup the `/data/library` folder regularly
2. **Monitor usage**: Check library growth and archive unused content
3. **Verify integrity**: Periodically verify all library items have valid stems
4. **Update metadata**: Keep music_info up to date when analysis improves

## Future Improvements

- [ ] Content-based deduplication (same audio from different uploads)
- [ ] Distributed library across multiple servers
- [ ] Cloud storage integration (S3, GCS)
- [ ] Automatic quality upgrade when better source available
- [ ] User ratings and quality feedback
