/**
 * Harmonix Chord Transposer
 * Transpose chords in song lyrics up or down
 */

(function() {
    'use strict';

    // Chord definitions
    const NOTES_SHARP = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'];
    const NOTES_FLAT = ['C', 'Db', 'D', 'Eb', 'E', 'F', 'Gb', 'G', 'Ab', 'A', 'Bb', 'B'];
    
    // Map for parsing both sharp and flat notes
    const NOTE_MAP = {
        'C': 0, 'C#': 1, 'Db': 1,
        'D': 2, 'D#': 3, 'Eb': 3,
        'E': 4, 'Fb': 4,
        'F': 5, 'E#': 5, 'F#': 6, 'Gb': 6,
        'G': 7, 'G#': 8, 'Ab': 8,
        'A': 9, 'A#': 10, 'Bb': 10,
        'B': 11, 'Cb': 11
    };

    // Chord regex pattern - matches chords like C, Cm, C7, Cmaj7, C/E, etc.
    const CHORD_REGEX = /\[([A-G][#b]?(?:m|min|maj|dim|aug|sus|add|[0-9]|\/[A-G][#b]?)*)\]/gi;
    const CHORD_PATTERN = /^([A-G][#b]?)(m|min|maj|dim|aug|sus2|sus4|add[0-9]+|[0-9]+)?(\/([A-G][#b]?))?$/i;

    // State
    let transposeAmount = 0;
    let useSharp = true;
    let originalKey = '';

    // DOM Elements
    const chordInput = document.getElementById('chordInput');
    const chordOutput = document.getElementById('chordOutput');
    const transposeValueEl = document.getElementById('transposeValue');
    const newKeyDisplay = document.getElementById('newKeyDisplay');
    const originalKeySelect = document.getElementById('originalKey');
    const copyBtn = document.getElementById('copyBtn');
    const downloadBtn = document.getElementById('downloadBtn');
    const clearBtn = document.getElementById('clearBtn');
    const loadSampleBtn = document.getElementById('loadSampleBtn');
    const transposeBtns = document.querySelectorAll('.transpose-btn[data-semitones]');
    const toggleBtns = document.querySelectorAll('.toggle-btn[data-notation]');
    const quickKeyBtns = document.querySelectorAll('.quick-key-btn');

    // Sample song
    const SAMPLE_SONG = `[G]Amazing grace, how [C]sweet the [G]sound
That [G]saved a [Em]wretch like [D]me
I [G]once was lost, but [C]now am [G]found
Was [Em]blind, but [D]now I [G]see

[G]'Twas grace that [C]taught my [G]heart to fear
And [G]grace my [Em]fears re[D]lieved
How [G]precious did that [C]grace ap[G]pear
The [Em]hour I [D]first be[G]lieved

[G]Through many [C]dangers, [G]toils and snares
[G]I have al[Em]ready [D]come
[G]'Tis grace hath [C]brought me [G]safe thus far
And [Em]grace will [D]lead me [G]home`;

    // Initialize
    function init() {
        setupEventListeners();
        buildReferenceTable();
    }

    function setupEventListeners() {
        // Input change
        chordInput.addEventListener('input', debounce(updateTransposition, 100));
        originalKeySelect.addEventListener('change', updateTransposition);

        // Transpose buttons
        transposeBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                const semitones = parseInt(btn.dataset.semitones);
                transposeAmount += semitones;
                // Keep within -12 to +12 range
                if (transposeAmount > 12) transposeAmount -= 12;
                if (transposeAmount < -12) transposeAmount += 12;
                updateTransposition();
            });
        });

        // Notation toggle
        toggleBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                toggleBtns.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                useSharp = btn.dataset.notation === 'sharp';
                updateTransposition();
            });
        });

        // Quick key transpose
        quickKeyBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                const targetKey = btn.dataset.key;
                transposeToKey(targetKey);
            });
        });

        // Action buttons
        copyBtn.addEventListener('click', copyToClipboard);
        downloadBtn.addEventListener('click', downloadAsText);
        clearBtn.addEventListener('click', () => {
            chordInput.value = '';
            transposeAmount = 0;
            updateTransposition();
        });
        loadSampleBtn.addEventListener('click', () => {
            chordInput.value = SAMPLE_SONG;
            updateTransposition();
        });
    }

    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    function transposeChord(chord, semitones) {
        const match = chord.match(CHORD_PATTERN);
        if (!match) return chord;

        const root = match[1];
        const suffix = match[2] || '';
        const bassNote = match[4];

        // Transpose root note
        const rootIndex = NOTE_MAP[root];
        if (rootIndex === undefined) return chord;
        
        let newIndex = (rootIndex + semitones + 12) % 12;
        const notes = useSharp ? NOTES_SHARP : NOTES_FLAT;
        let newRoot = notes[newIndex];

        // Transpose bass note if present
        let newBass = '';
        if (bassNote) {
            const bassIndex = NOTE_MAP[bassNote];
            if (bassIndex !== undefined) {
                let newBassIndex = (bassIndex + semitones + 12) % 12;
                newBass = '/' + notes[newBassIndex];
            }
        }

        return newRoot + suffix + newBass;
    }

    function updateTransposition() {
        const input = chordInput.value;
        
        if (!input.trim()) {
            chordOutput.innerHTML = '<p class="placeholder-text">Your transposed chords will appear here...</p>';
            transposeValueEl.textContent = transposeAmount;
            newKeyDisplay.textContent = '--';
            return;
        }

        // Detect original key if auto
        let detectedKey = originalKeySelect.value;
        if (!detectedKey) {
            detectedKey = detectKey(input);
        }

        // Calculate new key
        const newKey = calculateNewKey(detectedKey, transposeAmount);
        newKeyDisplay.textContent = newKey || '--';
        transposeValueEl.textContent = (transposeAmount > 0 ? '+' : '') + transposeAmount;

        // Transpose the text
        const transposed = input.replace(CHORD_REGEX, (match, chord) => {
            const newChord = transposeChord(chord, transposeAmount);
            return '[' + newChord + ']';
        });

        // Format output with styled chords
        const formatted = transposed.replace(/\[([^\]]+)\]/g, '<span class="chord">$1</span>');
        chordOutput.innerHTML = '<pre>' + formatted + '</pre>';

        // Highlight current row in reference table
        highlightReferenceRow();
    }

    function detectKey(text) {
        // Simple key detection - find first chord
        const match = text.match(/\[([A-G][#b]?)/);
        if (match) {
            return match[1];
        }
        return 'C';
    }

    function calculateNewKey(originalKey, semitones) {
        if (!originalKey) return null;
        
        const keyIndex = NOTE_MAP[originalKey];
        if (keyIndex === undefined) return originalKey;
        
        const newIndex = (keyIndex + semitones + 12) % 12;
        const notes = useSharp ? NOTES_SHARP : NOTES_FLAT;
        return notes[newIndex];
    }

    function transposeToKey(targetKey) {
        const input = chordInput.value;
        if (!input.trim()) return;

        let detectedKey = originalKeySelect.value || detectKey(input);
        const currentIndex = NOTE_MAP[detectedKey] || 0;
        const targetIndex = NOTE_MAP[targetKey];

        if (targetIndex !== undefined) {
            transposeAmount = (targetIndex - currentIndex + 12) % 12;
            if (transposeAmount > 6) transposeAmount -= 12;
            updateTransposition();
        }
    }

    function buildReferenceTable() {
        const tbody = document.getElementById('referenceTableBody');
        if (!tbody) return;

        tbody.innerHTML = '';

        for (let i = -6; i <= 6; i++) {
            const row = document.createElement('tr');
            row.dataset.semitones = i;
            
            // Semitones column
            const semitoneCell = document.createElement('td');
            semitoneCell.textContent = (i > 0 ? '+' : '') + i;
            semitoneCell.className = i === 0 ? 'current' : '';
            row.appendChild(semitoneCell);

            // Note columns
            NOTES_SHARP.forEach((note, noteIndex) => {
                const cell = document.createElement('td');
                const transposedIndex = (noteIndex + i + 12) % 12;
                const notes = useSharp ? NOTES_SHARP : NOTES_FLAT;
                cell.textContent = notes[transposedIndex];
                row.appendChild(cell);
            });

            tbody.appendChild(row);
        }
    }

    function highlightReferenceRow() {
        const tbody = document.getElementById('referenceTableBody');
        if (!tbody) return;

        const rows = tbody.querySelectorAll('tr');
        rows.forEach(row => {
            const semitones = parseInt(row.dataset.semitones);
            if (semitones === transposeAmount) {
                row.classList.add('active');
            } else {
                row.classList.remove('active');
            }
        });
    }

    function copyToClipboard() {
        const output = chordOutput.textContent;
        if (!output || output.includes('will appear here')) return;

        navigator.clipboard.writeText(output).then(() => {
            // Show success feedback
            const originalIcon = copyBtn.innerHTML;
            copyBtn.innerHTML = '<i class="fas fa-check"></i>';
            copyBtn.classList.add('success');
            setTimeout(() => {
                copyBtn.innerHTML = originalIcon;
                copyBtn.classList.remove('success');
            }, 2000);
        }).catch(err => {
            console.error('Failed to copy:', err);
        });
    }

    function downloadAsText() {
        const output = chordOutput.textContent;
        if (!output || output.includes('will appear here')) return;

        const blob = new Blob([output], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'transposed-chords.txt';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    // Initialize on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
