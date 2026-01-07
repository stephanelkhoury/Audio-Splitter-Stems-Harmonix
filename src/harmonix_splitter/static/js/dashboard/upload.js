/**
 * Dashboard Upload Module
 * Handles file uploads, drag & drop, and URL uploads
 */

const DashboardUpload = (function() {
    'use strict';
    
    let selectedFile = null;
    
    /**
     * Initialize upload functionality
     */
    function init() {
        setupDragAndDrop();
        setupFileInput();
        setupUrlUpload();
        setupUploadTabs();
    }
    
    /**
     * Setup drag and drop handlers
     */
    function setupDragAndDrop() {
        const uploadArea = document.getElementById('upload-area');
        if (!uploadArea) return;
        
        uploadArea.addEventListener('dragover', function(e) {
            e.preventDefault();
            this.classList.add('dragover');
        });
        
        uploadArea.addEventListener('dragleave', function() {
            this.classList.remove('dragover');
        });
        
        uploadArea.addEventListener('drop', function(e) {
            e.preventDefault();
            this.classList.remove('dragover');
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                handleFileSelect(files[0]);
            }
        });
        
        uploadArea.addEventListener('click', function() {
            const fileInput = document.getElementById('file-input');
            if (fileInput) fileInput.click();
        });
    }
    
    /**
     * Setup file input change handler
     */
    function setupFileInput() {
        const fileInput = document.getElementById('file-input');
        if (!fileInput) return;
        
        fileInput.addEventListener('change', function(e) {
            if (e.target.files.length > 0) {
                handleFileSelect(e.target.files[0]);
            }
        });
    }
    
    /**
     * Setup URL upload handlers
     */
    function setupUrlUpload() {
        const urlInput = document.getElementById('audio-url-input');
        const urlFetchBtn = document.getElementById('url-fetch-btn');
        
        if (urlFetchBtn) {
            urlFetchBtn.addEventListener('click', fetchUrlAudio);
        }
        
        if (urlInput) {
            urlInput.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    fetchUrlAudio();
                }
            });
        }
    }
    
    /**
     * Setup upload tab switching
     */
    function setupUploadTabs() {
        document.querySelectorAll('.upload-tab').forEach(function(tab) {
            tab.addEventListener('click', function() {
                const tabName = this.dataset.tab;
                switchUploadTab(tabName);
            });
        });
    }
    
    /**
     * Switch between upload tabs
     */
    function switchUploadTab(tabName) {
        // Update tab buttons
        document.querySelectorAll('.upload-tab').forEach(function(tab) {
            tab.classList.remove('active');
            if (tab.dataset.tab === tabName) {
                tab.classList.add('active');
            }
        });
        
        // Update tab content
        document.querySelectorAll('.upload-tab-content').forEach(function(content) {
            content.classList.remove('active');
        });
        
        const tabContent = document.getElementById('upload-' + tabName);
        if (tabContent) {
            tabContent.classList.add('active');
        }
    }
    
    /**
     * Handle file selection
     */
    function handleFileSelect(file) {
        if (!file) return;
        
        // Validate file type
        const validTypes = ['audio/mpeg', 'audio/wav', 'audio/mp3', 'audio/flac', 'audio/m4a'];
        if (!validTypes.includes(file.type) && !file.name.match(/\.(mp3|wav|flac|m4a)$/i)) {
            showToast('Please upload an audio file (MP3, WAV, FLAC, M4A)', 'error');
            return;
        }
        
        // Validate file size (500MB max)
        if (file.size > 500 * 1024 * 1024) {
            showToast('File too large. Maximum size is 500MB', 'error');
            return;
        }
        
        selectedFile = file;
        updateFilePreview(file);
        showToast('File selected: ' + file.name, 'success');
    }
    
    /**
     * Update file preview UI
     */
    function updateFilePreview(file) {
        const previewEl = document.getElementById('file-preview');
        if (previewEl) {
            previewEl.innerHTML = `
                <div class="file-preview-icon">
                    <i class="fas fa-music"></i>
                </div>
                <div class="file-preview-info">
                    <div class="file-preview-name">${file.name}</div>
                    <div class="file-preview-size">${formatFileSize(file.size)}</div>
                </div>
                <button class="btn btn-secondary" onclick="DashboardUpload.clearSelection()">
                    <i class="fas fa-times"></i>
                </button>
            `;
            previewEl.style.display = 'flex';
        }
    }
    
    /**
     * Fetch audio from URL
     */
    async function fetchUrlAudio() {
        const urlInput = document.getElementById('audio-url-input');
        const url = urlInput ? urlInput.value.trim() : '';
        
        if (!url) {
            showToast('Please enter a URL', 'error');
            return;
        }
        
        showToast('Fetching audio from URL...', 'info');
        
        // Implementation depends on backend API
        // This is a placeholder
        console.log('Fetching URL:', url);
    }
    
    /**
     * Clear file selection
     */
    function clearSelection() {
        selectedFile = null;
        const previewEl = document.getElementById('file-preview');
        if (previewEl) {
            previewEl.style.display = 'none';
        }
        const fileInput = document.getElementById('file-input');
        if (fileInput) {
            fileInput.value = '';
        }
    }
    
    /**
     * Get selected file
     */
    function getSelectedFile() {
        return selectedFile;
    }
    
    /**
     * Format file size to human readable
     */
    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    // Public API
    return {
        init: init,
        handleFileSelect: handleFileSelect,
        clearSelection: clearSelection,
        getSelectedFile: getSelectedFile,
        switchUploadTab: switchUploadTab
    };
})();

// NOTE: Auto-initialization disabled to avoid conflicts with inline upload code
// document.addEventListener('DOMContentLoaded', function() {
//     DashboardUpload.init();
// });
