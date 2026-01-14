"""
Harmonix Authentication System
User management, authentication, and admin functionality
"""

import os
import json
import hashlib
import secrets
from datetime import datetime, timedelta
from pathlib import Path
from functools import wraps
from flask import session, redirect, url_for, request, flash

# User data storage (JSON file-based for simplicity)
DATA_DIR = Path(__file__).parent.parent.parent / "data"
USERS_FILE = DATA_DIR / "users.json"
CONTACTS_FILE = DATA_DIR / "contacts.json"

# Ensure data directory exists
DATA_DIR.mkdir(parents=True, exist_ok=True)

# ==================== PLAN DEFINITIONS ====================

PLANS = {
    "free": {
        "name": "Free",
        "price": 0,
        "price_display": "$0/month",
        "songs_per_month": 3,
        "stems": 4,  # vocals, drums, bass, other
        "stem_types": ["vocals", "drums", "bass", "other"],
        "lyrics": "basic",  # basic lyrics extraction
        "export_formats": ["mp3"],
        "commercial_use": False,
        "priority_processing": False,
        "api_access": False,
        "custom_models": False,
        "dedicated_support": False,
        "features": [
            "3 songs per month",
            "4-stem separation",
            "Basic lyrics extraction",
            "No commercial use",
            "MP3 export only"
        ]
    },
    "creator": {
        "name": "Creator",
        "price": 19,
        "price_display": "$19/month",
        "songs_per_month": 50,
        "stems": 6,  # vocals, drums, bass, guitar, piano, other
        "stem_types": ["vocals", "drums", "bass", "guitar", "piano", "other"],
        "lyrics": "advanced",  # with timing
        "export_formats": ["mp3", "wav", "flac"],
        "commercial_use": True,  # limited
        "priority_processing": True,
        "api_access": False,
        "custom_models": False,
        "dedicated_support": False,
        "features": [
            "50 songs per month",
            "6-stem separation",
            "Advanced lyrics + timing",
            "All export formats",
            "Priority processing"
        ]
    },
    "studio": {
        "name": "Studio",
        "price": 49,
        "price_display": "$49/month",
        "songs_per_month": -1,  # unlimited
        "stems": 6,
        "stem_types": ["vocals", "drums", "bass", "guitar", "piano", "other"],
        "lyrics": "advanced",
        "export_formats": ["mp3", "wav", "flac", "stems_zip"],
        "commercial_use": True,  # full
        "priority_processing": True,
        "api_access": True,
        "custom_models": True,
        "dedicated_support": True,
        "features": [
            "Unlimited songs",
            "6-stem + custom models",
            "API access",
            "Commercial license",
            "Dedicated support"
        ]
    }
}


def get_plan(plan_name: str) -> dict:
    """Get plan details by name"""
    return PLANS.get(plan_name, PLANS["free"])


def get_all_plans() -> dict:
    """Get all available plans"""
    return PLANS


def check_usage_limit(username: str) -> dict:
    """Check if user has reached their usage limit for the month"""
    users = load_users()
    if username not in users:
        return {"allowed": False, "reason": "User not found"}
    
    user = users[username]
    plan = get_plan(user.get("plan", "free"))
    
    # Get current month usage
    usage = user.get("usage", {})
    current_month = datetime.now().strftime("%Y-%m")
    month_usage = usage.get("monthly", {}).get(current_month, 0)
    
    # Check limit (-1 means unlimited)
    limit = plan["songs_per_month"]
    if limit == -1:
        return {"allowed": True, "used": month_usage, "limit": "unlimited", "remaining": "unlimited"}
    
    remaining = max(0, limit - month_usage)
    
    return {
        "allowed": month_usage < limit,
        "used": month_usage,
        "limit": limit,
        "remaining": remaining,
        "reason": f"Monthly limit reached ({limit} songs)" if month_usage >= limit else None
    }


def increment_song_usage(username: str) -> bool:
    """Increment the song usage counter for a user"""
    users = load_users()
    if username not in users:
        return False
    
    # Initialize usage structure if needed
    if "usage" not in users[username]:
        users[username]["usage"] = {"songs_processed": 0, "stems_downloaded": 0, "monthly": {}}
    if "monthly" not in users[username]["usage"]:
        users[username]["usage"]["monthly"] = {}
    
    # Increment monthly counter
    current_month = datetime.now().strftime("%Y-%m")
    users[username]["usage"]["monthly"][current_month] = users[username]["usage"]["monthly"].get(current_month, 0) + 1
    
    # Increment total counter
    users[username]["usage"]["songs_processed"] = users[username]["usage"].get("songs_processed", 0) + 1
    
    save_users(users)
    return True


def get_user_stats(username: str) -> dict:
    """Get detailed user statistics"""
    users = load_users()
    if username not in users:
        return {}
    
    user = users[username]
    plan = get_plan(user.get("plan", "free"))
    usage = user.get("usage", {})
    
    current_month = datetime.now().strftime("%Y-%m")
    month_usage = usage.get("monthly", {}).get(current_month, 0)
    
    limit = plan["songs_per_month"]
    
    return {
        "plan": user.get("plan", "free"),
        "plan_name": plan["name"],
        "songs_this_month": month_usage,
        "songs_limit": limit if limit != -1 else "unlimited",
        "songs_remaining": "unlimited" if limit == -1 else max(0, limit - month_usage),
        "total_songs_processed": usage.get("songs_processed", 0),
        "total_stems_downloaded": usage.get("stems_downloaded", 0),
        "stems_available": plan["stems"],
        "stem_types": plan["stem_types"],
        "export_formats": plan["export_formats"],
        "has_api_access": plan["api_access"],
        "has_commercial_license": plan["commercial_use"],
        "member_since": user.get("created_at"),
        "last_login": user.get("last_login")
    }


def upgrade_plan(username: str, new_plan: str) -> bool:
    """Upgrade user's plan"""
    if new_plan not in PLANS:
        return False
    
    users = load_users()
    if username not in users:
        return False
    
    users[username]["plan"] = new_plan
    users[username]["plan_upgraded_at"] = datetime.now().isoformat()
    save_users(users)
    return True


# ==================== PASSWORD FUNCTIONS ====================


def hash_password(password: str, salt: str | None = None) -> tuple[str, str]:
    """Hash a password with salt"""
    if salt is None:
        salt = secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return hashed.hex(), salt


def verify_password(password: str, hashed: str, salt: str) -> bool:
    """Verify a password against its hash"""
    new_hash, _ = hash_password(password, salt)
    return new_hash == hashed


def load_users() -> dict:
    """Load users from JSON file"""
    if not USERS_FILE.exists():
        # Create default admin user
        default_users = {
            "admin": {
                "email": "admin@harmonix.app",
                "password_hash": "",
                "salt": "",
                "role": "admin",
                "name": "Administrator",
                "created_at": datetime.now().isoformat(),
                "last_login": None,
                "is_active": True,
                "plan": "studio",
                "usage": {"songs_processed": 0, "stems_downloaded": 0}
            }
        }
        # Set default admin password
        pw_hash, salt = hash_password("admin123")
        default_users["admin"]["password_hash"] = pw_hash
        default_users["admin"]["salt"] = salt
        save_users(default_users)
        return default_users
    
    with open(USERS_FILE, 'r') as f:
        return json.load(f)


def save_users(users: dict):
    """Save users to JSON file"""
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2, default=str)


def load_contacts() -> list:
    """Load contact submissions from JSON file"""
    if not CONTACTS_FILE.exists():
        return []
    with open(CONTACTS_FILE, 'r') as f:
        return json.load(f)


def save_contacts(contacts: list):
    """Save contact submissions to JSON file"""
    with open(CONTACTS_FILE, 'w') as f:
        json.dump(contacts, f, indent=2, default=str)


def create_user(username: str, email: str, password: str, name: str = "", role: str = "user") -> dict:
    """Create a new user"""
    users = load_users()
    
    if username in users:
        raise ValueError("Username already exists")
    
    # Check if email already exists
    for user in users.values():
        if user.get("email") == email:
            raise ValueError("Email already registered")
    
    pw_hash, salt = hash_password(password)
    
    users[username] = {
        "email": email,
        "password_hash": pw_hash,
        "salt": salt,
        "role": role,
        "name": name or username,
        "created_at": datetime.now().isoformat(),
        "last_login": None,
        "is_active": True,
        "plan": "free",
        "usage": {"songs_processed": 0, "stems_downloaded": 0}
    }
    
    save_users(users)
    return users[username]


def authenticate_user(username: str, password: str) -> dict | None:
    """Authenticate a user and return their data"""
    users = load_users()
    
    # Allow login with username or email
    user_data = None
    actual_username = None
    
    if username in users:
        user_data = users[username]
        actual_username = username
    else:
        # Check by email
        for uname, data in users.items():
            if data.get("email") == username:
                user_data = data
                actual_username = uname
                break
    
    if not user_data:
        return None
    
    if not user_data.get("is_active", True):
        return None
    
    if verify_password(password, user_data["password_hash"], user_data["salt"]):
        # Update last login
        users[actual_username]["last_login"] = datetime.now().isoformat()
        save_users(users)
        return {"username": actual_username, **user_data}
    
    return None


def get_user(username: str) -> dict | None:
    """Get user data by username"""
    users = load_users()
    if username in users:
        return {"username": username, **users[username]}
    return None


def update_user(username: str, updates: dict) -> dict | None:
    """Update user data"""
    users = load_users()
    if username not in users:
        return None
    
    # Don't allow updating sensitive fields directly
    safe_fields = ["name", "email", "plan", "is_active", "role", "avatar", "bio"]
    for key, value in updates.items():
        if key in safe_fields:
            users[username][key] = value
    
    save_users(users)
    return users[username]


def change_password(username: str, old_password: str, new_password: str) -> bool:
    """Change user password"""
    users = load_users()
    if username not in users:
        return False
    
    user = users[username]
    if not verify_password(old_password, user["password_hash"], user["salt"]):
        return False
    
    pw_hash, salt = hash_password(new_password)
    users[username]["password_hash"] = pw_hash
    users[username]["salt"] = salt
    save_users(users)
    return True


def delete_user(username: str) -> bool:
    """Delete a user"""
    users = load_users()
    if username not in users:
        return False
    if username == "admin":
        return False  # Can't delete admin
    del users[username]
    save_users(users)
    return True


def get_all_users() -> list:
    """Get all users (for admin)"""
    users = load_users()
    return [{"id": k, "username": k, **{key: val for key, val in v.items() if key not in ['password_hash', 'salt']}} for k, v in users.items()]


def get_user_by_id(user_id: str) -> dict | None:
    """Get user by ID (which is the username)"""
    return get_user(user_id)


def get_user_by_email(email: str) -> dict | None:
    """Get user by email address"""
    users = load_users()
    for username, data in users.items():
        if data.get("email") == email:
            return {"id": username, "username": username, **data}
    return None


def get_contact_by_id(contact_id: str) -> dict | None:
    """Get a contact by ID"""
    contacts = load_contacts()
    for contact in contacts:
        if contact.get("id") == contact_id:
            return contact
    return None


def increment_usage(username: str, field: str):
    """Increment a usage counter for a user"""
    users = load_users()
    if username in users:
        if "usage" not in users[username]:
            users[username]["usage"] = {"songs_processed": 0, "stems_downloaded": 0}
        users[username]["usage"][field] = users[username]["usage"].get(field, 0) + 1
        save_users(users)


def add_contact_submission(name: str, email: str, subject: str, message: str, 
                           category: str = "general") -> dict:
    """Add a contact form submission"""
    contacts = load_contacts()
    
    submission = {
        "id": secrets.token_hex(8),
        "name": name,
        "email": email,
        "subject": subject,
        "message": message,
        "category": category,
        "created_at": datetime.now().isoformat(),
        "status": "new",
        "replied": False,
        "reply": None,
        "reply_at": None
    }
    
    contacts.append(submission)
    save_contacts(contacts)
    return submission


def get_all_contacts() -> list:
    """Get all contact submissions (for admin)"""
    return load_contacts()


def update_contact(contact_id: str, updates: dict) -> dict | None:
    """Update a contact submission"""
    contacts = load_contacts()
    for i, contact in enumerate(contacts):
        if contact["id"] == contact_id:
            contacts[i].update(updates)
            save_contacts(contacts)
            return contacts[i]
    return None


def reply_to_contact(contact_id: str, reply: str) -> dict | None:
    """Reply to a contact submission"""
    return update_contact(contact_id, {
        "replied": True,
        "reply": reply,
        "reply_at": datetime.now().isoformat(),
        "status": "replied"
    })


def delete_contact(contact_id: str) -> bool:
    """Delete a contact submission"""
    contacts = load_contacts()
    for i, contact in enumerate(contacts):
        if contact["id"] == contact_id:
            contacts.pop(i)
            save_contacts(contacts)
            return True
    return False


def get_admin_stats() -> dict:
    """Get admin dashboard statistics"""
    users = load_users()
    contacts = load_contacts()
    
    now = datetime.now()
    week_ago = now - timedelta(days=7)
    today = now.strftime("%Y-%m-%d")
    
    # Count users by plan
    plan_counts = {"free": 0, "creator": 0, "studio": 0}
    total_songs = 0
    songs_today = 0
    new_users_week = 0
    
    for username, user in users.items():
        # Count by plan
        plan = user.get("plan", "free")
        if plan in plan_counts:
            plan_counts[plan] += 1
        
        # Count songs
        usage = user.get("usage", {})
        total_songs += usage.get("songs_processed", 0)
        
        # Check for daily processing (simplified - would need actual tracking)
        songs_today = 0  # Would need daily tracking to implement
        
        # Count new users this week
        created_at = user.get("created_at")
        if created_at:
            try:
                user_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                if user_date.replace(tzinfo=None) > week_ago:
                    new_users_week += 1
            except:
                pass
    
    # Calculate monthly revenue
    monthly_revenue = (plan_counts["creator"] * 19) + (plan_counts["studio"] * 49)
    
    # Count pending contacts
    pending_contacts = sum(1 for c in contacts if c.get("status") == "new" or not c.get("replied"))
    
    return {
        "total_users": len(users),
        "new_users_week": new_users_week,
        "free_users": plan_counts["free"],
        "creator_users": plan_counts["creator"],
        "studio_users": plan_counts["studio"],
        "total_songs": total_songs,
        "songs_today": songs_today,
        "pending_contacts": pending_contacts,
        "total_contacts": len(contacts),
        "monthly_revenue": monthly_revenue
    }


# Flask decorators for authentication

def login_required(f):
    """Decorator to require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login', next=request.url))
        if session.get('user', {}).get('role') != 'admin':
            flash('Admin access required.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function


def get_current_user() -> dict | None:
    """Get the current logged-in user"""
    if 'user' in session:
        return session['user']
    return None


# ==================== ACTIVITY TRACKING ====================

ACTIVITY_FILE = DATA_DIR / "activities.json"


def load_activities() -> dict:
    """Load activities from JSON file"""
    if not ACTIVITY_FILE.exists():
        return {}
    try:
        with open(ACTIVITY_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}


def save_activities(activities: dict):
    """Save activities to JSON file"""
    with open(ACTIVITY_FILE, 'w') as f:
        json.dump(activities, f, indent=2)


def log_activity(username: str, activity_type: str, description: str, metadata: dict = None):
    """
    Log a user activity
    
    activity_type: 'song_processed', 'download', 'login', 'logout', 'upload', 'midi_converted', etc.
    """
    activities = load_activities()
    
    if username not in activities:
        activities[username] = []
    
    activity = {
        "type": activity_type,
        "description": description,
        "timestamp": datetime.now().isoformat(),
        "metadata": metadata or {}
    }
    
    # Add to the beginning of the list (most recent first)
    activities[username].insert(0, activity)
    
    # Keep only the last 100 activities per user
    activities[username] = activities[username][:100]
    
    save_activities(activities)


def get_user_activities(username: str, limit: int = 10) -> list:
    """Get recent activities for a user"""
    activities = load_activities()
    user_activities = activities.get(username, [])
    return user_activities[:limit]


def get_activity_icon(activity_type: str) -> str:
    """Get Font Awesome icon for activity type"""
    icons = {
        'song_processed': 'fa-music',
        'download': 'fa-download',
        'login': 'fa-sign-in-alt',
        'logout': 'fa-sign-out-alt',
        'upload': 'fa-upload',
        'midi_converted': 'fa-file-audio',
        'lyrics_extracted': 'fa-closed-captioning',
        'account_updated': 'fa-user-edit',
        'password_changed': 'fa-key',
        'plan_upgraded': 'fa-crown',
    }
    return icons.get(activity_type, 'fa-circle')


def format_time_ago(timestamp_str: str) -> str:
    """Format a timestamp as 'X time ago'"""
    try:
        timestamp = datetime.fromisoformat(timestamp_str)
        now = datetime.now()
        diff = now - timestamp
        
        seconds = diff.total_seconds()
        
        if seconds < 60:
            return "Just now"
        elif seconds < 3600:
            mins = int(seconds // 60)
            return f"{mins} minute{'s' if mins != 1 else ''} ago"
        elif seconds < 86400:
            hours = int(seconds // 3600)
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif seconds < 604800:
            days = int(seconds // 86400)
            return f"{days} day{'s' if days != 1 else ''} ago"
        elif seconds < 2592000:
            weeks = int(seconds // 604800)
            return f"{weeks} week{'s' if weeks != 1 else ''} ago"
        else:
            return timestamp.strftime("%b %d, %Y")
    except:
        return "Unknown"

