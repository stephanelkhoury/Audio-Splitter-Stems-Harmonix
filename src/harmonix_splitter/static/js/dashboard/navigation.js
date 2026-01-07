/**
 * Dashboard Navigation Module
 * Handles sidebar navigation, section switching, and active states
 * NOTE: This module is available but NOT auto-initialized to avoid conflicts
 * with the inline navigation code in dashboard.html
 */

const DashboardNav = (function() {
    'use strict';
    
    let currentSection = 'stems';
    let initialized = false;
    
    /**
     * Initialize navigation
     * Call this manually if you want to use this module instead of inline code
     */
    function init() {
        if (initialized) return;
        setupNavItems();
        setupKeyboardNav();
        initialized = true;
    }
    
    /**
     * Setup navigation item click handlers
     */
    function setupNavItems() {
        document.querySelectorAll('.nav-item').forEach(function(item) {
            item.addEventListener('click', function() {
                const section = this.dataset.section;
                if (section) {
                    switchToSection(section);
                }
            });
        });
    }
    
    /**
     * Setup keyboard navigation
     */
    function setupKeyboardNav() {
        document.addEventListener('keydown', function(e) {
            // Ctrl+1-7 for quick section access
            if (e.ctrlKey && e.key >= '1' && e.key <= '7') {
                const sections = ['stems', 'midi-converter', 'tuner', 'transposer', 'account', 'docs', 'tutorials'];
                const index = parseInt(e.key) - 1;
                if (sections[index]) {
                    switchToSection(sections[index]);
                }
            }
        });
    }
    
    /**
     * Switch to a specific section
     * @param {string} section - Section name to switch to
     */
    function switchToSection(section) {
        // Update nav items
        document.querySelectorAll('.nav-item').forEach(function(item) {
            item.classList.remove('active');
            if (item.dataset.section === section) {
                item.classList.add('active');
            }
        });
        
        // Update content sections
        document.querySelectorAll('.content-section').forEach(function(s) {
            s.classList.remove('active');
        });
        
        const sectionEl = document.getElementById('section-' + section);
        if (sectionEl) {
            sectionEl.classList.add('active');
        }
        
        currentSection = section;
        
        // Trigger section-specific initialization
        if (typeof window['init' + capitalize(section)] === 'function') {
            window['init' + capitalize(section)]();
        }
    }
    
    /**
     * Get current active section
     * @returns {string} Current section name
     */
    function getCurrentSection() {
        return currentSection;
    }
    
    /**
     * Capitalize first letter of string
     */
    function capitalize(str) {
        return str.charAt(0).toUpperCase() + str.slice(1).replace(/-/g, '');
    }
    
    // Public API
    return {
        init: init,
        switchToSection: switchToSection,
        getCurrentSection: getCurrentSection
    };
})();

// NOTE: Auto-initialization disabled to avoid conflicts with inline navigation code
// If you want to use this module, call DashboardNav.init() manually after removing
// the inline initNavigation() code from dashboard.html
// document.addEventListener('DOMContentLoaded', function() {
//     DashboardNav.init();
// });
