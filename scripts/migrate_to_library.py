#!/usr/bin/env python3
"""
Migration script to move existing YouTube-processed content to the shared library.

This script:
1. Scans all user output folders for YouTube-processed content
2. Moves unique content to the shared library
3. Creates library links for users
4. Removes duplicate content (keeps only in library)

Run with: python scripts/migrate_to_library.py [--dry-run]
"""

import sys
import json
import shutil
import argparse
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from harmonix_splitter import library as shared_library


def find_youtube_jobs(user_dir: Path) -> list:
    """Find all jobs in a user directory that came from YouTube."""
    youtube_jobs = []
    
    for job_dir in user_dir.iterdir():
        if not job_dir.is_dir() or job_dir.name.startswith('.'):
            continue
            
        # Check for metadata.json with YouTube info
        metadata_file = job_dir / 'metadata.json'
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                
                source_url = metadata.get('source_url', '')
                youtube_id = None
                
                # Check if it's a YouTube URL
                if 'youtube.com' in source_url or 'youtu.be' in source_url:
                    youtube_id = shared_library.extract_youtube_id(source_url)
                
                # Also check for youtube_video_id in metadata
                if not youtube_id:
                    youtube_id = metadata.get('youtube_video_id')
                
                if youtube_id:
                    youtube_jobs.append({
                        'job_dir': job_dir,
                        'job_id': job_dir.name,
                        'youtube_id': youtube_id,
                        'metadata': metadata
                    })
                    
            except Exception as e:
                print(f"  Warning: Could not read {metadata_file}: {e}")
    
    return youtube_jobs


def migrate_to_library(job_info: dict, dry_run: bool = True) -> bool:
    """Migrate a single job to the shared library."""
    job_dir = job_info['job_dir']
    youtube_id = job_info['youtube_id']
    metadata = job_info['metadata']
    
    # Check if already in library
    if shared_library.check_library_exists(youtube_id):
        print(f"    Already in library: {youtube_id}")
        return False  # Already migrated
    
    # Get library path
    library_path = shared_library.get_library_path(youtube_id)
    
    if dry_run:
        print(f"    Would move: {job_dir} -> {library_path}")
        return True
    
    # Create library directory
    library_path.mkdir(parents=True, exist_ok=True)
    
    # Copy all files to library
    for file in job_dir.iterdir():
        if file.is_file():
            dest = library_path / file.name
            shutil.copy2(file, dest)
    
    # Update metadata in library
    library_metadata_file = library_path / 'metadata.json'
    library_metadata = {
        **metadata,
        'youtube_id': youtube_id,
        'migrated_at': datetime.now().isoformat(),
        'migrated_from': str(job_dir),
        'usage_count': 1  # Start with 1 for the original user
    }
    
    with open(library_metadata_file, 'w', encoding='utf-8') as f:
        json.dump(library_metadata, f, ensure_ascii=False, indent=2)
    
    print(f"    Migrated to library: {youtube_id}")
    return True


def link_user_to_library(username: str, job_id: str, youtube_id: str, 
                         metadata: dict, dry_run: bool = True) -> bool:
    """Create a library link for a user."""
    if dry_run:
        print(f"    Would link user '{username}' to library item {youtube_id}")
        return True
    
    display_name = metadata.get('display_name', metadata.get('title', 'Unknown'))
    
    success = shared_library.link_to_user_library(
        username=username,
        youtube_id=youtube_id,
        job_id=job_id,
        display_name=display_name,
        custom_data={
            'migrated': True,
            'original_job_id': job_id
        }
    )
    
    if success:
        print(f"    Linked user '{username}' to {youtube_id}")
    
    return success


def remove_user_copy(job_dir: Path, dry_run: bool = True) -> bool:
    """Remove the user's copy of content now in library."""
    if dry_run:
        print(f"    Would remove: {job_dir}")
        return True
    
    shutil.rmtree(job_dir)
    print(f"    Removed user copy: {job_dir}")
    return True


def main():
    parser = argparse.ArgumentParser(description='Migrate YouTube content to shared library')
    parser.add_argument('--dry-run', action='store_true', default=True,
                        help='Show what would be done without making changes (default)')
    parser.add_argument('--execute', action='store_true',
                        help='Actually perform the migration')
    parser.add_argument('--keep-originals', action='store_true',
                        help='Keep original user files after migration')
    args = parser.parse_args()
    
    dry_run = not args.execute
    
    if dry_run:
        print("=" * 60)
        print("DRY RUN MODE - No changes will be made")
        print("Use --execute to actually perform the migration")
        print("=" * 60)
    else:
        print("=" * 60)
        print("EXECUTING MIGRATION - Changes will be made!")
        print("=" * 60)
        response = input("Are you sure? (yes/no): ")
        if response.lower() != 'yes':
            print("Aborted.")
            return
    
    # Get data directory
    data_dir = Path(__file__).parent.parent / 'data'
    users_output_dir = data_dir / 'outputs' / 'users'
    
    if not users_output_dir.exists():
        print(f"User outputs directory not found: {users_output_dir}")
        return
    
    print(f"\nScanning user outputs in: {users_output_dir}")
    
    # Track what we find
    stats = {
        'users_scanned': 0,
        'youtube_jobs_found': 0,
        'unique_videos': set(),
        'duplicates_found': 0,
        'migrated': 0,
        'linked': 0,
        'removed': 0
    }
    
    # Track which YouTube IDs have been migrated and by whom
    video_owners = {}  # youtube_id -> first user who had it
    
    # First pass: Find all YouTube content
    print("\n--- Pass 1: Finding YouTube content ---")
    for user_dir in users_output_dir.iterdir():
        if not user_dir.is_dir() or user_dir.name.startswith('.'):
            continue
        
        username = user_dir.name
        stats['users_scanned'] += 1
        
        youtube_jobs = find_youtube_jobs(user_dir)
        
        if youtube_jobs:
            print(f"\nUser: {username} ({len(youtube_jobs)} YouTube jobs)")
            
            for job in youtube_jobs:
                stats['youtube_jobs_found'] += 1
                youtube_id = job['youtube_id']
                
                if youtube_id not in video_owners:
                    video_owners[youtube_id] = {
                        'first_user': username,
                        'first_job': job,
                        'other_users': []
                    }
                    stats['unique_videos'].add(youtube_id)
                else:
                    video_owners[youtube_id]['other_users'].append({
                        'username': username,
                        'job': job
                    })
                    stats['duplicates_found'] += 1
                
                print(f"  - {job['metadata'].get('display_name', 'Unknown')} ({youtube_id})")
    
    print(f"\n--- Summary ---")
    print(f"Users scanned: {stats['users_scanned']}")
    print(f"YouTube jobs found: {stats['youtube_jobs_found']}")
    print(f"Unique videos: {len(stats['unique_videos'])}")
    print(f"Duplicates found: {stats['duplicates_found']}")
    
    if not stats['unique_videos']:
        print("\nNo YouTube content to migrate.")
        return
    
    # Second pass: Migrate content
    print("\n--- Pass 2: Migrating to shared library ---")
    for youtube_id, info in video_owners.items():
        print(f"\nProcessing: {youtube_id}")
        
        first_job = info['first_job']
        
        # Migrate the first copy to library
        migrated = migrate_to_library(first_job, dry_run)
        if migrated:
            stats['migrated'] += 1
        
        # Link first user to library
        linked = link_user_to_library(
            info['first_user'],
            first_job['job_id'],
            youtube_id,
            first_job['metadata'],
            dry_run
        )
        if linked:
            stats['linked'] += 1
        
        # Remove first user's copy (if not keeping originals)
        if not args.keep_originals and migrated:
            remove_user_copy(first_job['job_dir'], dry_run)
            stats['removed'] += 1
        
        # Handle other users (duplicates)
        for other in info['other_users']:
            print(f"  Duplicate for user: {other['username']}")
            
            # Link to library
            linked = link_user_to_library(
                other['username'],
                other['job']['job_id'],
                youtube_id,
                other['job']['metadata'],
                dry_run
            )
            if linked:
                stats['linked'] += 1
            
            # Increment usage count
            if not dry_run:
                shared_library.update_library_usage(youtube_id, increment=True)
            
            # Remove duplicate
            if not args.keep_originals:
                remove_user_copy(other['job']['job_dir'], dry_run)
                stats['removed'] += 1
    
    print("\n" + "=" * 60)
    print("Migration Complete!")
    print(f"  Videos migrated to library: {stats['migrated']}")
    print(f"  User library links created: {stats['linked']}")
    print(f"  Duplicate files removed: {stats['removed']}")
    
    if dry_run:
        print("\n(This was a dry run - use --execute to apply changes)")


if __name__ == '__main__':
    main()
