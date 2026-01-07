/**
 * Dashboard Modal Module
 * Handles modal dialogs
 */

const DashboardModal = (function() {
    'use strict';
    
    let activeModals = [];
    
    /**
     * Initialize modal module
     */
    function init() {
        setupCloseHandlers();
        setupKeyboardHandlers();
    }
    
    /**
     * Setup close button handlers
     */
    function setupCloseHandlers() {
        // Close button clicks
        document.querySelectorAll('.modal-close, [data-modal-close]').forEach(function(btn) {
            btn.addEventListener('click', function() {
                const modal = this.closest('.modal');
                if (modal) {
                    close(modal.id);
                }
            });
        });
        
        // Backdrop clicks
        document.querySelectorAll('.modal').forEach(function(modal) {
            modal.addEventListener('click', function(e) {
                if (e.target === this) {
                    close(this.id);
                }
            });
        });
    }
    
    /**
     * Setup keyboard handlers
     */
    function setupKeyboardHandlers() {
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && activeModals.length > 0) {
                const topModal = activeModals[activeModals.length - 1];
                close(topModal);
            }
        });
    }
    
    /**
     * Open a modal
     */
    function open(modalId) {
        const modal = document.getElementById(modalId);
        if (!modal) {
            console.error('Modal not found:', modalId);
            return;
        }
        
        // Add to active modals stack
        activeModals.push(modalId);
        
        // Show modal
        modal.classList.add('active', 'show');
        document.body.classList.add('modal-open');
        
        // Focus first focusable element
        const focusable = modal.querySelector('button, input, select, textarea, [tabindex]:not([tabindex="-1"])');
        if (focusable) {
            setTimeout(function() {
                focusable.focus();
            }, 100);
        }
        
        // Trigger open event
        modal.dispatchEvent(new CustomEvent('modal:open', { detail: { modalId: modalId } }));
    }
    
    /**
     * Close a modal
     */
    function close(modalId) {
        const modal = document.getElementById(modalId);
        if (!modal) return;
        
        // Remove from active modals
        activeModals = activeModals.filter(function(id) {
            return id !== modalId;
        });
        
        // Hide modal
        modal.classList.remove('active', 'show');
        
        // Remove body class if no more modals
        if (activeModals.length === 0) {
            document.body.classList.remove('modal-open');
        }
        
        // Trigger close event
        modal.dispatchEvent(new CustomEvent('modal:close', { detail: { modalId: modalId } }));
    }
    
    /**
     * Close all modals
     */
    function closeAll() {
        activeModals.slice().forEach(function(modalId) {
            close(modalId);
        });
    }
    
    /**
     * Toggle modal
     */
    function toggle(modalId) {
        const modal = document.getElementById(modalId);
        if (modal && modal.classList.contains('active')) {
            close(modalId);
        } else {
            open(modalId);
        }
    }
    
    /**
     * Create a confirm dialog
     */
    function confirm(message, options) {
        options = options || {};
        
        return new Promise(function(resolve) {
            const modalId = 'confirm-modal-' + Date.now();
            
            const modalHtml = `
                <div class="modal" id="${modalId}">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h3 class="modal-title">${options.title || 'Confirm'}</h3>
                            <button class="modal-close" data-modal-close>
                                <i class="fas fa-times"></i>
                            </button>
                        </div>
                        <div class="modal-body">
                            <p>${message}</p>
                        </div>
                        <div class="modal-footer">
                            <button class="btn btn-secondary" data-action="cancel">
                                ${options.cancelText || 'Cancel'}
                            </button>
                            <button class="btn btn-primary" data-action="confirm">
                                ${options.confirmText || 'Confirm'}
                            </button>
                        </div>
                    </div>
                </div>
            `;
            
            document.body.insertAdjacentHTML('beforeend', modalHtml);
            const modal = document.getElementById(modalId);
            
            // Handle button clicks
            modal.querySelector('[data-action="confirm"]').addEventListener('click', function() {
                close(modalId);
                modal.remove();
                resolve(true);
            });
            
            modal.querySelector('[data-action="cancel"]').addEventListener('click', function() {
                close(modalId);
                modal.remove();
                resolve(false);
            });
            
            modal.querySelector('.modal-close').addEventListener('click', function() {
                modal.remove();
                resolve(false);
            });
            
            open(modalId);
        });
    }
    
    /**
     * Create an alert dialog
     */
    function alert(message, options) {
        options = options || {};
        
        return new Promise(function(resolve) {
            const modalId = 'alert-modal-' + Date.now();
            
            const modalHtml = `
                <div class="modal" id="${modalId}">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h3 class="modal-title">${options.title || 'Alert'}</h3>
                            <button class="modal-close" data-modal-close>
                                <i class="fas fa-times"></i>
                            </button>
                        </div>
                        <div class="modal-body">
                            <p>${message}</p>
                        </div>
                        <div class="modal-footer">
                            <button class="btn btn-primary" data-action="ok">
                                ${options.okText || 'OK'}
                            </button>
                        </div>
                    </div>
                </div>
            `;
            
            document.body.insertAdjacentHTML('beforeend', modalHtml);
            const modal = document.getElementById(modalId);
            
            modal.querySelector('[data-action="ok"]').addEventListener('click', function() {
                close(modalId);
                modal.remove();
                resolve();
            });
            
            modal.querySelector('.modal-close').addEventListener('click', function() {
                modal.remove();
                resolve();
            });
            
            open(modalId);
        });
    }
    
    /**
     * Check if any modal is open
     */
    function isOpen() {
        return activeModals.length > 0;
    }
    
    /**
     * Get active modal IDs
     */
    function getActiveModals() {
        return activeModals.slice();
    }
    
    // Public API
    return {
        init: init,
        open: open,
        close: close,
        closeAll: closeAll,
        toggle: toggle,
        confirm: confirm,
        alert: alert,
        isOpen: isOpen,
        getActiveModals: getActiveModals
    };
})();

// NOTE: Auto-initialization disabled to avoid conflicts with inline modal code
// document.addEventListener('DOMContentLoaded', function() {
//     DashboardModal.init();
// });
