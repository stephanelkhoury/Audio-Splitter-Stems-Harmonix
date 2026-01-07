/**
 * Dashboard Main Module
 * Main entry point that initializes all dashboard modules
 */

const Dashboard = (function() {
    'use strict';
    
    let initialized = false;
    
    /**
     * Initialize the dashboard
     */
    function init() {
        if (initialized) return;
        
        console.log('Initializing Harmonix Dashboard...');
        
        // Initialize all modules in order
        initializeModules();
        
        // Setup global event handlers
        setupGlobalHandlers();
        
        // Mark as initialized
        initialized = true;
        
        console.log('Dashboard initialized successfully');
        showToast('Dashboard ready', 'success');
    }
    
    /**
     * Initialize all dashboard modules
     */
    function initializeModules() {
        // Core modules (order matters)
        const modules = [
            { name: 'Utils', module: window.DashboardUtils },
            { name: 'Toast', module: window.DashboardToast },
            { name: 'Theme', module: window.DashboardTheme },
            { name: 'Navigation', module: window.DashboardNav },
            { name: 'Modal', module: window.DashboardModal },
            { name: 'Upload', module: window.DashboardUpload },
            { name: 'Player', module: window.DashboardPlayer },
            { name: 'MidiPlayer', module: window.DashboardMidiPlayer },
            { name: 'Tracks', module: window.DashboardTracks }
        ];
        
        modules.forEach(function(item) {
            if (item.module && typeof item.module.init === 'function') {
                try {
                    // Note: modules self-initialize on DOMContentLoaded
                    // This is for explicit initialization if needed
                    console.log('Module ready:', item.name);
                } catch (error) {
                    console.error('Error initializing module ' + item.name + ':', error);
                }
            } else {
                console.warn('Module not found or no init method:', item.name);
            }
        });
    }
    
    /**
     * Setup global event handlers
     */
    function setupGlobalHandlers() {
        // Handle visibility change (pause when tab is hidden)
        document.addEventListener('visibilitychange', function() {
            if (document.hidden) {
                // Optionally pause audio when tab is hidden
                // DashboardPlayer.pause();
            }
        });
        
        // Handle before unload (warn about unsaved changes)
        window.addEventListener('beforeunload', function(e) {
            const playerState = DashboardPlayer?.getState?.();
            const midiState = DashboardMidiPlayer?.getState?.();
            
            if ((playerState?.isPlaying) || (midiState?.isPlaying)) {
                e.preventDefault();
                e.returnValue = 'Audio is still playing. Are you sure you want to leave?';
                return e.returnValue;
            }
        });
        
        // Handle errors
        window.addEventListener('error', function(e) {
            console.error('Global error:', e.error);
        });
        
        // Handle unhandled promise rejections
        window.addEventListener('unhandledrejection', function(e) {
            console.error('Unhandled promise rejection:', e.reason);
        });
        
        // Handle resize (debounced)
        let resizeTimeout;
        window.addEventListener('resize', function() {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(function() {
                handleResize();
            }, 250);
        });
    }
    
    /**
     * Handle window resize
     */
    function handleResize() {
        // Trigger resize event for modules that need it
        document.dispatchEvent(new CustomEvent('dashboard:resize'));
    }
    
    /**
     * Get dashboard state
     */
    function getState() {
        return {
            initialized: initialized,
            theme: DashboardTheme?.getCurrentTheme?.(),
            currentSection: DashboardNav?.getCurrentSection?.(),
            playerState: DashboardPlayer?.getState?.(),
            midiPlayerState: DashboardMidiPlayer?.getState?.()
        };
    }
    
    /**
     * Reset dashboard to initial state
     */
    function reset() {
        DashboardPlayer?.stop?.();
        DashboardMidiPlayer?.stop?.();
        DashboardNav?.switchToSection?.('stems');
        DashboardUpload?.clearSelection?.();
        showToast('Dashboard reset', 'info');
    }
    
    // Public API
    return {
        init: init,
        getState: getState,
        reset: reset
    };
})();

// NOTE: Auto-initialization disabled - modules are loaded but not auto-started
// to avoid conflicts with existing inline code in dashboard.html
// Modules can be used selectively by calling their init() methods manually
// document.addEventListener('DOMContentLoaded', function() {
//     Dashboard.init();
// });
