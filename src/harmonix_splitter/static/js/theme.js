/**
 * Harmonix Design System - Theme Manager
 * Handles dark/light mode switching and persistence
 */

class ThemeManager {
    constructor() {
        this.storageKey = 'harmonix-theme';
        this.defaultTheme = 'dark';
        this.init();
    }

    init() {
        // Apply saved theme immediately to prevent flash
        const savedTheme = this.getSavedTheme();
        this.applyTheme(savedTheme);
        
        // Listen for system theme changes
        this.watchSystemTheme();
    }

    getSavedTheme() {
        const saved = localStorage.getItem(this.storageKey);
        if (saved) return saved;
        
        // Check system preference if no saved theme
        // But we default to dark as per design
        return this.defaultTheme;
    }

    applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        this.updateToggleIcon(theme);
    }

    toggle() {
        const currentTheme = document.documentElement.getAttribute('data-theme') || this.defaultTheme;
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        
        this.applyTheme(newTheme);
        localStorage.setItem(this.storageKey, newTheme);
        
        // Dispatch custom event for other components
        window.dispatchEvent(new CustomEvent('themechange', { detail: { theme: newTheme } }));
    }

    updateToggleIcon(theme) {
        const toggleButtons = document.querySelectorAll('.theme-toggle');
        toggleButtons.forEach(btn => {
            const icon = btn.querySelector('i');
            if (icon) {
                icon.className = theme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
            }
        });
    }

    watchSystemTheme() {
        const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
        mediaQuery.addEventListener('change', (e) => {
            // Only auto-switch if user hasn't manually set a preference
            if (!localStorage.getItem(this.storageKey)) {
                this.applyTheme(e.matches ? 'dark' : 'light');
            }
        });
    }

    getCurrentTheme() {
        return document.documentElement.getAttribute('data-theme') || this.defaultTheme;
    }
}

// Initialize theme manager immediately
const themeManager = new ThemeManager();

// Export for use in other modules
window.themeManager = themeManager;
