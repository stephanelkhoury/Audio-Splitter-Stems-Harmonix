/**
 * Dashboard Toast Notifications Module
 * Handles toast notification display
 */

const DashboardToast = (function() {
    'use strict';
    
    let container = null;
    const defaultDuration = 3000;
    const maxToasts = 5;
    
    /**
     * Initialize toast container
     */
    function init() {
        if (!container) {
            container = document.getElementById('toast-container');
            if (!container) {
                container = document.createElement('div');
                container.id = 'toast-container';
                container.className = 'toast-container';
                document.body.appendChild(container);
            }
        }
    }
    
    /**
     * Show a toast notification
     * @param {string} message - The message to display
     * @param {string} type - Type: 'success', 'error', 'warning', 'info'
     * @param {number} duration - Duration in milliseconds
     */
    function show(message, type, duration) {
        init();
        
        type = type || 'info';
        duration = duration || defaultDuration;
        
        // Limit number of visible toasts
        const toasts = container.querySelectorAll('.toast');
        if (toasts.length >= maxToasts) {
            toasts[0].remove();
        }
        
        const toast = document.createElement('div');
        toast.className = 'toast toast-' + type;
        
        const icon = getIconForType(type);
        
        toast.innerHTML = `
            <div class="toast-icon">
                <i class="fas ${icon}"></i>
            </div>
            <div class="toast-content">
                <p class="toast-message">${message}</p>
            </div>
            <button class="toast-close" onclick="this.parentElement.remove()">
                <i class="fas fa-times"></i>
            </button>
        `;
        
        container.appendChild(toast);
        
        // Trigger animation
        requestAnimationFrame(function() {
            toast.classList.add('show');
        });
        
        // Auto remove after duration
        if (duration > 0) {
            setTimeout(function() {
                hide(toast);
            }, duration);
        }
        
        return toast;
    }
    
    /**
     * Hide a toast
     */
    function hide(toast) {
        if (!toast || !toast.parentElement) return;
        
        toast.classList.remove('show');
        toast.classList.add('hide');
        
        setTimeout(function() {
            if (toast.parentElement) {
                toast.remove();
            }
        }, 300);
    }
    
    /**
     * Get icon class for toast type
     */
    function getIconForType(type) {
        const icons = {
            success: 'fa-check-circle',
            error: 'fa-exclamation-circle',
            warning: 'fa-exclamation-triangle',
            info: 'fa-info-circle'
        };
        return icons[type] || icons.info;
    }
    
    /**
     * Show success toast
     */
    function success(message, duration) {
        return show(message, 'success', duration);
    }
    
    /**
     * Show error toast
     */
    function error(message, duration) {
        return show(message, 'error', duration);
    }
    
    /**
     * Show warning toast
     */
    function warning(message, duration) {
        return show(message, 'warning', duration);
    }
    
    /**
     * Show info toast
     */
    function info(message, duration) {
        return show(message, 'info', duration);
    }
    
    /**
     * Clear all toasts
     */
    function clearAll() {
        if (container) {
            container.innerHTML = '';
        }
    }
    
    // Public API
    return {
        init: init,
        show: show,
        hide: hide,
        success: success,
        error: error,
        warning: warning,
        info: info,
        clearAll: clearAll
    };
})();

// NOTE: Global showToast is NOT redefined here to avoid overwriting the inline version
// The inline showToast in dashboard.html takes precedence
// If you want to use the modular toast system, remove the inline showToast function

// NOTE: Auto-initialization disabled to avoid conflicts with inline toast code
// document.addEventListener('DOMContentLoaded', function() {
//     DashboardToast.init();
// });
