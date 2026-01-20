# 👥 User Management & Authentication

**Complete guide to user accounts, plans, and permissions**

---

## Table of Contents

- [Overview](#overview)
- [User Registration](#user-registration)
- [Authentication](#authentication)
- [User Plans](#user-plans)
- [Plan Features](#plan-features)
- [User Profiles](#user-profiles)
- [Activity Tracking](#activity-tracking)
- [Admin Management](#admin-management)
- [Security](#security)

---

## Overview

Harmonix includes a complete user management system with:

- 📝 **User Registration** - Create accounts with email/password
- 🔐 **Authentication** - Secure login with sessions
- 📊 **Plan Tiers** - Free, Creator, and Studio plans
- 📈 **Usage Tracking** - Monthly processing limits
- 👤 **Profiles** - Customizable user profiles
- 🛡️ **Admin Tools** - User management interface

---

## User Registration

### Registration Fields

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Display name (2-50 chars) |
| `email` | Yes | Valid email address |
| `password` | Yes | Minimum 8 characters |

### Registration Flow

```
1. User visits /register
2. Fills out registration form
3. Server validates input
4. Creates user with unique ID
5. Initializes on "free" plan
6. Sets creation timestamp
7. Logs user in automatically
8. Redirects to dashboard
```

### API Registration

```python
import requests

response = requests.post(
    "http://localhost:8000/auth/register",
    json={
        "name": "John Doe",
        "email": "john@example.com",
        "password": "securepassword123"
    }
)

user = response.json()
print(f"User ID: {user['id']}")
```

### Registration Validation

```python
# Validation rules applied:
- Email must be unique (no duplicate accounts)
- Email must be valid format (contains @)
- Name must be 2-50 characters
- Password must be 8+ characters
- All fields are required
```

---

## Authentication

### Login Methods

**Dashboard Login:**
```
1. Go to /login
2. Enter email and password
3. Click "Sign In"
4. Redirected to dashboard
```

**API Authentication:**
```python
import requests

# Login
response = requests.post(
    "http://localhost:8000/auth/login",
    json={
        "email": "john@example.com",
        "password": "securepassword123"
    }
)

# Response includes session token
session = response.json()
```

### Session Management

Sessions are managed via:
- Secure HTTP-only cookies
- Server-side session storage
- Configurable expiry time
- "Remember me" option

```python
# Session configuration (Flask)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
```

### Logout

```python
# Clear session on logout
session.clear()
```

---

## User Plans

### Plan Tiers

| Plan | Price | Songs/Month | Stems | API Access |
|------|-------|-------------|-------|------------|
| **Free** | $0 | 3 | 4 | ❌ |
| **Creator** | $19/mo | 50 | 6 | ❌ |
| **Studio** | $49/mo | Unlimited | 6 | ✅ |

### Plan Structure

```python
PLANS = {
    "free": {
        "name": "Free",
        "songs_per_month": 3,
        "max_stems": 4,
        "price": 0,
        "features": [
            "Basic stem separation",
            "4 stems (vocals, drums, bass, other)",
            "Standard quality"
        ]
    },
    "creator": {
        "name": "Creator",
        "songs_per_month": 50,
        "max_stems": 6,
        "price": 19,
        "features": [
            "Advanced stem separation",
            "6+ stems including guitar, piano",
            "Studio quality",
            "Priority processing"
        ]
    },
    "studio": {
        "name": "Studio",
        "songs_per_month": -1,  # Unlimited
        "max_stems": 6,
        "price": 49,
        "features": [
            "Unlimited songs",
            "All stem types",
            "Maximum quality",
            "API access",
            "Commercial use license"
        ]
    }
}
```

### Checking Usage

```python
def can_user_process(user_id: str) -> bool:
    """Check if user has remaining quota."""
    user = get_user(user_id)
    plan = PLANS[user.get("plan", "free")]
    
    # Unlimited plan
    if plan["songs_per_month"] == -1:
        return True
    
    # Count this month's usage
    monthly_count = get_monthly_usage(user_id)
    return monthly_count < plan["songs_per_month"]
```

---

## Plan Features

### Free Plan

**Included:**
- ✅ 3 songs per month
- ✅ 4-stem separation (vocals, drums, bass, other)
- ✅ Basic quality mode
- ✅ Web dashboard access
- ✅ Download stems

**Limitations:**
- ❌ No per-instrument separation
- ❌ No API access
- ❌ Standard processing queue

### Creator Plan ($19/month)

**Included:**
- ✅ 50 songs per month
- ✅ 6-stem separation (+ guitar, piano)
- ✅ All quality modes
- ✅ Priority processing queue
- ✅ Lyrics extraction
- ✅ Pitch shifting

**Limitations:**
- ❌ No API access
- ❌ Non-commercial use only

### Studio Plan ($49/month)

**Included:**
- ✅ Unlimited songs
- ✅ All stem types
- ✅ Maximum quality
- ✅ API access with key
- ✅ Commercial use license
- ✅ Priority support
- ✅ Early access to features
- ✅ No watermarks

---

## User Profiles

### Profile Fields

```python
user = {
    "id": "user_abc123",
    "name": "John Doe",
    "email": "john@example.com",
    "avatar": "/data/avatars/user_abc123.jpg",
    "bio": "Music producer from NYC",
    "plan": "creator",
    "created_at": "2025-01-15T10:30:00Z",
    "last_login": "2025-12-30T14:22:00Z",
    "usage": {
        "total_songs": 147,
        "this_month": 12
    }
}
```

### Updating Profile

```python
# Dashboard: Settings page
# API endpoint
response = requests.patch(
    "http://localhost:8000/auth/profile",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "name": "John Smith",
        "bio": "Updated bio"
    }
)
```

### Avatar Upload

```python
# Upload avatar image
with open("avatar.jpg", "rb") as f:
    response = requests.post(
        "http://localhost:8000/auth/avatar",
        headers={"Authorization": f"Bearer {token}"},
        files={"avatar": f}
    )
```

---

## Activity Tracking

### Activity Types

| Activity | Description |
|----------|-------------|
| `login` | User logged in |
| `register` | Account created |
| `process` | Song processed |
| `download` | Stem downloaded |
| `upload` | File uploaded |
| `url_process` | URL processed |

### Activity Log Structure

```json
{
    "id": "activity_xyz789",
    "user_id": "user_abc123",
    "type": "process",
    "timestamp": "2025-12-30T14:22:00Z",
    "details": {
        "song": "song.mp3",
        "mode": "grouped",
        "quality": "studio"
    }
}
```

### Logging Activities

```python
from harmonix_splitter.auth import log_activity

# Log a processing activity
log_activity(
    user_id="user_abc123",
    activity_type="process",
    details={
        "song": "song.mp3",
        "mode": "grouped",
        "quality": "studio"
    }
)
```

### Retrieving Activity History

```python
from harmonix_splitter.auth import get_user_activities

# Get user's recent activities
activities = get_user_activities(
    user_id="user_abc123",
    limit=50
)

for activity in activities:
    print(f"{activity['timestamp']}: {activity['type']}")
```

---

## Admin Management

### Admin Dashboard

Access the admin panel at `/admin` (requires admin privileges).

**Admin Features:**
- View all users
- Modify user plans
- View system statistics
- Manage shared library
- View error logs

### Setting Admin Users

```python
# In user data file (data/users.json)
{
    "user_abc123": {
        "name": "Admin User",
        "email": "admin@example.com",
        "is_admin": true,
        "plan": "studio"
    }
}
```

### Admin API Endpoints

```python
# Get all users (admin only)
GET /admin/users

# Update user plan (admin only)
PATCH /admin/users/{user_id}
{
    "plan": "studio"
}

# View system stats (admin only)
GET /admin/stats
```

---

## Security

### Password Storage

Passwords are securely hashed using bcrypt:

```python
import bcrypt

def hash_password(password: str) -> str:
    """Hash password with bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(
        password.encode('utf-8'), 
        salt
    ).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash."""
    return bcrypt.checkpw(
        password.encode('utf-8'),
        hashed.encode('utf-8')
    )
```

### Session Security

```python
# Session best practices
- HTTP-only cookies (prevent XSS)
- Secure flag in production (HTTPS only)
- SameSite attribute (prevent CSRF)
- Regular session rotation
- Absolute expiry time
```

### Rate Limiting

```python
# Rate limiting configuration
RATE_LIMITS = {
    "login": "5 per minute",
    "register": "3 per hour",
    "process": "Based on plan",
    "api": "100 per hour"
}
```

### Security Headers

```python
# Applied security headers
- X-Content-Type-Options: nosniff
- X-Frame-Options: DENY
- X-XSS-Protection: 1; mode=block
- Content-Security-Policy: default-src 'self'
- Strict-Transport-Security (HTTPS)
```

---

## User Data Storage

### Data Files

```
data/
├── users.json          # User accounts
├── activities.json     # Activity log
└── avatars/           # Profile images
    ├── user_abc123.jpg
    └── user_def456.png
```

### User JSON Structure

```json
{
    "user_abc123": {
        "id": "user_abc123",
        "name": "John Doe",
        "email": "john@example.com",
        "password_hash": "$2b$12$...",
        "plan": "creator",
        "is_admin": false,
        "created_at": "2025-01-15T10:30:00Z",
        "last_login": "2025-12-30T14:22:00Z",
        "avatar": "/data/avatars/user_abc123.jpg",
        "bio": "Music producer"
    }
}
```

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Session encryption key | Random |
| `SESSION_LIFETIME` | Session duration | 7 days |
| `MAX_USERS` | Maximum registered users | Unlimited |
| `ADMIN_EMAIL` | Default admin email | None |

---

## Related Documentation

- [Dashboard](./DASHBOARD.md) - Web interface
- [API Reference](./API_REFERENCE.md) - REST API
- [Configuration](./CONFIGURATION.md) - Settings
- [Security](./SECURITY.md) - Security guide

---

*User management documentation last updated: January 2026*
