/**
 * Dashboard Audio Player Module
 * Handles stems audio playback with WaveSurfer
 */

const DashboardPlayer = (function() {
    'use strict';
    
    // State
    let wavesurfers = {};
    let isPlaying = false;
    let currentTime = 0;
    let masterVolume = 1;
    let soloedTrack = null;
    let mutedTracks = new Set();
    
    /**
     * Initialize player module
     */
    function init() {
        setupPlayerControls();
        setupKeyboardShortcuts();
    }
    
    /**
     * Setup player control event listeners
     */
    function setupPlayerControls() {
        // Master play/pause
        const playBtn = document.getElementById('master-play-btn');
        if (playBtn) {
            playBtn.addEventListener('click', togglePlayPause);
        }
        
        // Master volume
        const volumeSlider = document.getElementById('master-volume');
        if (volumeSlider) {
            volumeSlider.addEventListener('input', function(e) {
                setMasterVolume(parseFloat(e.target.value));
            });
        }
        
        // Seek bar
        const seekBar = document.getElementById('master-seek');
        if (seekBar) {
            seekBar.addEventListener('input', function(e) {
                seekTo(parseFloat(e.target.value));
            });
        }
    }
    
    /**
     * Setup keyboard shortcuts
     */
    function setupKeyboardShortcuts() {
        document.addEventListener('keydown', function(e) {
            // Only handle if not in input/textarea
            if (['INPUT', 'TEXTAREA', 'SELECT'].includes(e.target.tagName)) return;
            
            switch(e.code) {
                case 'Space':
                    e.preventDefault();
                    togglePlayPause();
                    break;
                case 'ArrowLeft':
                    e.preventDefault();
                    skipBackward(5);
                    break;
                case 'ArrowRight':
                    e.preventDefault();
                    skipForward(5);
                    break;
                case 'ArrowUp':
                    if (e.shiftKey) {
                        e.preventDefault();
                        adjustMasterVolume(0.1);
                    }
                    break;
                case 'ArrowDown':
                    if (e.shiftKey) {
                        e.preventDefault();
                        adjustMasterVolume(-0.1);
                    }
                    break;
                case 'KeyM':
                    e.preventDefault();
                    toggleMute();
                    break;
            }
        });
    }
    
    /**
     * Initialize a stem track with WaveSurfer
     */
    function initStemTrack(trackId, audioUrl, container) {
        if (wavesurfers[trackId]) {
            wavesurfers[trackId].destroy();
        }
        
        const wavesurfer = WaveSurfer.create({
            container: container,
            waveColor: '#4a9eff',
            progressColor: '#1976d2',
            cursorColor: '#ffffff',
            height: 60,
            barWidth: 2,
            barGap: 1,
            responsive: true,
            normalize: true,
            backend: 'WebAudio'
        });
        
        wavesurfer.load(audioUrl);
        
        wavesurfer.on('ready', function() {
            console.log('Track ready:', trackId);
        });
        
        wavesurfer.on('audioprocess', function(time) {
            updateCurrentTime(time);
        });
        
        wavesurfer.on('finish', function() {
            handleTrackEnd();
        });
        
        wavesurfers[trackId] = wavesurfer;
        return wavesurfer;
    }
    
    /**
     * Toggle play/pause for all tracks
     */
    function togglePlayPause() {
        if (isPlaying) {
            pause();
        } else {
            play();
        }
    }
    
    /**
     * Play all tracks
     */
    function play() {
        Object.values(wavesurfers).forEach(function(ws) {
            ws.play();
        });
        isPlaying = true;
        updatePlayButton();
    }
    
    /**
     * Pause all tracks
     */
    function pause() {
        Object.values(wavesurfers).forEach(function(ws) {
            ws.pause();
        });
        isPlaying = false;
        updatePlayButton();
    }
    
    /**
     * Stop all tracks
     */
    function stop() {
        Object.values(wavesurfers).forEach(function(ws) {
            ws.stop();
        });
        isPlaying = false;
        currentTime = 0;
        updatePlayButton();
        updateTimeDisplay();
    }
    
    /**
     * Seek to position (0-1)
     */
    function seekTo(position) {
        Object.values(wavesurfers).forEach(function(ws) {
            ws.seekTo(position);
        });
    }
    
    /**
     * Skip forward by seconds
     */
    function skipForward(seconds) {
        const firstWs = Object.values(wavesurfers)[0];
        if (!firstWs) return;
        
        const duration = firstWs.getDuration();
        const newTime = Math.min(currentTime + seconds, duration);
        const position = newTime / duration;
        seekTo(position);
    }
    
    /**
     * Skip backward by seconds
     */
    function skipBackward(seconds) {
        const firstWs = Object.values(wavesurfers)[0];
        if (!firstWs) return;
        
        const duration = firstWs.getDuration();
        const newTime = Math.max(currentTime - seconds, 0);
        const position = newTime / duration;
        seekTo(position);
    }
    
    /**
     * Set master volume
     */
    function setMasterVolume(volume) {
        masterVolume = DashboardUtils.clamp(volume, 0, 1);
        updateTrackVolumes();
    }
    
    /**
     * Adjust master volume
     */
    function adjustMasterVolume(delta) {
        setMasterVolume(masterVolume + delta);
        
        const volumeSlider = document.getElementById('master-volume');
        if (volumeSlider) {
            volumeSlider.value = masterVolume;
        }
    }
    
    /**
     * Toggle mute
     */
    function toggleMute() {
        Object.values(wavesurfers).forEach(function(ws) {
            ws.toggleMute();
        });
    }
    
    /**
     * Set track volume
     */
    function setTrackVolume(trackId, volume) {
        if (wavesurfers[trackId]) {
            wavesurfers[trackId].setVolume(volume * masterVolume);
        }
    }
    
    /**
     * Mute a track
     */
    function muteTrack(trackId) {
        mutedTracks.add(trackId);
        if (wavesurfers[trackId]) {
            wavesurfers[trackId].setMute(true);
        }
        updateTrackMuteButton(trackId, true);
    }
    
    /**
     * Unmute a track
     */
    function unmuteTrack(trackId) {
        mutedTracks.delete(trackId);
        if (wavesurfers[trackId]) {
            wavesurfers[trackId].setMute(false);
        }
        updateTrackMuteButton(trackId, false);
    }
    
    /**
     * Toggle track mute
     */
    function toggleTrackMute(trackId) {
        if (mutedTracks.has(trackId)) {
            unmuteTrack(trackId);
        } else {
            muteTrack(trackId);
        }
    }
    
    /**
     * Solo a track (mute all others)
     */
    function soloTrack(trackId) {
        if (soloedTrack === trackId) {
            // Unsolo
            soloedTrack = null;
            Object.keys(wavesurfers).forEach(function(id) {
                if (!mutedTracks.has(id)) {
                    wavesurfers[id].setMute(false);
                }
            });
        } else {
            soloedTrack = trackId;
            Object.keys(wavesurfers).forEach(function(id) {
                wavesurfers[id].setMute(id !== trackId);
            });
        }
        updateSoloButtons();
    }
    
    /**
     * Update all track volumes based on master
     */
    function updateTrackVolumes() {
        Object.keys(wavesurfers).forEach(function(trackId) {
            const trackVolumeSlider = document.querySelector(`[data-track="${trackId}"] .track-volume`);
            const trackVolume = trackVolumeSlider ? parseFloat(trackVolumeSlider.value) : 1;
            setTrackVolume(trackId, trackVolume);
        });
    }
    
    /**
     * Update play button icon
     */
    function updatePlayButton() {
        const playBtn = document.getElementById('master-play-btn');
        if (playBtn) {
            const icon = playBtn.querySelector('i');
            if (icon) {
                icon.className = isPlaying ? 'fas fa-pause' : 'fas fa-play';
            }
        }
    }
    
    /**
     * Update current time display
     */
    function updateCurrentTime(time) {
        currentTime = time;
        updateTimeDisplay();
        updateSeekBar();
    }
    
    /**
     * Update time display elements
     */
    function updateTimeDisplay() {
        const timeDisplay = document.getElementById('current-time');
        if (timeDisplay) {
            timeDisplay.textContent = DashboardUtils.formatTime(currentTime);
        }
    }
    
    /**
     * Update seek bar position
     */
    function updateSeekBar() {
        const seekBar = document.getElementById('master-seek');
        const firstWs = Object.values(wavesurfers)[0];
        
        if (seekBar && firstWs) {
            const duration = firstWs.getDuration();
            if (duration > 0) {
                seekBar.value = currentTime / duration;
            }
        }
    }
    
    /**
     * Update track mute button UI
     */
    function updateTrackMuteButton(trackId, isMuted) {
        const btn = document.querySelector(`[data-track="${trackId}"] .mute-btn`);
        if (btn) {
            btn.classList.toggle('active', isMuted);
            const icon = btn.querySelector('i');
            if (icon) {
                icon.className = isMuted ? 'fas fa-volume-mute' : 'fas fa-volume-up';
            }
        }
    }
    
    /**
     * Update solo buttons UI
     */
    function updateSoloButtons() {
        document.querySelectorAll('.solo-btn').forEach(function(btn) {
            const trackId = btn.closest('[data-track]')?.dataset.track;
            btn.classList.toggle('active', trackId === soloedTrack);
        });
    }
    
    /**
     * Handle track end
     */
    function handleTrackEnd() {
        isPlaying = false;
        updatePlayButton();
    }
    
    /**
     * Destroy all wavesurfers
     */
    function destroy() {
        Object.values(wavesurfers).forEach(function(ws) {
            ws.destroy();
        });
        wavesurfers = {};
        isPlaying = false;
        currentTime = 0;
    }
    
    /**
     * Get current playback state
     */
    function getState() {
        return {
            isPlaying: isPlaying,
            currentTime: currentTime,
            masterVolume: masterVolume,
            soloedTrack: soloedTrack,
            mutedTracks: Array.from(mutedTracks)
        };
    }
    
    // Public API
    return {
        init: init,
        initStemTrack: initStemTrack,
        play: play,
        pause: pause,
        stop: stop,
        togglePlayPause: togglePlayPause,
        seekTo: seekTo,
        skipForward: skipForward,
        skipBackward: skipBackward,
        setMasterVolume: setMasterVolume,
        setTrackVolume: setTrackVolume,
        muteTrack: muteTrack,
        unmuteTrack: unmuteTrack,
        toggleTrackMute: toggleTrackMute,
        soloTrack: soloTrack,
        destroy: destroy,
        getState: getState
    };
})();

// NOTE: Auto-initialization disabled to avoid conflicts with inline player code
// document.addEventListener('DOMContentLoaded', function() {
//     DashboardPlayer.init();
// });
