/**
 * Harmonix Instrument Tuner
 * Real-time pitch detection using Web Audio API
 */

(function() {
    'use strict';

    // Instrument tuning configurations
    const INSTRUMENTS = {
        guitar: {
            name: 'Guitar (Standard)',
            notes: ['E2', 'A2', 'D3', 'G3', 'B3', 'E4'],
            frequencies: [82.41, 110.00, 146.83, 196.00, 246.94, 329.63]
        },
        bass: {
            name: 'Bass (4-String)',
            notes: ['E1', 'A1', 'D2', 'G2'],
            frequencies: [41.20, 55.00, 73.42, 98.00]
        },
        violin: {
            name: 'Violin',
            notes: ['G3', 'D4', 'A4', 'E5'],
            frequencies: [196.00, 293.66, 440.00, 659.26]
        },
        viola: {
            name: 'Viola',
            notes: ['C3', 'G3', 'D4', 'A4'],
            frequencies: [130.81, 196.00, 293.66, 440.00]
        },
        cello: {
            name: 'Cello',
            notes: ['C2', 'G2', 'D3', 'A3'],
            frequencies: [65.41, 98.00, 146.83, 220.00]
        },
        ukulele: {
            name: 'Ukulele (Standard)',
            notes: ['G4', 'C4', 'E4', 'A4'],
            frequencies: [392.00, 261.63, 329.63, 440.00]
        },
        saxophone: {
            name: 'Saxophone (Concert Pitch)',
            notes: ['Bb3', 'C4', 'D4', 'Eb4', 'F4', 'G4', 'A4', 'Bb4'],
            frequencies: [233.08, 261.63, 293.66, 311.13, 349.23, 392.00, 440.00, 466.16]
        },
        trumpet: {
            name: 'Trumpet (Concert Pitch)',
            notes: ['C4', 'D4', 'E4', 'F4', 'G4', 'A4', 'Bb4', 'C5'],
            frequencies: [261.63, 293.66, 329.63, 349.23, 392.00, 440.00, 466.16, 523.25]
        },
        chromatic: {
            name: 'Chromatic (All Notes)',
            notes: [],
            frequencies: []
        }
    };

    // Note names for chromatic scale
    const NOTE_NAMES_SHARP = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'];
    const NOTE_NAMES_FLAT = ['C', 'Db', 'D', 'Eb', 'E', 'F', 'Gb', 'G', 'Ab', 'A', 'Bb', 'B'];

    // State
    let audioContext = null;
    let analyser = null;
    let mediaStream = null;
    let isRunning = false;
    let currentInstrument = 'guitar';
    let referenceA4 = 440;
    let animationId = null;

    // DOM Elements
    const startBtn = document.getElementById('startTunerBtn');
    const stopBtn = document.getElementById('stopTunerBtn');
    const micStatus = document.getElementById('micStatus');
    const gaugeNeedle = document.getElementById('gaugeNeedle');
    const centsValue = document.getElementById('centsValue');
    const detectedNote = document.getElementById('detectedNote');
    const detectedFrequency = document.getElementById('detectedFrequency');
    const tuningStatus = document.getElementById('tuningStatus');
    const notesGrid = document.getElementById('notesGrid');
    const refValue = document.getElementById('refValue');
    const refMinus = document.getElementById('refMinus');
    const refPlus = document.getElementById('refPlus');
    const instrumentBtns = document.querySelectorAll('.instrument-btn');

    // Initialize
    function init() {
        updateInstrumentNotes();
        setupEventListeners();
    }

    function setupEventListeners() {
        // Start/Stop buttons
        startBtn.addEventListener('click', startTuner);
        stopBtn.addEventListener('click', stopTuner);

        // Instrument selection
        instrumentBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                instrumentBtns.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                currentInstrument = btn.dataset.instrument;
                updateInstrumentNotes();
            });
        });

        // Reference pitch controls
        refMinus.addEventListener('click', () => {
            referenceA4 = Math.max(400, referenceA4 - 1);
            refValue.textContent = referenceA4;
        });

        refPlus.addEventListener('click', () => {
            referenceA4 = Math.min(480, referenceA4 + 1);
            refValue.textContent = referenceA4;
        });
    }

    function updateInstrumentNotes() {
        const instrument = INSTRUMENTS[currentInstrument];
        notesGrid.innerHTML = '';

        if (currentInstrument === 'chromatic') {
            notesGrid.innerHTML = '<p style="grid-column: 1/-1; text-align: center; color: var(--text-secondary);">Chromatic mode - detects any note</p>';
            return;
        }

        instrument.notes.forEach((note, index) => {
            const noteEl = document.createElement('button');
            noteEl.className = 'target-note-btn';
            noteEl.innerHTML = `
                <span class="note-name">${note}</span>
                <span class="note-freq">${instrument.frequencies[index].toFixed(1)} Hz</span>
            `;
            notesGrid.appendChild(noteEl);
        });
    }

    async function startTuner() {
        try {
            // Request microphone access
            mediaStream = await navigator.mediaDevices.getUserMedia({ 
                audio: { 
                    echoCancellation: false,
                    noiseSuppression: false,
                    autoGainControl: false
                } 
            });

            // Create audio context
            audioContext = new (window.AudioContext || window.webkitAudioContext)();
            analyser = audioContext.createAnalyser();
            analyser.fftSize = 4096;
            analyser.smoothingTimeConstant = 0.8;

            // Connect microphone to analyser
            const source = audioContext.createMediaStreamSource(mediaStream);
            source.connect(analyser);

            isRunning = true;
            updateUI();
            detectPitch();

        } catch (error) {
            console.error('Error accessing microphone:', error);
            micStatus.innerHTML = '<i class="fas fa-exclamation-triangle"></i> <span>Microphone access denied</span>';
        }
    }

    function stopTuner() {
        isRunning = false;
        
        if (animationId) {
            cancelAnimationFrame(animationId);
        }

        if (mediaStream) {
            mediaStream.getTracks().forEach(track => track.stop());
        }

        if (audioContext) {
            audioContext.close();
        }

        updateUI();
        resetDisplay();
    }

    function updateUI() {
        if (isRunning) {
            startBtn.style.display = 'none';
            stopBtn.style.display = 'inline-flex';
            micStatus.innerHTML = '<i class="fas fa-microphone" style="color: var(--accent);"></i> <span>Listening...</span>';
            micStatus.classList.add('active');
        } else {
            startBtn.style.display = 'inline-flex';
            stopBtn.style.display = 'none';
            micStatus.innerHTML = '<i class="fas fa-microphone-slash"></i> <span>Click "Start Tuning" to begin</span>';
            micStatus.classList.remove('active');
        }
    }

    function resetDisplay() {
        detectedNote.textContent = '--';
        detectedFrequency.textContent = '-- Hz';
        centsValue.textContent = '0';
        tuningStatus.querySelector('.status-text').textContent = 'Waiting for signal...';
        tuningStatus.className = 'tuning-status';
        gaugeNeedle.setAttribute('transform', 'rotate(0, 150, 150)');
    }

    function detectPitch() {
        if (!isRunning) return;

        const bufferLength = analyser.fftSize;
        const buffer = new Float32Array(bufferLength);
        analyser.getFloatTimeDomainData(buffer);

        // Check if there's signal
        const rms = Math.sqrt(buffer.reduce((sum, val) => sum + val * val, 0) / bufferLength);
        
        if (rms < 0.01) {
            // No significant signal
            detectedNote.textContent = '--';
            detectedFrequency.textContent = '-- Hz';
            tuningStatus.querySelector('.status-text').textContent = 'Waiting for signal...';
            tuningStatus.className = 'tuning-status';
        } else {
            // Detect pitch using autocorrelation
            const frequency = autoCorrelate(buffer, audioContext.sampleRate);
            
            if (frequency !== -1) {
                updatePitchDisplay(frequency);
            }
        }

        animationId = requestAnimationFrame(detectPitch);
    }

    function autoCorrelate(buffer, sampleRate) {
        const SIZE = buffer.length;
        const MAX_SAMPLES = Math.floor(SIZE / 2);
        let bestOffset = -1;
        let bestCorrelation = 0;
        let foundGoodCorrelation = false;
        const correlations = new Array(MAX_SAMPLES);

        // Find the starting point (first zero crossing)
        let start = 0;
        for (let i = 0; i < SIZE / 2; i++) {
            if (Math.abs(buffer[i]) < 0.2) {
                start = i;
                break;
            }
        }

        for (let offset = start; offset < MAX_SAMPLES; offset++) {
            let correlation = 0;

            for (let i = 0; i < MAX_SAMPLES; i++) {
                correlation += Math.abs(buffer[i] - buffer[i + offset]);
            }

            correlation = 1 - (correlation / MAX_SAMPLES);
            correlations[offset] = correlation;

            if (correlation > 0.9 && correlation > bestCorrelation) {
                bestCorrelation = correlation;
                bestOffset = offset;
                foundGoodCorrelation = true;
            } else if (foundGoodCorrelation) {
                // We've found a good correlation and now it's getting worse
                // Interpolate to get better precision
                const shift = (correlations[bestOffset + 1] - correlations[bestOffset - 1]) / correlations[bestOffset];
                return sampleRate / (bestOffset + (8 * shift));
            }
        }

        if (bestCorrelation > 0.01) {
            return sampleRate / bestOffset;
        }

        return -1;
    }

    function updatePitchDisplay(frequency) {
        // Calculate note information
        const noteInfo = frequencyToNote(frequency);
        
        // Skip display if invalid
        if (!noteInfo.valid) {
            return;
        }
        
        detectedNote.textContent = noteInfo.note;
        detectedFrequency.textContent = frequency.toFixed(1) + ' Hz';
        centsValue.textContent = Math.round(noteInfo.cents);

        // Update gauge needle (cents range: -50 to +50 maps to -90 to +90 degrees)
        const rotation = isFinite(noteInfo.cents) ? (noteInfo.cents / 50) * 90 : 0;
        gaugeNeedle.setAttribute('transform', `rotate(${rotation}, 150, 150)`);

        // Update tuning status
        const statusEl = tuningStatus.querySelector('.status-text');
        const absCents = Math.abs(noteInfo.cents);
        
        if (absCents < 5) {
            statusEl.textContent = 'In Tune! ✓';
            tuningStatus.className = 'tuning-status in-tune';
        } else if (noteInfo.cents > 0) {
            statusEl.textContent = 'Too Sharp ↑';
            tuningStatus.className = 'tuning-status sharp';
        } else {
            statusEl.textContent = 'Too Flat ↓';
            tuningStatus.className = 'tuning-status flat';
        }

        // Update target notes highlighting
        if (currentInstrument !== 'chromatic') {
            const noteBtns = notesGrid.querySelectorAll('.target-note-btn');
            noteBtns.forEach(btn => {
                const noteName = btn.querySelector('.note-name').textContent;
                const noteStr = String(noteInfo.note || '');
                if (noteStr === noteName || (noteStr && noteStr.startsWith(noteName.replace(/[0-9]/g, '')))) {
                    btn.classList.add('active');
                } else {
                    btn.classList.remove('active');
                }
            });
        }
    }

    function frequencyToNote(frequency) {
        // Validate frequency
        if (!frequency || frequency <= 0 || !isFinite(frequency)) {
            return {
                note: '--',
                noteIndex: 0,
                octave: 0,
                cents: 0,
                midiNote: 0,
                valid: false
            };
        }

        // Calculate semitones from A4
        const semitones = 12 * Math.log2(frequency / referenceA4);
        
        // Check for valid calculation
        if (!isFinite(semitones)) {
            return {
                note: '--',
                noteIndex: 0,
                octave: 0,
                cents: 0,
                midiNote: 0,
                valid: false
            };
        }

        const noteNum = Math.round(semitones) + 69; // MIDI note number
        const cents = (semitones - Math.round(semitones)) * 100;

        // Calculate octave and note name
        const octave = Math.floor(noteNum / 12) - 1;
        const noteIndex = ((noteNum % 12) + 12) % 12; // Ensure positive index
        const noteName = NOTE_NAMES_SHARP[noteIndex] || 'C';

        return {
            note: noteName + octave,
            noteIndex: noteIndex,
            octave: octave,
            cents: cents,
            midiNote: noteNum,
            valid: true
        };
    }

    // Initialize on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
