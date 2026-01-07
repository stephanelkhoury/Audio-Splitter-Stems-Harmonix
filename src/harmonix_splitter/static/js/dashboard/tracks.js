/**
 * Dashboard Tracks Module
 * Handles track list management and stem separation
 */

const DashboardTracks = (function() {
    'use strict';
    
    let tracks = [];
    let processingJobId = null;
    let pollInterval = null;
    
    /**
     * Initialize tracks module
     */
    function init() {
        loadSavedTracks();
        setupEventListeners();
    }
    
    /**
     * Setup event listeners
     */
    function setupEventListeners() {
        // Separate button
        const separateBtn = document.getElementById('separate-btn');
        if (separateBtn) {
            separateBtn.addEventListener('click', startSeparation);
        }
        
        // Download all button
        const downloadAllBtn = document.getElementById('download-all-btn');
        if (downloadAllBtn) {
            downloadAllBtn.addEventListener('click', downloadAllStems);
        }
    }
    
    /**
     * Load saved tracks from API
     */
    async function loadSavedTracks() {
        try {
            const response = await fetch('/api/tracks');
            if (response.ok) {
                const data = await response.json();
                tracks = data.tracks || [];
                renderTrackList();
            }
        } catch (error) {
            console.error('Error loading tracks:', error);
        }
    }
    
    /**
     * Start audio separation
     */
    async function startSeparation() {
        const file = DashboardUpload.getSelectedFile();
        if (!file) {
            showToast('Please select an audio file first', 'warning');
            return;
        }
        
        const model = document.getElementById('model-select')?.value || 'htdemucs';
        const stems = document.getElementById('stems-select')?.value || '4';
        
        try {
            showProgress(true);
            updateProgress(0, 'Uploading file...');
            
            const formData = new FormData();
            formData.append('file', file);
            formData.append('model', model);
            formData.append('stems', stems);
            
            const response = await fetch('/api/separate', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                throw new Error('Separation request failed');
            }
            
            const data = await response.json();
            processingJobId = data.job_id;
            
            updateProgress(10, 'Processing started...');
            startProgressPolling();
            
        } catch (error) {
            console.error('Separation error:', error);
            showToast('Error starting separation: ' + error.message, 'error');
            showProgress(false);
        }
    }
    
    /**
     * Start polling for job progress
     */
    function startProgressPolling() {
        if (pollInterval) {
            clearInterval(pollInterval);
        }
        
        pollInterval = setInterval(async function() {
            try {
                const response = await fetch('/api/job/' + processingJobId);
                if (!response.ok) throw new Error('Failed to get job status');
                
                const data = await response.json();
                
                updateProgress(data.progress, data.status);
                
                if (data.state === 'completed') {
                    clearInterval(pollInterval);
                    pollInterval = null;
                    handleSeparationComplete(data);
                } else if (data.state === 'failed') {
                    clearInterval(pollInterval);
                    pollInterval = null;
                    handleSeparationError(data.error);
                }
            } catch (error) {
                console.error('Polling error:', error);
            }
        }, 2000);
    }
    
    /**
     * Handle separation complete
     */
    function handleSeparationComplete(data) {
        showProgress(false);
        showToast('Separation complete!', 'success');
        
        // Add track to list
        if (data.track) {
            tracks.unshift(data.track);
            renderTrackList();
        }
        
        // Load stems into player
        if (data.stems) {
            loadStemsIntoPlayer(data.stems);
        }
        
        // Switch to results section
        DashboardNav.switchToSection('results');
    }
    
    /**
     * Handle separation error
     */
    function handleSeparationError(error) {
        showProgress(false);
        showToast('Separation failed: ' + error, 'error');
    }
    
    /**
     * Load stems into player
     */
    function loadStemsIntoPlayer(stems) {
        const stemsContainer = document.getElementById('stems-container');
        if (!stemsContainer) return;
        
        stemsContainer.innerHTML = '';
        
        stems.forEach(function(stem, index) {
            const stemEl = createStemElement(stem, index);
            stemsContainer.appendChild(stemEl);
            
            // Initialize WaveSurfer for this stem
            const waveformContainer = stemEl.querySelector('.stem-waveform');
            if (waveformContainer) {
                DashboardPlayer.initStemTrack('stem-' + index, stem.url, waveformContainer);
            }
        });
    }
    
    /**
     * Create stem track element
     */
    function createStemElement(stem, index) {
        const div = document.createElement('div');
        div.className = 'stem-track';
        div.dataset.track = 'stem-' + index;
        
        const colors = ['#4CAF50', '#2196F3', '#FF9800', '#E91E63', '#9C27B0', '#00BCD4'];
        const color = colors[index % colors.length];
        
        div.innerHTML = `
            <div class="stem-header">
                <div class="stem-color" style="background: ${color}"></div>
                <span class="stem-name">${stem.name}</span>
                <div class="stem-controls">
                    <button class="btn btn-icon mute-btn" onclick="DashboardPlayer.toggleTrackMute('stem-${index}')">
                        <i class="fas fa-volume-up"></i>
                    </button>
                    <button class="btn btn-icon solo-btn" onclick="DashboardPlayer.soloTrack('stem-${index}')">
                        <i class="fas fa-headphones"></i>
                    </button>
                    <input type="range" class="track-volume" min="0" max="1" step="0.01" value="1" 
                           onchange="DashboardPlayer.setTrackVolume('stem-${index}', this.value)">
                    <button class="btn btn-icon download-btn" onclick="DashboardTracks.downloadStem('${stem.url}', '${stem.name}')">
                        <i class="fas fa-download"></i>
                    </button>
                </div>
            </div>
            <div class="stem-waveform"></div>
        `;
        
        return div;
    }
    
    /**
     * Render track list
     */
    function renderTrackList() {
        const listEl = document.getElementById('track-list');
        if (!listEl) return;
        
        if (tracks.length === 0) {
            listEl.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-music"></i>
                    <p>No tracks yet</p>
                    <p class="text-muted">Upload an audio file to get started</p>
                </div>
            `;
            return;
        }
        
        listEl.innerHTML = tracks.map(function(track) {
            return `
                <div class="track-item" data-id="${track.id}">
                    <div class="track-thumbnail">
                        <i class="fas fa-music"></i>
                    </div>
                    <div class="track-info">
                        <div class="track-name">${track.name}</div>
                        <div class="track-meta">
                            <span>${DashboardUtils.formatRelativeTime(track.created_at)}</span>
                            <span>${track.stems?.length || 0} stems</span>
                        </div>
                    </div>
                    <div class="track-actions">
                        <button class="btn btn-icon" onclick="DashboardTracks.loadTrack('${track.id}')">
                            <i class="fas fa-play"></i>
                        </button>
                        <button class="btn btn-icon" onclick="DashboardTracks.deleteTrack('${track.id}')">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            `;
        }).join('');
    }
    
    /**
     * Load a track
     */
    async function loadTrack(trackId) {
        try {
            const response = await fetch('/api/tracks/' + trackId);
            if (!response.ok) throw new Error('Failed to load track');
            
            const data = await response.json();
            
            if (data.stems) {
                loadStemsIntoPlayer(data.stems);
                DashboardNav.switchToSection('results');
                showToast('Track loaded', 'success');
            }
        } catch (error) {
            console.error('Error loading track:', error);
            showToast('Error loading track', 'error');
        }
    }
    
    /**
     * Delete a track
     */
    async function deleteTrack(trackId) {
        if (!confirm('Are you sure you want to delete this track?')) return;
        
        try {
            const response = await fetch('/api/tracks/' + trackId, {
                method: 'DELETE'
            });
            
            if (!response.ok) throw new Error('Failed to delete track');
            
            tracks = tracks.filter(function(t) {
                return t.id !== trackId;
            });
            
            renderTrackList();
            showToast('Track deleted', 'success');
        } catch (error) {
            console.error('Error deleting track:', error);
            showToast('Error deleting track', 'error');
        }
    }
    
    /**
     * Download a single stem
     */
    function downloadStem(url, name) {
        DashboardUtils.downloadFile(url, name + '.mp3');
    }
    
    /**
     * Download all stems as zip
     */
    async function downloadAllStems() {
        if (!processingJobId) {
            showToast('No stems to download', 'warning');
            return;
        }
        
        try {
            showToast('Preparing download...', 'info');
            
            const response = await fetch('/api/download/' + processingJobId);
            if (!response.ok) throw new Error('Download failed');
            
            const blob = await response.blob();
            DashboardUtils.downloadBlob(blob, 'stems.zip');
            
            showToast('Download started', 'success');
        } catch (error) {
            console.error('Download error:', error);
            showToast('Error downloading stems', 'error');
        }
    }
    
    /**
     * Show/hide progress bar
     */
    function showProgress(show) {
        const progressEl = document.getElementById('progress-container');
        if (progressEl) {
            progressEl.style.display = show ? 'block' : 'none';
        }
    }
    
    /**
     * Update progress bar
     */
    function updateProgress(percent, status) {
        const progressBar = document.getElementById('progress-bar');
        const progressText = document.getElementById('progress-text');
        
        if (progressBar) {
            progressBar.style.width = percent + '%';
        }
        if (progressText) {
            progressText.textContent = status || (percent + '%');
        }
    }
    
    /**
     * Get all tracks
     */
    function getTracks() {
        return tracks;
    }
    
    // Public API
    return {
        init: init,
        loadSavedTracks: loadSavedTracks,
        startSeparation: startSeparation,
        loadTrack: loadTrack,
        deleteTrack: deleteTrack,
        downloadStem: downloadStem,
        downloadAllStems: downloadAllStems,
        getTracks: getTracks
    };
})();

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    DashboardTracks.init();
});
