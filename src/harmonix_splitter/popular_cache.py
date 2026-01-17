"""
Popular Songs Cache System

Pre-processes trending YouTube songs in the background so users get instant access
to commonly requested content.

Usage:
    - Automatic: Background thread processes trending songs overnight
    - Manual: Admin can trigger via /admin/cache/refresh endpoint
    - API: Get popular songs from /api/popular endpoint
"""

import json
import logging
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# Data directory
DATA_DIR = Path(__file__).parent.parent.parent.parent / "data"
CACHE_FILE = DATA_DIR / "popular_cache.json"
CACHE_DIR = DATA_DIR / "cache"

# Ensure directories exist
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def load_cache_config() -> Dict[str, Any]:
    """Load popular songs cache configuration."""
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading cache config: {e}")
    
    return {
        "enabled": True,
        "max_songs": 50,
        "refresh_interval_hours": 24,
        "last_refresh": None,
        "trending_sources": [
            "youtube_music_trending",
            "most_requested"
        ],
        "popular_songs": []
    }


def save_cache_config(config: Dict[str, Any]):
    """Save cache configuration."""
    try:
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error saving cache config: {e}")


def get_most_requested_songs() -> List[Dict[str, str]]:
    """
    Get most frequently requested songs from user activity.
    Returns list of {youtube_id, title, request_count}
    """
    from harmonix_splitter import library as shared_library
    
    # Get all library items sorted by usage
    all_items = shared_library.get_all_library_items()
    
    # Return top requested songs
    popular = []
    for item in all_items[:20]:  # Top 20 most used
        if item.get('usage_count', 0) > 0:
            popular.append({
                'youtube_id': item.get('youtube_id'),
                'title': item.get('display_name', 'Unknown'),
                'request_count': item.get('usage_count', 0),
                'source': 'most_requested'
            })
    
    return popular


def get_trending_songs_youtube() -> List[Dict[str, str]]:
    """
    Fetch trending songs from YouTube Music.
    Returns list of {youtube_id, title, source}
    
    Note: This is a placeholder - in production, you'd use YouTube Data API
    or a service like chart.lemon.sh
    """
    # Placeholder trending songs (replace with API call in production)
    # These are popular karaoke/cover songs that are frequently requested
    trending = [
        {"youtube_id": "dQw4w9WgXcQ", "title": "Rick Astley - Never Gonna Give You Up", "source": "youtube_trending"},
        {"youtube_id": "fJ9rUzIMcZQ", "title": "Queen - Bohemian Rhapsody", "source": "youtube_trending"},
        {"youtube_id": "L0MK7qz13bU", "title": "The Weeknd - Blinding Lights", "source": "youtube_trending"},
        {"youtube_id": "7PCkvCPvDXk", "title": "a]ha - Take On Me", "source": "youtube_trending"},
        {"youtube_id": "kJQP7kiw5Fk", "title": "Luis Fonsi - Despacito", "source": "youtube_trending"},
    ]
    
    return trending


def get_popular_songs_for_caching() -> List[Dict[str, str]]:
    """
    Get list of popular songs that should be pre-cached.
    Combines trending and most-requested songs.
    """
    songs = []
    seen_ids = set()
    
    # Add most requested first (already processed, just verify they're cached)
    for song in get_most_requested_songs():
        if song['youtube_id'] not in seen_ids:
            songs.append(song)
            seen_ids.add(song['youtube_id'])
    
    # Add trending songs
    for song in get_trending_songs_youtube():
        if song['youtube_id'] not in seen_ids:
            songs.append(song)
            seen_ids.add(song['youtube_id'])
    
    return songs[:50]  # Limit to 50 songs


def is_song_cached(youtube_id: str) -> bool:
    """Check if a song is already in the shared library."""
    from harmonix_splitter import library as shared_library
    return shared_library.check_library_exists(youtube_id) is not None


def cache_song(youtube_id: str, title: str) -> bool:
    """
    Cache a song by processing it.
    This runs the full separation pipeline and stores in shared library.
    """
    from harmonix_splitter import library as shared_library
    
    # Skip if already cached
    if is_song_cached(youtube_id):
        logger.info(f"Cache: {title} already cached")
        return True
    
    logger.info(f"Cache: Processing {title} ({youtube_id})")
    
    try:
        import yt_dlp
        from harmonix_splitter.core.orchestrator import create_orchestrator
        from harmonix_splitter.analysis.music_analyzer import MusicAnalyzer
        
        # Create library entry
        url = f"https://www.youtube.com/watch?v={youtube_id}"
        job_output_dir = shared_library.create_library_entry(youtube_id, {
            'source_url': url,
            'quality': 'balanced',
            'mode': 'grouped',
            'cached': True,
            'cached_at': datetime.now().isoformat()
        })
        
        # Download audio
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': str(job_output_dir / '%(title)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320',
            }],
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            video_title = info.get('title', title)
            duration = info.get('duration', 0)
        
        # Find downloaded file
        audio_files = list(job_output_dir.glob('*.mp3'))
        if not audio_files:
            raise Exception("Failed to download audio")
        
        audio_path = audio_files[0]
        
        # Rename to standard format
        from werkzeug.utils import secure_filename
        display_name = secure_filename(video_title or title)
        original_audio_path = job_output_dir / f"{display_name}_original{audio_path.suffix}"
        audio_path.rename(original_audio_path)
        
        # Analyze for tempo/key
        try:
            analyzer = MusicAnalyzer()
            analysis = analyzer.analyze(original_audio_path)
            music_info = {
                'tempo': {'bpm': analysis.tempo.bpm, 'confidence': analysis.tempo.bpm_confidence},
                'key': {'key': analysis.key.key, 'scale': analysis.key.scale},
                'duration': analysis.duration
            }
        except Exception:
            music_info = {}
        
        # Process stems
        orchestrator = create_orchestrator(auto_route=True)
        result = orchestrator.process(
            audio_path=str(original_audio_path),
            job_id=youtube_id,
            quality='balanced',
            mode='grouped',
            output_dir=str(job_output_dir.parent),
            custom_name=display_name
        )
        
        # Update metadata with ALL required fields
        metadata_file = job_output_dir / 'metadata.json'
        metadata = {
            'youtube_id': youtube_id,
            'created_at': datetime.now().isoformat(),
            'usage_count': 0,
            'source_url': url,
            'quality': 'balanced',
            'mode': 'grouped',
            'display_name': display_name,
            'title': video_title,
            'duration': duration,
            'is_youtube': True,
            'youtube_video_id': youtube_id,
            'has_video': True,
            'processed_at': datetime.now().isoformat(),
            'music_info': music_info,
            'stems': ['original'] + list(result.stems.keys()),
            'clean_title': display_name,
            'cached': True,
            'cached_at': datetime.now().isoformat(),
            'processing_time': result.processing_time
        }
        
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Cache: Successfully cached {title}")
        return True
        
    except Exception as e:
        logger.error(f"Cache: Failed to cache {title}: {e}")
        return False


def refresh_popular_cache(max_songs: int = 10):
    """
    Refresh the popular songs cache.
    Processes songs that aren't already cached.
    """
    config = load_cache_config()
    
    if not config.get('enabled', True):
        logger.info("Cache: Popular songs caching is disabled")
        return
    
    logger.info(f"Cache: Starting popular songs refresh (max {max_songs} songs)")
    
    # Get songs to cache
    popular_songs = get_popular_songs_for_caching()
    
    cached_count = 0
    for song in popular_songs:
        if cached_count >= max_songs:
            break
        
        youtube_id = song.get('youtube_id')
        title = song.get('title', 'Unknown')
        
        if youtube_id and not is_song_cached(youtube_id):
            if cache_song(youtube_id, title):
                cached_count += 1
            
            # Small delay between processing
            time.sleep(2)
    
    # Update config
    config['last_refresh'] = datetime.now().isoformat()
    config['popular_songs'] = [s['youtube_id'] for s in popular_songs if s.get('youtube_id')]
    save_cache_config(config)
    
    logger.info(f"Cache: Refresh complete. Cached {cached_count} new songs.")


def get_cached_popular_songs() -> List[Dict[str, Any]]:
    """Get list of popular songs that are cached and ready for instant access."""
    from harmonix_splitter import library as shared_library
    
    popular = []
    for song in get_popular_songs_for_caching():
        youtube_id = song.get('youtube_id')
        
        if youtube_id and is_song_cached(youtube_id):
            metadata = shared_library.get_library_metadata(youtube_id)
            if metadata:
                popular.append({
                    'youtube_id': youtube_id,
                    'title': metadata.get('display_name', song.get('title')),
                    'duration': metadata.get('duration', 0),
                    'stems': metadata.get('stems', []),
                    'instant': True
                })
    
    return popular


def start_background_cache_worker():
    """
    Start a background worker that refreshes the cache overnight.
    This should be called at app startup.
    """
    def worker():
        while True:
            try:
                config = load_cache_config()
                
                # Check if refresh is needed
                last_refresh = config.get('last_refresh')
                refresh_interval = config.get('refresh_interval_hours', 24)
                
                should_refresh = False
                if not last_refresh:
                    should_refresh = True
                else:
                    last_dt = datetime.fromisoformat(last_refresh)
                    if datetime.now() - last_dt > timedelta(hours=refresh_interval):
                        should_refresh = True
                
                if should_refresh:
                    logger.info("Cache: Starting scheduled cache refresh")
                    refresh_popular_cache(max_songs=5)  # Process 5 songs at a time
                
            except Exception as e:
                logger.error(f"Cache worker error: {e}")
            
            # Check every hour
            time.sleep(3600)
    
    thread = threading.Thread(target=worker, daemon=True, name="CacheWorker")
    thread.start()
    logger.info("Cache: Background cache worker started")
