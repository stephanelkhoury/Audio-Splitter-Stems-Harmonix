# 🌐 Web Dashboard Guide

**Complete guide to the Harmonix web dashboard interface**

---

## Table of Contents

- [Overview](#overview)
- [Getting Started](#getting-started)
- [Dashboard Features](#dashboard-features)
- [Processing Audio](#processing-audio)
- [Playback and Controls](#playback-and-controls)
- [User Accounts](#user-accounts)
- [Advanced Features](#advanced-features)
- [Keyboard Shortcuts](#keyboard-shortcuts)

---

## Overview

The Harmonix Web Dashboard provides a beautiful, easy-to-use interface for:

- 📤 **Uploading** audio files or YouTube URLs
- 🎛️ **Processing** with customizable settings
- 🎵 **Playing** separated stems in browser
- ⬇️ **Downloading** individual or all stems
- 🎤 **Extracting** and viewing lyrics
- 🎹 **Pitch shifting** in real-time
- 📊 **Analyzing** music (BPM, key)

---

## Getting Started

### Starting the Dashboard

```bash
# Option 1: Shell script
./start_dashboard.sh

# Option 2: Python module
python -m harmonix_splitter.dashboard

# Option 3: Direct Python
python run_dashboard.py
```

### Accessing the Dashboard

Open your browser to: **http://localhost:5000**

### Dashboard URLs

| URL | Description |
|-----|-------------|
| `/` | Landing page |
| `/dashboard` | Main studio |
| `/app` | Alias for dashboard |
| `/studio` | Alias for dashboard |
| `/login` | User login |
| `/register` | New account |
| `/admin` | Admin panel |

---

## Dashboard Features

### Main Interface

```
┌──────────────────────────────────────────────────────────────┐
│  🎵 Harmonix Audio Splitter                    [User] [Theme]│
├────────────┬─────────────────────────────────────────────────┤
│            │                                                 │
│  SIDEBAR   │              MAIN CONTENT AREA                  │
│            │                                                 │
│  • Upload  │  ┌────────────────────────────────────────────┐ │
│  • Tracks  │  │  Upload Area                                │ │
│  • Library │  │  Drop audio files here or click to browse  │ │
│  • MIDI    │  │  ────────────────────────────────────────  │ │
│  • Tools   │  │  [URL Input Tab]                           │ │
│  • Settings│  └────────────────────────────────────────────┘ │
│            │                                                 │
│            │  ┌────────────────────────────────────────────┐ │
│            │  │  Settings                                  │ │
│            │  │  Quality: [Fast] [Balanced] [Studio]       │ │
│            │  │  Mode: [Grouped] [Per-Instrument] [Karaoke]│ │
│            │  └────────────────────────────────────────────┘ │
│            │                                                 │
│            │  [▶️ Start Processing]                          │
│            │                                                 │
└────────────┴─────────────────────────────────────────────────┘
```

### Sidebar Navigation

| Section | Description |
|---------|-------------|
| **Upload** | Upload and process new audio |
| **Tracks** | View processed tracks |
| **Library** | Shared content library |
| **MIDI** | MIDI converter and player |
| **Tools** | Tuner, transposer, metronome |
| **Settings** | User preferences |

---

## Processing Audio

### Uploading Files

**Supported Formats:**
- MP3 (.mp3)
- WAV (.wav)
- FLAC (.flac)
- M4A (.m4a)
- OGG (.ogg)
- AAC (.aac)

**Upload Methods:**
1. **Drag & Drop** - Drag file onto upload area
2. **Click to Browse** - Click upload area to select file
3. **URL Input** - Paste YouTube or direct audio URL

### URL Processing

```
Supported URLs:
• YouTube videos: https://youtube.com/watch?v=...
• YouTube shorts: https://youtube.com/shorts/...
• Direct audio: https://example.com/song.mp3
```

### Processing Settings

#### Quality Mode

| Mode | Speed | Quality | Best For |
|------|-------|---------|----------|
| **Fast** | ~30s | Good | Testing |
| **Balanced** | ~2min | Very Good | Most work |
| **Studio** | ~5min | Excellent | Final output |

#### Separation Mode

| Mode | Output | Description |
|------|--------|-------------|
| **Grouped** | 4 stems | Vocals, Drums, Bass, Other |
| **Per-Instrument** | 6-8 stems | Individual instruments |
| **Karaoke** | 2 stems | Vocals + Instrumental |

### Processing Progress

```
┌────────────────────────────────────────────────────────────┐
│  Processing: song.mp3                                      │
│                                                            │
│  [████████████████████░░░░░░░░░░░] 65%                    │
│                                                            │
│  Stage: Separating stems (studio quality)...              │
│  Elapsed: 1:23                                            │
│  Estimated: 2:10 remaining                                │
│                                                            │
│  Detected: 128 BPM, A Minor (8A)                          │
│                                                            │
│  [Cancel]                                                  │
└────────────────────────────────────────────────────────────┘
```

---

## Playback and Controls

### Stem Player Interface

```
┌────────────────────────────────────────────────────────────┐
│  Now Playing: song.mp3                                     │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐ │
│  │  [▶]  00:45 ═══════════●════════════════ 03:24      │ │
│  │        [|◀◀] [▶/❚❚] [▶▶|]      🔊 ━━━━━●━━━━━       │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                            │
│  STEMS:                                                    │
│  ┌────────────────────────────────────────────────────┐   │
│  │ 🎤 Vocals    [M] [S]  ━━━━━━●━━━━━  [⬇]           │   │
│  │ ▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  │   │
│  └────────────────────────────────────────────────────┘   │
│  ┌────────────────────────────────────────────────────┐   │
│  │ 🥁 Drums     [M] [S]  ━━━━━━━━●━━━  [⬇]           │   │
│  │ ▓▓▓▓▓░░▓▓░░▓▓░░▓▓░░▓▓░░▓▓░░▓▓░░▓▓░░▓▓░░▓▓░░▓▓░░  │   │
│  └────────────────────────────────────────────────────┘   │
│  ┌────────────────────────────────────────────────────┐   │
│  │ 🎸 Bass      [M] [S]  ━━━━━●━━━━━━  [⬇]           │   │
│  │ ▓▓▓▓▓▓▓▓▓▓░░░░░░░░░░░▓▓▓▓▓▓▓▓▓▓░░░░░░░░░░░░░░░░  │   │
│  └────────────────────────────────────────────────────┘   │
│  ┌────────────────────────────────────────────────────┐   │
│  │ 🎹 Other     [M] [S]  ━━━━━━━●━━━━  [⬇]           │   │
│  │ ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  │   │
│  └────────────────────────────────────────────────────┘   │
│                                                            │
│  [Download All as ZIP]                                     │
└────────────────────────────────────────────────────────────┘
```

### Playback Controls

| Control | Function |
|---------|----------|
| **Play/Pause** | Start/stop playback |
| **Seek** | Click waveform to jump |
| **Master Volume** | Overall volume slider |

### Per-Stem Controls

| Control | Icon | Function |
|---------|------|----------|
| **Mute** | [M] | Silence this stem |
| **Solo** | [S] | Play only this stem |
| **Volume** | Slider | Individual stem volume |
| **Download** | ⬇ | Download single stem |

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Space` | Play/Pause |
| `M` | Mute selected |
| `S` | Solo selected |
| `←` | Seek back 5s |
| `→` | Seek forward 5s |

---

## User Accounts

### Registration

1. Go to `/register`
2. Enter name, email, password
3. Click "Create Account"
4. Automatically logged in

### Login

1. Go to `/login`
2. Enter email and password
3. Optionally check "Remember me"
4. Click "Sign In"

### User Plans

| Plan | Songs/Month | Stems | Features |
|------|-------------|-------|----------|
| **Free** | 3 | 4 | Basic |
| **Creator** | 50 | 6 | Priority processing |
| **Studio** | Unlimited | 6 | API access, commercial |

### Profile Settings

- Change display name
- Update email
- Change password
- Upload avatar
- Update bio
- View usage statistics

---

## Advanced Features

### Lyrics Extraction

1. Process a track
2. Click "Extract Lyrics"
3. View synchronized lyrics
4. Export as LRC/SRT/JSON

```
┌────────────────────────────────────────────────────────────┐
│  Lyrics: song.mp3                       [Export ▼]        │
│                                                            │
│  [00:05] Welcome to the jungle                            │
│  [00:08] We've got fun and games                          │
│  [00:12] We got everything you want                       │
│  [00:15] Honey, we know the names                         │
│  ...                                                       │
│                                                            │
│  Language: English (98% confidence)                        │
└────────────────────────────────────────────────────────────┘
```

### Pitch Shifting

1. Load a processed track
2. Select a stem
3. Use pitch slider (-12 to +12 semitones)
4. Preview in real-time
5. Download shifted version

```
┌────────────────────────────────────────────────────────────┐
│  Pitch Shift: Vocals                                       │
│                                                            │
│  ◀━━━━━━━━━━━━━●━━━━━━━━━━━━━━━━━▶                         │
│           -6      0      +6                                │
│                                                            │
│  Current: +2 semitones                                     │
│  [☑] Preserve Formants (natural sound)                     │
│                                                            │
│  [Preview] [Apply & Download]                              │
└────────────────────────────────────────────────────────────┘
```

### Music Analysis Display

```
┌────────────────────────────────────────────────────────────┐
│  Music Analysis                                            │
│                                                            │
│  🎵 Tempo: 128 BPM (95% confidence)                       │
│  🎹 Key: A Minor (8A Camelot)                             │
│  ⏱️ Time Signature: 4/4                                    │
│  📏 Duration: 3:24                                         │
│                                                            │
│  Detected Instruments:                                     │
│  • Vocals    ████████████░░░░ 85%                         │
│  • Drums     ███████████████░ 92%                         │
│  • Bass      █████████░░░░░░░ 68%                         │
│  • Guitar    ████████░░░░░░░░ 61%                         │
└────────────────────────────────────────────────────────────┘
```

### Shared Library

- Pre-processed content available instantly
- YouTube videos cached for all users
- Reduces processing time to zero
- Shows original metadata

```
┌────────────────────────────────────────────────────────────┐
│  🔗 From Shared Library                                    │
│                                                            │
│  This content was previously processed and is              │
│  instantly available!                                      │
│                                                            │
│  Original: Rick Astley - Never Gonna Give You Up          │
│  Processed: December 15, 2025                              │
│  Quality: Studio                                           │
│  Mode: Per-Instrument                                      │
└────────────────────────────────────────────────────────────┘
```

---

## Keyboard Shortcuts

### Global

| Shortcut | Action |
|----------|--------|
| `Space` | Play/Pause |
| `Escape` | Close modal |
| `?` | Show shortcuts |

### Navigation

| Shortcut | Action |
|----------|--------|
| `1` | Go to Upload |
| `2` | Go to Tracks |
| `3` | Go to Library |
| `4` | Go to Tools |

### Playback

| Shortcut | Action |
|----------|--------|
| `Space` | Play/Pause |
| `←` | Seek -5 seconds |
| `→` | Seek +5 seconds |
| `↑` | Volume up |
| `↓` | Volume down |
| `M` | Mute/unmute |

### Stems

| Shortcut | Action |
|----------|--------|
| `1-6` | Toggle stem mute |
| `Shift+1-6` | Solo stem |
| `A` | Unmute all |

---

## Troubleshooting

### Audio Not Playing

1. Check browser supports HTML5 audio
2. Ensure audio files exist in output directory
3. Try refreshing the page
4. Check browser console for errors

### Processing Stuck

1. Check server logs for errors
2. Verify GPU/CPU availability
3. Try restarting the dashboard
4. Use smaller/shorter test file

### Upload Fails

1. Check file size (max 500MB)
2. Verify file format is supported
3. Ensure upload directory is writable
4. Check server disk space

---

## Related Documentation

- [Quickstart](./QUICKSTART.md) - Getting started
- [CLI Guide](./CLI_GUIDE.md) - Command-line alternative
- [API Reference](./API_REFERENCE.md) - REST API
- [Troubleshooting](./TROUBLESHOOTING.md) - Common issues

---

*Dashboard documentation last updated: January 2026*
