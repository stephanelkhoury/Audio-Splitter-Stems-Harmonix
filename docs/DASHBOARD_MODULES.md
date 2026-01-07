# Dashboard Modular Architecture

This document describes the modular architecture of the Harmonix Dashboard.

## Directory Structure

```
src/harmonix_splitter/
├── static/
│   ├── css/
│   │   └── dashboard/
│   │       ├── index.css       # Main import file
│   │       ├── variables.css   # CSS custom properties
│   │       ├── base.css        # Base styles, buttons, forms
│   │       ├── sidebar.css     # Sidebar navigation
│   │       ├── upload.css      # File upload area
│   │       ├── player.css      # Audio player & stems
│   │       ├── midi.css        # MIDI converter & player
│   │       └── modal.css       # Modal dialogs
│   │
│   └── js/
│       └── dashboard/
│           ├── main.js         # Main entry point
│           ├── utils.js        # Utility functions
│           ├── toast.js        # Toast notifications
│           ├── theme.js        # Theme management
│           ├── navigation.js   # Section navigation
│           ├── modal.js        # Modal dialogs
│           ├── upload.js       # File upload handling
│           ├── player.js       # Audio player (WaveSurfer)
│           ├── midi-player.js  # MIDI playback (Tone.js)
│           └── tracks.js       # Track list management
│
└── templates/
    └── dashboard/
        ├── _navbar.html        # Top navigation bar
        ├── _sidebar.html       # Sidebar navigation
        ├── _modals.html        # Modal dialogs
        └── _toast.html         # Toast container
```

## JavaScript Modules

### Module Pattern
Each JavaScript module follows the IIFE (Immediately Invoked Function Expression) pattern:

```javascript
const ModuleName = (function() {
    'use strict';
    
    // Private variables
    let privateVar = null;
    
    // Private functions
    function privateFunc() {}
    
    // Public API
    return {
        init: init,
        publicMethod: publicMethod
    };
})();
```

### Available Modules

#### DashboardUtils
Utility functions for common operations:
- `formatTime(seconds)` - Format seconds to MM:SS
- `formatFileSize(bytes)` - Format bytes to human-readable
- `formatRelativeTime(date)` - Format date to "2 hours ago"
- `debounce(fn, wait)` - Debounce function calls
- `throttle(fn, limit)` - Throttle function calls
- `copyToClipboard(text)` - Copy text to clipboard
- `downloadFile(url, filename)` - Download file
- `escapeHtml(text)` - Escape HTML special characters

#### DashboardToast
Toast notification system:
- `show(message, type, duration)` - Show a toast
- `success(message)` - Show success toast
- `error(message)` - Show error toast
- `warning(message)` - Show warning toast
- `info(message)` - Show info toast
- `clearAll()` - Clear all toasts

#### DashboardTheme
Theme management:
- `toggle()` - Toggle between dark/light
- `getCurrentTheme()` - Get current theme
- `setTheme(theme)` - Set specific theme
- `isDark()` - Check if dark theme

#### DashboardNav
Section navigation:
- `switchToSection(sectionId)` - Switch to a section
- `getCurrentSection()` - Get current section

#### DashboardModal
Modal dialog management:
- `open(modalId)` - Open a modal
- `close(modalId)` - Close a modal
- `toggle(modalId)` - Toggle modal
- `confirm(message, options)` - Show confirm dialog
- `alert(message, options)` - Show alert dialog

#### DashboardUpload
File upload handling:
- `handleFileSelect(file)` - Handle file selection
- `clearSelection()` - Clear selected file
- `getSelectedFile()` - Get selected file
- `switchUploadTab(tabName)` - Switch upload tab

#### DashboardPlayer
Audio player with WaveSurfer:
- `initStemTrack(trackId, audioUrl, container)` - Initialize stem
- `play()` / `pause()` / `stop()` - Playback controls
- `togglePlayPause()` - Toggle play/pause
- `setMasterVolume(volume)` - Set master volume
- `muteTrack(trackId)` / `unmuteTrack(trackId)` - Track muting
- `soloTrack(trackId)` - Solo a track

#### DashboardMidiPlayer
MIDI playback with Tone.js and sampled instruments:
- `loadMidiFile(file)` - Load MIDI file
- `loadMidiUrl(url)` - Load MIDI from URL
- `play()` / `pause()` / `stop()` - Playback controls
- `setInstrument(instrumentKey)` - Change instrument
- `setVolume(volume)` - Set volume
- `testSound()` - Test instrument sound

Available instruments:
- `piano` - Grand Piano
- `guitar` - Acoustic Guitar
- `violin` - Violin
- `cello` - Cello
- `flute` - Flute
- `trumpet` - Trumpet
- `bass` - Electric Bass
- `organ` - Church Organ

#### DashboardTracks
Track list management:
- `loadSavedTracks()` - Load tracks from API
- `startSeparation()` - Start audio separation
- `loadTrack(trackId)` - Load a track
- `deleteTrack(trackId)` - Delete a track
- `downloadStem(url, name)` - Download single stem
- `downloadAllStems()` - Download all stems as ZIP

## CSS Architecture

### CSS Custom Properties
All colors, spacing, and theme values are defined in `variables.css`:

```css
:root {
    --primary: #7c3aed;
    --primary-light: #a78bfa;
    --secondary: #06b6d4;
    --success: #10b981;
    --danger: #ef4444;
    --warning: #f59e0b;
    /* ... */
}

[data-theme="light"] {
    /* Light theme overrides */
}
```

### Module Responsibilities
- **base.css**: Reset, typography, buttons, cards, form controls
- **sidebar.css**: Sidebar layout, navigation items, mobile sidebar
- **upload.css**: Upload area, drag & drop, file preview
- **player.css**: Waveforms, stem tracks, controls, timeline
- **midi.css**: MIDI converter, library, instrument selector
- **modal.css**: Modal overlay, content, animations

## HTML Partials

### Using Partials in Templates
```jinja2
{% include 'dashboard/_navbar.html' %}
{% include 'dashboard/_sidebar.html' %}
{% include 'dashboard/_modals.html' %}
{% include 'dashboard/_toast.html' %}
```

### Partial Naming Convention
- Prefixed with underscore (`_`) to indicate partial
- Lowercase with hyphens for multi-word names

## Integration

### Loading Scripts
Add these script tags in order:
```html
<!-- External Dependencies -->
<script src="https://unpkg.com/wavesurfer.js@7"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/tone/14.8.49/Tone.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/@tonejs/midi"></script>

<!-- Dashboard Modules -->
<script src="{{ url_for('static', filename='js/dashboard/utils.js') }}"></script>
<script src="{{ url_for('static', filename='js/dashboard/toast.js') }}"></script>
<script src="{{ url_for('static', filename='js/dashboard/theme.js') }}"></script>
<script src="{{ url_for('static', filename='js/dashboard/navigation.js') }}"></script>
<script src="{{ url_for('static', filename='js/dashboard/modal.js') }}"></script>
<script src="{{ url_for('static', filename='js/dashboard/upload.js') }}"></script>
<script src="{{ url_for('static', filename='js/dashboard/player.js') }}"></script>
<script src="{{ url_for('static', filename='js/dashboard/midi-player.js') }}"></script>
<script src="{{ url_for('static', filename='js/dashboard/tracks.js') }}"></script>
<script src="{{ url_for('static', filename='js/dashboard/main.js') }}"></script>
```

### Loading Styles
```html
<link rel="stylesheet" href="{{ url_for('static', filename='css/dashboard/index.css') }}">
```

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl/Cmd + 1-7` | Switch sections |
| `Space` | Play/Pause audio |
| `←` / `→` | Skip backward/forward 5s |
| `Shift + ↑/↓` | Adjust volume |
| `M` | Toggle mute |
| `Ctrl/Cmd + Shift + T` | Toggle theme |
| `Escape` | Close modal |

## Best Practices

1. **Initialize modules on DOMContentLoaded** - Each module self-initializes
2. **Use public API** - Access modules through their public methods
3. **Backward compatibility** - Global functions like `showToast()` remain available
4. **Error handling** - All async operations include try/catch
5. **Event delegation** - Use event delegation for dynamic content
