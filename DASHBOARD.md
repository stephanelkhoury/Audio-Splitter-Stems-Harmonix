# 🎵 Harmonix Dashboard - Quick Start Guide

## Launch the Dashboard

### Simple One-Command Start:
```bash
./start_dashboard.sh
```

### Or manually:
```bash
# Activate virtual environment
source venv/bin/activate

# Start the dashboard
python -m harmonix_splitter.dashboard
```

The dashboard will open at: **http://localhost:5000**

---

## Using the Dashboard

### 1. **Upload Your Audio File**
- Click the upload area or drag & drop your audio file
- Supported formats: MP3, WAV, FLAC, M4A, OGG, AAC
- Max size: 500MB

### 2. **Choose Your Settings**

**Quality Mode:**
- **Fast** - Quick processing (best for testing)
- **Balanced** - Recommended for most uses
- **Studio** - Highest quality (slower)

**Separation Mode:**
- **Grouped** - Standard 4 stems (Vocals, Drums, Bass, Other)
- **Per-Instrument** - Individual instruments (Vocals, Drums, Bass, Guitar, Piano, Strings, Synth, etc.)

### 3. **Optional: Select Specific Instruments**
When using "Per-Instrument" mode, you can select which instruments to extract:
- ✅ Vocals
- ✅ Drums  
- ✅ Bass
- ✅ Guitar
- ✅ Piano
- ✅ Strings
- ✅ Synth

### 4. **Process & Listen**
- Click "Start Processing"
- Watch the progress bar
- Once complete, you'll see all your stems
- **Play audio directly in the browser** 🎧
- Download individual stems as WAV files

---

## Features

✨ **Real-time Progress Tracking** - See processing status live  
🎵 **In-Browser Audio Playback** - Listen to stems immediately  
⬇️ **Individual Downloads** - Download any stem as WAV  
🎨 **Beautiful UI** - Modern, responsive design  
🚀 **Fast Processing** - GPU-accelerated when available  
📊 **Instrument Detection** - Shows detected instruments  

---

## Tips

- Use **Balanced** quality for best speed/quality ratio
- **Per-Instrument** mode takes longer but gives more control
- Select specific instruments to speed up processing
- Audio files stay on your local machine - nothing is uploaded to the cloud

---

## Troubleshooting

**Dashboard won't start?**
```bash
# Install dependencies
pip install flask flask-cors

# Or reinstall everything
pip install -r requirements.txt
```

**Processing is slow?**
- Try "Fast" quality mode
- Use "Grouped" mode instead of "Per-Instrument"
- GPU processing is much faster - check if CUDA is available

**Can't hear audio?**
- Make sure your browser supports HTML5 audio
- Try downloading the file and playing locally

---

## Stopping the Dashboard

Press `Ctrl+C` in the terminal to stop the server.

---

**Enjoy separating your audio! 🎶**
