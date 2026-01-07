/**
 * Dashboard Theme Module
 * Handles dark/light theme toggling and persistence
 */

const DashboardTheme = (function() {
    'use strict';
    
    const THEME_KEY = 'harmonix-theme';
    const DARK_THEME = 'dark';
    const LIGHT_THEME = 'light';
    
    /**
     * Initialize theme functionality
     */
    function init() {
        loadSavedTheme();
        setupThemeToggle();
    }
    
    /**
     * Load saved theme from localStorage
     */
    function loadSavedTheme() {
        const savedTheme = localStorage.getItem(THEME_KEY);
        
        if (savedTheme) {
            applyTheme(savedTheme);
        } else {
            // Check system preference
            const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
            applyTheme(prefersDark ? DARK_THEME : LIGHT_THEME);
        }
    }
    
    /**
     * Setup theme toggle button
     */
    function setupThemeToggle() {
        const toggleBtn = document.getElementById('theme-toggle');
        if (toggleBtn) {
            toggleBtn.addEventListener('click', toggle);
        }
        
        // Listen for system theme changes
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function(e) {
            if (!localStorage.getItem(THEME_KEY)) {
                applyTheme(e.matches ? DARK_THEME : LIGHT_THEME);
            }
        });
        
        // Keyboard shortcut for theme toggle (Ctrl/Cmd + Shift + T)
        document.addEventListener('keydown', function(e) {
            if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'T') {
                e.preventDefault();
                toggle();
            }
        });
    }
    
    /**
     * Apply theme to document
     */
    function applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        document.body.classList.remove(DARK_THEME, LIGHT_THEME);
        document.body.classList.add(theme);
        
        updateThemeIcon(theme);
    }
    
    /**
     * Update theme toggle icon
     */
    function updateThemeIcon(theme) {
        const toggleBtn = document.getElementById('theme-toggle');
        if (!toggleBtn) return;
        
        const icon = toggleBtn.querySelector('i');
        if (icon) {
            icon.className = theme === DARK_THEME ? 'fas fa-sun' : 'fas fa-moon';
        }
    }
    
    /**
     * Toggle between themes
     */
    function toggle() {
        const currentTheme = getCurrentTheme();
        const newTheme = currentTheme === DARK_THEME ? LIGHT_THEME : DARK_THEME;
        
        applyTheme(newTheme);
        localStorage.setItem(THEME_KEY, newTheme);
        
        showToast(`Switched to ${newTheme} mode`, 'success');
    }
    
    /**
     * Get current theme
     */
    function getCurrentTheme() {
        return document.documentElement.getAttribute('data-theme') || DARK_THEME;
    }
    
    /**
     * Set specific theme
     */
    function setTheme(theme) {
        if (theme === DARK_THEME || theme === LIGHT_THEME) {
            applyTheme(theme);
            localStorage.setItem(THEME_KEY, theme);
        }
    }
    
    /**
     * Check if dark theme is active
     */
    function isDark() {
        return getCurrentTheme() === DARK_THEME;
    }
    
    // Public API
    return {
        init: init,
        toggle: toggle,
        getCurrentTheme: getCurrentTheme,
        setTheme: setTheme,
        isDark: isDark,
        DARK_THEME: DARK_THEME,
        LIGHT_THEME: LIGHT_THEME
    };
})();

// NOTE: Auto-initialization disabled to avoid conflicts with inline theme code
// document.addEventListener('DOMContentLoaded', function() {
//     DashboardTheme.init();
// });
