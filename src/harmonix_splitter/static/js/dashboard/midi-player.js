/**
 * Dashboard MIDI Player Module
 * Handles MIDI playback with Tone.js and realistic sampled instruments
 */

const DashboardMidiPlayer = (function() {
    'use strict';
    
    // State
    let currentSynth = null;
    let midiData = null;
    let isPlaying = false;
    let isPaused = false;
    let currentTime = 0;
    let duration = 0;
    let animationFrame = null;
    let noteEvents = [];
    let playbackStartTime = 0;
    let pausedTime = 0;
    let currentInstrument = 'piano';
    let volume = 0.8;
    
    // Realistic instrument presets using Tone.js Samplers with real samples
    const instrumentPresets = {
        'piano': {
            name: 'Grand Piano',
            icon: 'fa-music',
            baseUrl: 'https://nbrosowsky.github.io/tonejs-instruments/samples/piano/',
            samples: {
                'A0': 'A0.mp3', 'C1': 'C1.mp3', 'D#1': 'Ds1.mp3', 'F#1': 'Fs1.mp3',
                'A1': 'A1.mp3', 'C2': 'C2.mp3', 'D#2': 'Ds2.mp3', 'F#2': 'Fs2.mp3',
                'A2': 'A2.mp3', 'C3': 'C3.mp3', 'D#3': 'Ds3.mp3', 'F#3': 'Fs3.mp3',
                'A3': 'A3.mp3', 'C4': 'C4.mp3', 'D#4': 'Ds4.mp3', 'F#4': 'Fs4.mp3',
                'A4': 'A4.mp3', 'C5': 'C5.mp3', 'D#5': 'Ds5.mp3', 'F#5': 'Fs5.mp3',
                'A5': 'A5.mp3', 'C6': 'C6.mp3', 'D#6': 'Ds6.mp3', 'F#6': 'Fs6.mp3',
                'A6': 'A6.mp3', 'C7': 'C7.mp3', 'D#7': 'Ds7.mp3', 'F#7': 'Fs7.mp3',
                'A7': 'A7.mp3', 'C8': 'C8.mp3'
            }
        },
        'guitar': {
            name: 'Acoustic Guitar',
            icon: 'fa-guitar',
            baseUrl: 'https://nbrosowsky.github.io/tonejs-instruments/samples/guitar-acoustic/',
            samples: {
                'E2': 'E2.mp3', 'F#2': 'Fs2.mp3', 'G#2': 'Gs2.mp3', 'A2': 'A2.mp3',
                'B2': 'B2.mp3', 'C#3': 'Cs3.mp3', 'D#3': 'Ds3.mp3', 'E3': 'E3.mp3',
                'F#3': 'Fs3.mp3', 'G#3': 'Gs3.mp3', 'A3': 'A3.mp3', 'B3': 'B3.mp3',
                'C#4': 'Cs4.mp3', 'D#4': 'Ds4.mp3', 'E4': 'E4.mp3', 'F#4': 'Fs4.mp3'
            }
        },
        'violin': {
            name: 'Violin',
            icon: 'fa-violin',
            baseUrl: 'https://nbrosowsky.github.io/tonejs-instruments/samples/violin/',
            samples: {
                'A3': 'A3.mp3', 'A4': 'A4.mp3', 'A5': 'A5.mp3', 'A6': 'A6.mp3',
                'C4': 'C4.mp3', 'C5': 'C5.mp3', 'C6': 'C6.mp3', 'C7': 'C7.mp3',
                'E4': 'E4.mp3', 'E5': 'E5.mp3', 'E6': 'E6.mp3',
                'G4': 'G4.mp3', 'G5': 'G5.mp3', 'G6': 'G6.mp3'
            }
        },
        'cello': {
            name: 'Cello',
            icon: 'fa-volume-up',
            baseUrl: 'https://nbrosowsky.github.io/tonejs-instruments/samples/cello/',
            samples: {
                'C2': 'C2.mp3', 'D#2': 'Ds2.mp3', 'F#2': 'Fs2.mp3', 'A2': 'A2.mp3',
                'C3': 'C3.mp3', 'D#3': 'Ds3.mp3', 'F#3': 'Fs3.mp3', 'A3': 'A3.mp3',
                'C4': 'C4.mp3', 'D#4': 'Ds4.mp3', 'F#4': 'Fs4.mp3', 'A4': 'A4.mp3',
                'C5': 'C5.mp3', 'D#5': 'Ds5.mp3'
            }
        },
        'flute': {
            name: 'Flute',
            icon: 'fa-wind',
            baseUrl: 'https://nbrosowsky.github.io/tonejs-instruments/samples/flute/',
            samples: {
                'A4': 'A4.mp3', 'C4': 'C4.mp3', 'C5': 'C5.mp3', 'C6': 'C6.mp3',
                'D#5': 'Ds5.mp3', 'D#6': 'Ds6.mp3', 'E4': 'E4.mp3', 'E5': 'E5.mp3',
                'F#4': 'Fs4.mp3', 'F#5': 'Fs5.mp3', 'A5': 'A5.mp3', 'A6': 'A6.mp3'
            }
        },
        'trumpet': {
            name: 'Trumpet',
            icon: 'fa-bullhorn',
            baseUrl: 'https://nbrosowsky.github.io/tonejs-instruments/samples/trumpet/',
            samples: {
                'A3': 'A3.mp3', 'A#4': 'As4.mp3', 'A5': 'A5.mp3',
                'C4': 'C4.mp3', 'C5': 'C5.mp3', 'C6': 'C6.mp3',
                'D4': 'D4.mp3', 'D5': 'D5.mp3', 'D#3': 'Ds3.mp3',
                'F3': 'F3.mp3', 'F4': 'F4.mp3', 'F5': 'F5.mp3'
            }
        },
        'bass': {
            name: 'Electric Bass',
            icon: 'fa-drum',
            baseUrl: 'https://nbrosowsky.github.io/tonejs-instruments/samples/bass-electric/',
            samples: {
                'A#1': 'As1.mp3', 'A#2': 'As2.mp3', 'A#3': 'As3.mp3',
                'C#2': 'Cs2.mp3', 'C#3': 'Cs3.mp3', 'C#4': 'Cs4.mp3',
                'E2': 'E2.mp3', 'E3': 'E3.mp3', 'E4': 'E4.mp3',
                'G2': 'G2.mp3', 'G3': 'G3.mp3', 'G4': 'G4.mp3'
            }
        },
        'organ': {
            name: 'Church Organ',
            icon: 'fa-church',
            baseUrl: 'https://nbrosowsky.github.io/tonejs-instruments/samples/organ/',
            samples: {
                'A1': 'A1.mp3', 'A2': 'A2.mp3', 'A3': 'A3.mp3', 'A4': 'A4.mp3', 'A5': 'A5.mp3',
                'C2': 'C2.mp3', 'C3': 'C3.mp3', 'C4': 'C4.mp3', 'C5': 'C5.mp3', 'C6': 'C6.mp3',
                'D#2': 'Ds2.mp3', 'D#3': 'Ds3.mp3', 'D#4': 'Ds4.mp3', 'D#5': 'Ds5.mp3',
                'F#2': 'Fs2.mp3', 'F#3': 'Fs3.mp3', 'F#4': 'Fs4.mp3', 'F#5': 'Fs5.mp3'
            }
        }
    };
    
    /**
     * Initialize MIDI player
     */
    function init() {
        setupInstrumentButtons();
        setupPlayerControls();
        setupTestButton();
    }
    
    /**
     * Setup instrument selection buttons
     */
    function setupInstrumentButtons() {
        document.querySelectorAll('.midi-instrument-btn').forEach(function(btn) {
            btn.addEventListener('click', function() {
                const instrument = this.dataset.instrument;
                setInstrument(instrument);
            });
        });
    }
    
    /**
     * Setup player control buttons
     */
    function setupPlayerControls() {
        const playBtn = document.getElementById('midi-play-btn');
        const pauseBtn = document.getElementById('midi-pause-btn');
        const stopBtn = document.getElementById('midi-stop-btn');
        const volumeSlider = document.getElementById('midi-volume');
        
        if (playBtn) playBtn.addEventListener('click', play);
        if (pauseBtn) pauseBtn.addEventListener('click', pause);
        if (stopBtn) stopBtn.addEventListener('click', stop);
        
        if (volumeSlider) {
            volumeSlider.addEventListener('input', function(e) {
                setVolume(parseFloat(e.target.value));
            });
        }
    }
    
    /**
     * Setup test sound button
     */
    function setupTestButton() {
        const testBtn = document.getElementById('test-midi-sound');
        if (testBtn) {
            testBtn.addEventListener('click', testSound);
        }
    }
    
    /**
     * Create sampler for instrument
     */
    async function createSampler(instrumentKey) {
        const preset = instrumentPresets[instrumentKey];
        if (!preset) {
            console.error('Unknown instrument:', instrumentKey);
            return createFallbackSynth();
        }
        
        return new Promise(function(resolve, reject) {
            try {
                const sampler = new Tone.Sampler({
                    urls: preset.samples,
                    baseUrl: preset.baseUrl,
                    release: 1,
                    onload: function() {
                        console.log('Sampler loaded for:', instrumentKey);
                        resolve(sampler.toDestination());
                    },
                    onerror: function(error) {
                        console.error('Error loading sampler:', error);
                        resolve(createFallbackSynth());
                    }
                });
                
                // Timeout fallback
                setTimeout(function() {
                    resolve(createFallbackSynth());
                }, 10000);
            } catch (error) {
                console.error('Error creating sampler:', error);
                resolve(createFallbackSynth());
            }
        });
    }
    
    /**
     * Create fallback synthesizer
     */
    function createFallbackSynth() {
        console.log('Using fallback synth');
        return new Tone.PolySynth(Tone.Synth, {
            oscillator: { type: 'triangle' },
            envelope: {
                attack: 0.02,
                decay: 0.3,
                sustain: 0.4,
                release: 1.2
            }
        }).toDestination();
    }
    
    /**
     * Set current instrument
     */
    async function setInstrument(instrumentKey) {
        showToast('Loading ' + instrumentPresets[instrumentKey]?.name + '...', 'info');
        
        // Clean up old synth
        if (currentSynth) {
            currentSynth.dispose();
        }
        
        currentInstrument = instrumentKey;
        currentSynth = await createSampler(instrumentKey);
        
        // Update UI
        document.querySelectorAll('.midi-instrument-btn').forEach(function(btn) {
            btn.classList.remove('active');
            if (btn.dataset.instrument === instrumentKey) {
                btn.classList.add('active');
            }
        });
        
        showToast(instrumentPresets[instrumentKey]?.name + ' loaded!', 'success');
    }
    
    /**
     * Test current instrument sound
     */
    async function testSound() {
        try {
            await Tone.start();
            
            if (!currentSynth) {
                await setInstrument(currentInstrument);
            }
            
            // Play a simple chord
            const now = Tone.now();
            currentSynth.triggerAttackRelease('C4', '8n', now);
            currentSynth.triggerAttackRelease('E4', '8n', now + 0.2);
            currentSynth.triggerAttackRelease('G4', '8n', now + 0.4);
            currentSynth.triggerAttackRelease('C5', '4n', now + 0.6);
            
            showToast('Sound test playing...', 'success');
        } catch (error) {
            console.error('Test sound error:', error);
            showToast('Error playing test sound', 'error');
        }
    }
    
    /**
     * Load MIDI file
     */
    async function loadMidiFile(file) {
        try {
            showToast('Loading MIDI file...', 'info');
            
            const arrayBuffer = await file.arrayBuffer();
            const midi = new Midi(arrayBuffer);
            
            midiData = midi;
            noteEvents = [];
            duration = midi.duration;
            
            // Extract all note events
            midi.tracks.forEach(function(track) {
                track.notes.forEach(function(note) {
                    noteEvents.push({
                        time: note.time,
                        note: note.name,
                        duration: note.duration,
                        velocity: note.velocity
                    });
                });
            });
            
            // Sort by time
            noteEvents.sort(function(a, b) {
                return a.time - b.time;
            });
            
            updateMidiInfo(midi);
            showToast('MIDI file loaded: ' + file.name, 'success');
            
            return true;
        } catch (error) {
            console.error('Error loading MIDI:', error);
            showToast('Error loading MIDI file', 'error');
            return false;
        }
    }
    
    /**
     * Load MIDI from URL
     */
    async function loadMidiUrl(url) {
        try {
            showToast('Fetching MIDI from URL...', 'info');
            
            const response = await fetch(url);
            const arrayBuffer = await response.arrayBuffer();
            const midi = new Midi(arrayBuffer);
            
            midiData = midi;
            noteEvents = [];
            duration = midi.duration;
            
            midi.tracks.forEach(function(track) {
                track.notes.forEach(function(note) {
                    noteEvents.push({
                        time: note.time,
                        note: note.name,
                        duration: note.duration,
                        velocity: note.velocity
                    });
                });
            });
            
            noteEvents.sort(function(a, b) {
                return a.time - b.time;
            });
            
            updateMidiInfo(midi);
            showToast('MIDI loaded successfully', 'success');
            
            return true;
        } catch (error) {
            console.error('Error loading MIDI URL:', error);
            showToast('Error loading MIDI from URL', 'error');
            return false;
        }
    }
    
    /**
     * Update MIDI info display
     */
    function updateMidiInfo(midi) {
        const infoEl = document.getElementById('midi-info');
        if (!infoEl) return;
        
        const totalNotes = midi.tracks.reduce(function(sum, track) {
            return sum + track.notes.length;
        }, 0);
        
        infoEl.innerHTML = `
            <div class="midi-info-item">
                <span class="midi-info-label">Duration:</span>
                <span class="midi-info-value">${DashboardUtils.formatTime(midi.duration)}</span>
            </div>
            <div class="midi-info-item">
                <span class="midi-info-label">Tracks:</span>
                <span class="midi-info-value">${midi.tracks.length}</span>
            </div>
            <div class="midi-info-item">
                <span class="midi-info-label">Notes:</span>
                <span class="midi-info-value">${totalNotes}</span>
            </div>
            <div class="midi-info-item">
                <span class="midi-info-label">BPM:</span>
                <span class="midi-info-value">${Math.round(midi.header.tempos[0]?.bpm || 120)}</span>
            </div>
        `;
    }
    
    /**
     * Play MIDI
     */
    async function play() {
        if (!noteEvents.length) {
            showToast('No MIDI file loaded', 'warning');
            return;
        }
        
        try {
            await Tone.start();
            
            if (!currentSynth) {
                await setInstrument(currentInstrument);
            }
            
            if (isPaused) {
                // Resume from paused position
                playbackStartTime = Tone.now() - pausedTime;
                isPaused = false;
            } else {
                // Start from beginning
                currentTime = 0;
                playbackStartTime = Tone.now();
            }
            
            isPlaying = true;
            scheduleNotes();
            startTimeUpdate();
            updatePlayPauseButton();
            
            showToast('Playing MIDI...', 'success');
        } catch (error) {
            console.error('Error playing MIDI:', error);
            showToast('Error playing MIDI', 'error');
        }
    }
    
    /**
     * Schedule note playback
     */
    function scheduleNotes() {
        const now = Tone.now();
        
        noteEvents.forEach(function(event) {
            if (event.time >= currentTime) {
                const playTime = now + (event.time - currentTime);
                currentSynth.triggerAttackRelease(
                    event.note,
                    event.duration,
                    playTime,
                    event.velocity
                );
            }
        });
    }
    
    /**
     * Pause MIDI playback
     */
    function pause() {
        if (!isPlaying) return;
        
        isPlaying = false;
        isPaused = true;
        pausedTime = Tone.now() - playbackStartTime;
        
        Tone.Transport.pause();
        if (currentSynth && currentSynth.releaseAll) {
            currentSynth.releaseAll();
        }
        
        stopTimeUpdate();
        updatePlayPauseButton();
        showToast('Paused', 'info');
    }
    
    /**
     * Stop MIDI playback
     */
    function stop() {
        isPlaying = false;
        isPaused = false;
        currentTime = 0;
        pausedTime = 0;
        
        Tone.Transport.stop();
        Tone.Transport.cancel();
        
        if (currentSynth && currentSynth.releaseAll) {
            currentSynth.releaseAll();
        }
        
        stopTimeUpdate();
        updateTimeDisplay();
        updatePlayPauseButton();
    }
    
    /**
     * Set volume
     */
    function setVolume(vol) {
        volume = DashboardUtils.clamp(vol, 0, 1);
        Tone.Destination.volume.value = Tone.gainToDb(volume);
    }
    
    /**
     * Seek to position
     */
    function seekTo(position) {
        const newTime = position * duration;
        currentTime = newTime;
        
        if (isPlaying) {
            stop();
            currentTime = newTime;
            play();
        }
    }
    
    /**
     * Start time update animation
     */
    function startTimeUpdate() {
        function update() {
            if (!isPlaying) return;
            
            currentTime = Tone.now() - playbackStartTime;
            
            if (currentTime >= duration) {
                stop();
                return;
            }
            
            updateTimeDisplay();
            updateProgressBar();
            
            animationFrame = requestAnimationFrame(update);
        }
        
        update();
    }
    
    /**
     * Stop time update
     */
    function stopTimeUpdate() {
        if (animationFrame) {
            cancelAnimationFrame(animationFrame);
            animationFrame = null;
        }
    }
    
    /**
     * Update time display
     */
    function updateTimeDisplay() {
        const timeEl = document.getElementById('midi-current-time');
        const durationEl = document.getElementById('midi-duration');
        
        if (timeEl) timeEl.textContent = DashboardUtils.formatTime(currentTime);
        if (durationEl) durationEl.textContent = DashboardUtils.formatTime(duration);
    }
    
    /**
     * Update progress bar
     */
    function updateProgressBar() {
        const progressBar = document.getElementById('midi-progress');
        if (progressBar && duration > 0) {
            progressBar.style.width = (currentTime / duration * 100) + '%';
        }
    }
    
    /**
     * Update play/pause button
     */
    function updatePlayPauseButton() {
        const playBtn = document.getElementById('midi-play-btn');
        if (playBtn) {
            const icon = playBtn.querySelector('i');
            if (icon) {
                icon.className = isPlaying ? 'fas fa-pause' : 'fas fa-play';
            }
        }
    }
    
    /**
     * Get current state
     */
    function getState() {
        return {
            isPlaying: isPlaying,
            isPaused: isPaused,
            currentTime: currentTime,
            duration: duration,
            currentInstrument: currentInstrument,
            volume: volume,
            hasMidi: noteEvents.length > 0
        };
    }
    
    /**
     * Dispose all resources
     */
    function dispose() {
        stop();
        if (currentSynth) {
            currentSynth.dispose();
            currentSynth = null;
        }
        midiData = null;
        noteEvents = [];
    }
    
    // Public API
    return {
        init: init,
        loadMidiFile: loadMidiFile,
        loadMidiUrl: loadMidiUrl,
        play: play,
        pause: pause,
        stop: stop,
        setInstrument: setInstrument,
        setVolume: setVolume,
        seekTo: seekTo,
        testSound: testSound,
        getState: getState,
        dispose: dispose,
        instrumentPresets: instrumentPresets
    };
})();

// NOTE: Auto-initialization disabled to avoid conflicts with inline MIDI code
// The inline code in dashboard.html already handles MIDI playback
// document.addEventListener('DOMContentLoaded', function() {
//     DashboardMidiPlayer.init();
// });
