/**
 * Dashboard Utilities Module
 * Shared utility functions for the dashboard
 */

const DashboardUtils = (function() {
    'use strict';
    
    /**
     * Format time in seconds to MM:SS
     */
    function formatTime(seconds) {
        if (isNaN(seconds) || seconds < 0) return '0:00';
        
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return mins + ':' + (secs < 10 ? '0' : '') + secs;
    }
    
    /**
     * Format file size to human readable
     */
    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    /**
     * Format date to relative time (e.g., "2 hours ago")
     */
    function formatRelativeTime(date) {
        const now = new Date();
        const diffMs = now - new Date(date);
        const diffSecs = Math.floor(diffMs / 1000);
        const diffMins = Math.floor(diffSecs / 60);
        const diffHours = Math.floor(diffMins / 60);
        const diffDays = Math.floor(diffHours / 24);
        
        if (diffSecs < 60) return 'just now';
        if (diffMins < 60) return diffMins + ' minute' + (diffMins > 1 ? 's' : '') + ' ago';
        if (diffHours < 24) return diffHours + ' hour' + (diffHours > 1 ? 's' : '') + ' ago';
        if (diffDays < 7) return diffDays + ' day' + (diffDays > 1 ? 's' : '') + ' ago';
        
        return new Date(date).toLocaleDateString();
    }
    
    /**
     * Debounce function to limit execution rate
     */
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = function() {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
    
    /**
     * Throttle function to limit execution rate
     */
    function throttle(func, limit) {
        let inThrottle;
        return function(...args) {
            if (!inThrottle) {
                func.apply(this, args);
                inThrottle = true;
                setTimeout(function() {
                    inThrottle = false;
                }, limit);
            }
        };
    }
    
    /**
     * Generate unique ID
     */
    function generateId() {
        return 'id-' + Date.now().toString(36) + '-' + Math.random().toString(36).substr(2, 9);
    }
    
    /**
     * Copy text to clipboard
     */
    async function copyToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
            showToast('Copied to clipboard', 'success');
            return true;
        } catch (err) {
            console.error('Failed to copy:', err);
            showToast('Failed to copy to clipboard', 'error');
            return false;
        }
    }
    
    /**
     * Download file from URL or blob
     */
    function downloadFile(url, filename) {
        const link = document.createElement('a');
        link.href = url;
        link.download = filename || 'download';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
    
    /**
     * Download blob as file
     */
    function downloadBlob(blob, filename) {
        const url = URL.createObjectURL(blob);
        downloadFile(url, filename);
        setTimeout(function() {
            URL.revokeObjectURL(url);
        }, 100);
    }
    
    /**
     * Check if element is in viewport
     */
    function isInViewport(element) {
        const rect = element.getBoundingClientRect();
        return (
            rect.top >= 0 &&
            rect.left >= 0 &&
            rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
            rect.right <= (window.innerWidth || document.documentElement.clientWidth)
        );
    }
    
    /**
     * Scroll to element smoothly
     */
    function scrollToElement(element, offset) {
        offset = offset || 0;
        const elementPosition = element.getBoundingClientRect().top + window.pageYOffset;
        const offsetPosition = elementPosition - offset;
        
        window.scrollTo({
            top: offsetPosition,
            behavior: 'smooth'
        });
    }
    
    /**
     * Parse query string parameters
     */
    function parseQueryString(queryString) {
        queryString = queryString || window.location.search;
        const params = {};
        const searchParams = new URLSearchParams(queryString);
        
        for (const [key, value] of searchParams) {
            params[key] = value;
        }
        
        return params;
    }
    
    /**
     * Validate email address
     */
    function isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }
    
    /**
     * Escape HTML special characters
     */
    function escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, function(m) {
            return map[m];
        });
    }
    
    /**
     * Clamp value between min and max
     */
    function clamp(value, min, max) {
        return Math.min(Math.max(value, min), max);
    }
    
    /**
     * Linear interpolation
     */
    function lerp(a, b, t) {
        return a + (b - a) * t;
    }
    
    /**
     * Map value from one range to another
     */
    function mapRange(value, inMin, inMax, outMin, outMax) {
        return (value - inMin) * (outMax - outMin) / (inMax - inMin) + outMin;
    }
    
    // Public API
    return {
        formatTime: formatTime,
        formatFileSize: formatFileSize,
        formatRelativeTime: formatRelativeTime,
        debounce: debounce,
        throttle: throttle,
        generateId: generateId,
        copyToClipboard: copyToClipboard,
        downloadFile: downloadFile,
        downloadBlob: downloadBlob,
        isInViewport: isInViewport,
        scrollToElement: scrollToElement,
        parseQueryString: parseQueryString,
        isValidEmail: isValidEmail,
        escapeHtml: escapeHtml,
        clamp: clamp,
        lerp: lerp,
        mapRange: mapRange
    };
})();

// NOTE: Global formatTime is NOT redefined here to avoid overwriting the inline version
// The inline formatTime in dashboard.html takes precedence
// Access via DashboardUtils.formatTime() if needed
