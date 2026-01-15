"""
Harmonix Shared Content Library
Manages deduplicated content storage for YouTube videos.
Enables instant access to already-processed content.
"""

import json
import logging
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Any
from threading import Lock
import re

logger = logging.getLogger(__name__)

# Thread-safe lock for library operations
library_lock = Lock()

# Base data directory
DATA_DIR = Path(__file__).parent.parent.parent / "data"
LIBRARY_DIR = DATA_DIR / "library"
ARCHIVE_DIR = DATA_DIR / "archive"
USERS_DIR = DATA_DIR / "outputs" / "users"

# Ensure directories exist
LIBRARY_DIR.mkdir(parents=True, exist_ok=True)
ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)


def extract_youtube_id(url: str) -> Optional[str]:
    """Extract YouTube video ID from various URL formats."""
    if not url:
        return None
    
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/|youtube\.com\/v\/)([a-zA-Z0-9_-]{11})',
        r'youtube\.com\/shorts\/([a-zA-Z0-9_-]{11})',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None


def get_library_path(youtube_id: str) -> Path:
    """Get the library folder path for a YouTube video."""
    return LIBRARY_DIR / youtube_id


def get_user_links_file(username: str) -> Path:
    """Get the library links file for a user."""
    user_dir = USERS_DIR / username
    user_dir.mkdir(parents=True, exist_ok=True)
    return user_dir / "library_links.json"


def load_user_links(username: str) -> Dict[str, Any]:
    """Load user's library links."""
    links_file = get_user_links_file(username)
    if links_file.exists():
        try:
            with open(links_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load user links for {username}: {e}")
    return {"links": {}, "created_at": datetime.now().isoformat()}


def save_user_links(username: str, links_data: Dict[str, Any]) -> bool:
    """Save user's library links."""
    links_file = get_user_links_file(username)
    try:
        links_data["updated_at"] = datetime.now().isoformat()
        with open(links_file, 'w', encoding='utf-8') as f:
            json.dump(links_data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"Failed to save user links for {username}: {e}")
        return False


def get_user_library_links(username: str) -> Dict[str, Any]:
    """
    Get user's library links (just the links dictionary).
    Returns a dict mapping youtube_id -> link_info.
    """
    if not username:
        return {}
    links_data = load_user_links(username)
    return links_data.get("links", {})


def check_library_exists(youtube_id: str) -> Optional[Dict[str, Any]]:
    """
    Check if content already exists in the shared library.
    Returns metadata if exists, None otherwise.
    """
    library_path = get_library_path(youtube_id)
    metadata_file = library_path / "metadata.json"
    
    if metadata_file.exists():
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            # Verify essential files exist
            required_files = ['instrumental', 'vocals']
            stems_exist = False
            for stem in required_files:
                if list(library_path.glob(f"*_{stem}.*")):
                    stems_exist = True
                    break
            
            if stems_exist:
                logger.info(f"Found existing library content for YouTube ID: {youtube_id}")
                return metadata
        except Exception as e:
            logger.error(f"Error checking library for {youtube_id}: {e}")
    
    return None


def get_library_stems(youtube_id: str) -> Dict[str, str]:
    """Get available stems for a library item."""
    library_path = get_library_path(youtube_id)
    stems = {}
    
    valid_stem_types = {'vocals', 'drums', 'bass', 'guitar', 'piano', 'other', 
                        'instrumental', 'synth', 'strings', 'melody', 
                        'accompaniment', 'percussion', 'lead', 'background', 'original'}
    
    for stem_file in library_path.glob("*.mp3"):
        parts = stem_file.stem.rsplit('_', 1)
        if len(parts) == 2 and parts[1].lower() in valid_stem_types:
            stems[parts[1]] = str(stem_file)
    
    for stem_file in library_path.glob("*.wav"):
        parts = stem_file.stem.rsplit('_', 1)
        if len(parts) == 2 and parts[1].lower() in valid_stem_types:
            if parts[1] not in stems:  # Prefer MP3 if both exist
                stems[parts[1]] = str(stem_file)
    
    return stems


def link_to_user_library(username: str, youtube_id: str, job_id: str, 
                          display_name: Optional[str] = None, custom_data: Optional[Dict] = None) -> bool:
    """
    Link a shared library item to a user's library.
    This gives the user access to the content without duplicating files.
    """
    with library_lock:
        try:
            # Load existing links
            links_data = load_user_links(username)
            
            # Add new link
            links_data["links"][job_id] = {
                "youtube_id": youtube_id,
                "display_name": display_name,
                "linked_at": datetime.now().isoformat(),
                "is_library_link": True,
                **(custom_data or {})
            }
            
            # Save updated links
            save_user_links(username, links_data)
            
            # Update library usage count
            update_library_usage(youtube_id, increment=True)
            
            logger.info(f"Linked {youtube_id} to user {username} as job {job_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to link library item: {e}")
            return False


def unlink_from_user_library(username: str, job_id: str) -> Optional[str]:
    """
    Unlink a library item from user's library.
    Returns the youtube_id if it was a library link, None otherwise.
    """
    with library_lock:
        try:
            links_data = load_user_links(username)
            
            if job_id in links_data.get("links", {}):
                link_info = links_data["links"].pop(job_id)
                save_user_links(username, links_data)
                
                youtube_id = link_info.get("youtube_id")
                if youtube_id:
                    update_library_usage(youtube_id, increment=False)
                    logger.info(f"Unlinked {youtube_id} from user {username}")
                    return youtube_id
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to unlink library item: {e}")
            return None


def get_library_metadata_path(youtube_id: str) -> Path:
    """Get path to library item metadata."""
    return get_library_path(youtube_id) / "metadata.json"


def get_library_metadata(youtube_id: str) -> Optional[Dict[str, Any]]:
    """Get metadata for a library item."""
    metadata_file = get_library_metadata_path(youtube_id)
    try:
        if metadata_file.exists():
            with open(metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    except Exception as e:
        logger.error(f"Failed to read library metadata for {youtube_id}: {e}")
        return None


def get_library_usage(youtube_id: str) -> int:
    """Get current usage count for a library item."""
    metadata = get_library_metadata(youtube_id)
    if metadata:
        return metadata.get("usage_count", 0)
    return 0


def update_library_usage(youtube_id: str, increment: bool = True) -> int:
    """Update usage count for a library item."""
    metadata_file = get_library_metadata_path(youtube_id)
    
    try:
        if metadata_file.exists():
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
        else:
            metadata = {}
        
        current_count = metadata.get("usage_count", 0)
        new_count = current_count + (1 if increment else -1)
        new_count = max(0, new_count)  # Never go below 0
        
        metadata["usage_count"] = new_count
        metadata["last_usage_update"] = datetime.now().isoformat()
        
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        return new_count
        
    except Exception as e:
        logger.error(f"Failed to update usage count for {youtube_id}: {e}")
        return 0


def create_library_entry(youtube_id: str, metadata: Dict[str, Any]) -> Path:
    """
    Create a new entry in the shared library.
    Returns the library path for storing files.
    """
    library_path = get_library_path(youtube_id)
    library_path.mkdir(parents=True, exist_ok=True)
    
    # Save metadata
    metadata_file = library_path / "metadata.json"
    full_metadata = {
        "youtube_id": youtube_id,
        "created_at": datetime.now().isoformat(),
        "usage_count": 0,
        **metadata
    }
    
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(full_metadata, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Created library entry for {youtube_id}")
    return library_path


def archive_library_item(youtube_id: str, reason: str = "user_deleted") -> bool:
    """
    Move a library item to archive (soft delete).
    Only moves if usage_count is 0.
    """
    library_path = get_library_path(youtube_id)
    
    if not library_path.exists():
        return False
    
    # Check usage count
    metadata_file = library_path / "metadata.json"
    if metadata_file.exists():
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        if metadata.get("usage_count", 0) > 0:
            logger.warning(f"Cannot archive {youtube_id}: still in use by {metadata['usage_count']} users")
            return False
    
    # Create dated archive folder
    date_folder = ARCHIVE_DIR / datetime.now().strftime("%Y-%m-%d")
    date_folder.mkdir(parents=True, exist_ok=True)
    
    archive_path = date_folder / youtube_id
    
    try:
        # Update metadata with archive info
        if metadata_file.exists():
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            metadata["archived_at"] = datetime.now().isoformat()
            metadata["archive_reason"] = reason
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        # Move to archive
        shutil.move(str(library_path), str(archive_path))
        logger.info(f"Archived library item {youtube_id} to {archive_path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to archive {youtube_id}: {e}")
        return False


def restore_from_archive(youtube_id: str) -> bool:
    """Restore an archived library item."""
    # Search for the item in archive
    for date_folder in ARCHIVE_DIR.iterdir():
        if date_folder.is_dir():
            archived_path = date_folder / youtube_id
            if archived_path.exists():
                try:
                    library_path = get_library_path(youtube_id)
                    shutil.move(str(archived_path), str(library_path))
                    
                    # Update metadata
                    metadata_file = library_path / "metadata.json"
                    if metadata_file.exists():
                        with open(metadata_file, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                        metadata["restored_at"] = datetime.now().isoformat()
                        metadata.pop("archived_at", None)
                        metadata.pop("archive_reason", None)
                        with open(metadata_file, 'w', encoding='utf-8') as f:
                            json.dump(metadata, f, ensure_ascii=False, indent=2)
                    
                    logger.info(f"Restored {youtube_id} from archive")
                    return True
                    
                except Exception as e:
                    logger.error(f"Failed to restore {youtube_id}: {e}")
                    return False
    
    logger.warning(f"Could not find {youtube_id} in archive")
    return False


def get_archived_items() -> List[Dict[str, Any]]:
    """Get all archived items with their metadata."""
    archived = []
    
    for date_folder in sorted(ARCHIVE_DIR.iterdir(), reverse=True):
        if date_folder.is_dir() and date_folder.name != ".DS_Store":
            for item_folder in date_folder.iterdir():
                if item_folder.is_dir():
                    metadata_file = item_folder / "metadata.json"
                    try:
                        if metadata_file.exists():
                            with open(metadata_file, 'r', encoding='utf-8') as f:
                                metadata = json.load(f)
                        else:
                            metadata = {}
                        
                        archived.append({
                            "youtube_id": item_folder.name,
                            "archived_date": date_folder.name,
                            "archive_path": str(item_folder),
                            "display_name": metadata.get("display_name", metadata.get("title", item_folder.name)),
                            "usage_count": metadata.get("usage_count", 0),
                            "archived_at": metadata.get("archived_at"),
                            "archive_reason": metadata.get("archive_reason", "unknown"),
                            "original_url": metadata.get("source_url"),
                            "size_mb": sum(f.stat().st_size for f in item_folder.rglob("*") if f.is_file()) / (1024 * 1024)
                        })
                    except Exception as e:
                        logger.error(f"Error reading archived item {item_folder}: {e}")
    
    return archived


def permanently_delete_archived(youtube_id: str) -> bool:
    """Permanently delete an archived item (admin only, with confirmation)."""
    for date_folder in ARCHIVE_DIR.iterdir():
        if date_folder.is_dir():
            archived_path = date_folder / youtube_id
            if archived_path.exists():
                try:
                    shutil.rmtree(str(archived_path))
                    logger.warning(f"Permanently deleted archived item: {youtube_id}")
                    
                    # Remove empty date folders
                    if not any(date_folder.iterdir()):
                        date_folder.rmdir()
                    
                    return True
                except Exception as e:
                    logger.error(f"Failed to permanently delete {youtube_id}: {e}")
                    return False
    
    return False


def get_library_stats() -> Dict[str, Any]:
    """Get statistics about the shared library."""
    total_items = 0
    total_size = 0
    total_usage = 0
    items_by_usage = {"unused": 0, "low": 0, "medium": 0, "high": 0}
    
    for item_folder in LIBRARY_DIR.iterdir():
        if item_folder.is_dir() and item_folder.name != ".DS_Store":
            total_items += 1
            
            # Calculate size
            size = sum(f.stat().st_size for f in item_folder.rglob("*") if f.is_file())
            total_size += size
            
            # Get usage
            metadata_file = item_folder / "metadata.json"
            if metadata_file.exists():
                try:
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                    usage = metadata.get("usage_count", 0)
                    total_usage += usage
                    
                    if usage == 0:
                        items_by_usage["unused"] += 1
                    elif usage < 3:
                        items_by_usage["low"] += 1
                    elif usage < 10:
                        items_by_usage["medium"] += 1
                    else:
                        items_by_usage["high"] += 1
                except:
                    items_by_usage["unused"] += 1
    
    # Archive stats
    archived_items = len(get_archived_items())
    
    return {
        "total_items": total_items,
        "total_size_mb": round(total_size / (1024 * 1024), 2),
        "total_usage": total_usage,
        "average_usage": round(total_usage / max(total_items, 1), 2),
        "items_by_usage": items_by_usage,
        "archived_items": archived_items
    }


def get_all_library_items() -> List[Dict[str, Any]]:
    """Get all items in the shared library."""
    items = []
    
    for item_folder in LIBRARY_DIR.iterdir():
        if item_folder.is_dir() and item_folder.name != ".DS_Store":
            metadata_file = item_folder / "metadata.json"
            try:
                if metadata_file.exists():
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                else:
                    metadata = {"youtube_id": item_folder.name}
                
                # Get file info
                stems = get_library_stems(item_folder.name)
                
                items.append({
                    "youtube_id": item_folder.name,
                    "display_name": metadata.get("display_name", metadata.get("title", item_folder.name)),
                    "usage_count": metadata.get("usage_count", 0),
                    "created_at": metadata.get("created_at"),
                    "stems": list(stems.keys()),
                    "has_lyrics": bool(list(item_folder.glob("*_lyrics*.json"))),
                    "size_mb": sum(f.stat().st_size for f in item_folder.rglob("*") if f.is_file()) / (1024 * 1024)
                })
            except Exception as e:
                logger.error(f"Error reading library item {item_folder}: {e}")
    
    return sorted(items, key=lambda x: x.get("usage_count", 0), reverse=True)


def is_user_link(username: str, job_id: str) -> bool:
    """Check if a job is a library link for a user."""
    links_data = load_user_links(username)
    return job_id in links_data.get("links", {})


def get_user_link_info(username: str, job_id: str) -> Optional[Dict[str, Any]]:
    """Get link info for a user's job."""
    links_data = load_user_links(username)
    return links_data.get("links", {}).get(job_id)
