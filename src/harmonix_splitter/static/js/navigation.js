/**
 * Harmonix Design System - Navigation
 * Handles navbar behavior, dropdowns, and mobile menu
 */

class Navigation {
    constructor() {
        this.navbar = document.querySelector('.navbar');
        this.mobileToggle = document.querySelector('.mobile-menu-toggle');
        this.mobileMenu = document.querySelector('.mobile-menu');
        this.mobileOverlay = document.querySelector('.mobile-menu-overlay');
        this.mobileClose = document.querySelector('.mobile-menu-close');
        
        this.init();
    }

    init() {
        this.handleScroll();
        this.setupMobileMenu();
        this.setupDropdowns();
        this.setupActiveLinks();
    }

    handleScroll() {
        if (!this.navbar) return;
        
        let lastScroll = 0;
        const scrollThreshold = 50;
        
        window.addEventListener('scroll', () => {
            const currentScroll = window.pageYOffset;
            
            // Add scrolled class for background change
            if (currentScroll > scrollThreshold) {
                this.navbar.classList.add('scrolled');
            } else {
                this.navbar.classList.remove('scrolled');
            }
            
            // Hide/show navbar on scroll direction (optional)
            if (currentScroll > lastScroll && currentScroll > 200) {
                // this.navbar.classList.add('hidden');
            } else {
                // this.navbar.classList.remove('hidden');
            }
            
            lastScroll = currentScroll;
        });
    }

    setupMobileMenu() {
        if (!this.mobileToggle || !this.mobileMenu) return;
        
        // Toggle mobile menu
        this.mobileToggle.addEventListener('click', () => {
            this.openMobileMenu();
        });
        
        // Close button
        if (this.mobileClose) {
            this.mobileClose.addEventListener('click', () => {
                this.closeMobileMenu();
            });
        }
        
        // Overlay click
        if (this.mobileOverlay) {
            this.mobileOverlay.addEventListener('click', () => {
                this.closeMobileMenu();
            });
        }
        
        // Close on escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.mobileMenu.classList.contains('active')) {
                this.closeMobileMenu();
            }
        });
        
        // Close on link click
        const mobileLinks = this.mobileMenu.querySelectorAll('.mobile-nav-link');
        mobileLinks.forEach(link => {
            link.addEventListener('click', () => {
                this.closeMobileMenu();
            });
        });
    }

    openMobileMenu() {
        this.mobileMenu.classList.add('active');
        this.mobileOverlay.classList.add('active');
        document.body.style.overflow = 'hidden';
    }

    closeMobileMenu() {
        this.mobileMenu.classList.remove('active');
        this.mobileOverlay.classList.remove('active');
        document.body.style.overflow = '';
    }

    setupDropdowns() {
        // Dropdowns are handled by CSS hover, but we add touch support
        const dropdowns = document.querySelectorAll('.nav-dropdown');
        
        dropdowns.forEach(dropdown => {
            const trigger = dropdown.querySelector('.nav-dropdown-trigger');
            const menu = dropdown.querySelector('.nav-dropdown-menu');
            
            if (!trigger || !menu) return;
            
            // Touch support - use passive: false since we need preventDefault
            trigger.addEventListener('touchstart', (e) => {
                e.preventDefault();
                
                // Close other dropdowns
                dropdowns.forEach(d => {
                    if (d !== dropdown) {
                        d.classList.remove('open');
                    }
                });
                
                dropdown.classList.toggle('open');
            }, { passive: false });
        });
        
        // Close dropdowns on outside click
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.nav-dropdown')) {
                dropdowns.forEach(d => d.classList.remove('open'));
            }
        });
    }

    setupActiveLinks() {
        const currentPath = window.location.pathname;
        const navLinks = document.querySelectorAll('.nav-link, .mobile-nav-link');
        
        navLinks.forEach(link => {
            const href = link.getAttribute('href');
            if (href === currentPath || (currentPath === '/' && href === '/')) {
                link.classList.add('active');
            }
        });
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.navigation = new Navigation();
});
