/**
 * Harmonix Design System - Main JavaScript
 * Entry point that imports and initializes all modules
 */

// Initialize all components when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    console.log('🎵 Harmonix Design System Loaded');
    
    // Setup theme toggle buttons
    setupThemeToggles();
    
    // Initialize audio wave visualizers
    initializeAudioWaves();
    
    // Initialize stat counters
    initializeCounters();
    
    // Smooth scroll for anchor links
    setupSmoothScroll();
    
    // Initialize tooltips
    initializeTooltips();
    
    // Initialize FAQ accordions
    initializeFAQ();
});

/**
 * Setup theme toggle button click handlers
 */
function setupThemeToggles() {
    const toggleButtons = document.querySelectorAll('.theme-toggle');
    
    toggleButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            if (window.themeManager) {
                window.themeManager.toggle();
            }
        });
    });
}

/**
 * Initialize audio wave visualizers on the page
 */
function initializeAudioWaves() {
    // Auto-initialize elements with data-audio-waves attribute
    const waveContainers = document.querySelectorAll('[data-audio-waves]');
    
    waveContainers.forEach(container => {
        const barCount = parseInt(container.dataset.barCount) || 8;
        new AudioWaveVisualizer(container, { barCount });
    });
    
    // Initialize demo waveform canvases
    const demoWaveforms = document.querySelectorAll('.demo-waveform');
    demoWaveforms.forEach(waveform => {
        if (!waveform.querySelector('canvas')) {
            const canvas = document.createElement('canvas');
            canvas.className = 'demo-waveform-canvas';
            waveform.appendChild(canvas);
        }
    });
}

/**
 * Initialize counter animations for stats
 */
function initializeCounters() {
    const counters = document.querySelectorAll('[data-counter]');
    
    counters.forEach(counter => {
        new CounterAnimation(counter, {
            duration: parseInt(counter.dataset.duration) || 2000,
            prefix: counter.dataset.prefix || '',
            suffix: counter.dataset.suffix || ''
        });
    });
}

/**
 * Setup smooth scrolling for anchor links
 */
function setupSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            
            // Skip if it's just "#"
            if (href === '#') return;
            
            const target = document.querySelector(href);
            
            if (target) {
                e.preventDefault();
                
                const navHeight = document.querySelector('.navbar')?.offsetHeight || 0;
                const targetPosition = target.getBoundingClientRect().top + window.pageYOffset - navHeight - 20;
                
                window.scrollTo({
                    top: targetPosition,
                    behavior: 'smooth'
                });
            }
        });
    });
}

/**
 * Initialize tooltips
 */
function initializeTooltips() {
    // Tooltips are CSS-based using data-tooltip attribute
    // This function can be extended for more complex tooltip behavior
}

/**
 * Initialize FAQ accordions
 */
function initializeFAQ() {
    const faqItems = document.querySelectorAll('.faq-item');
    
    faqItems.forEach(item => {
        const question = item.querySelector('.faq-question');
        
        if (question) {
            question.addEventListener('click', () => {
                // Close other items
                faqItems.forEach(otherItem => {
                    if (otherItem !== item && otherItem.classList.contains('active')) {
                        otherItem.classList.remove('active');
                    }
                });
                
                // Toggle current item
                item.classList.toggle('active');
            });
        }
    });
}

/**
 * Utility: Debounce function
 */
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

/**
 * Utility: Throttle function
 */
function throttle(func, limit) {
    let inThrottle;
    return function executedFunction(...args) {
        if (!inThrottle) {
            func(...args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

/**
 * Utility: Format number with commas
 */
function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

/**
 * Utility: Get CSS variable value
 */
function getCSSVariable(name) {
    return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

// Export utilities
window.harmonixUtils = {
    debounce,
    throttle,
    formatNumber,
    getCSSVariable
};
