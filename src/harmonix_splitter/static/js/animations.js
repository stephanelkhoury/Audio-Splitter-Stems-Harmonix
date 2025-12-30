/**
 * Harmonix Design System - Animations
 * Scroll reveals, particles, and audio visualizations
 */

class AnimationManager {
    constructor() {
        this.init();
    }

    init() {
        this.setupScrollReveal();
        this.setupParticles();
        this.setupAudioVisualizers();
    }

    // === Scroll Reveal ===
    setupScrollReveal() {
        const observerOptions = {
            root: null,
            rootMargin: '0px',
            threshold: 0.1
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('visible');
                    
                    // Handle staggered children
                    if (entry.target.classList.contains('stagger-children')) {
                        entry.target.classList.add('visible');
                    }
                }
            });
        }, observerOptions);

        // Observe all animated elements
        const animatedElements = document.querySelectorAll(
            '.fade-in, .fade-in-left, .fade-in-right, .scale-in, .stagger-children'
        );
        
        animatedElements.forEach(el => observer.observe(el));
    }

    // === Particle System ===
    setupParticles() {
        const container = document.querySelector('.particles-container');
        if (!container) return;

        const particleCount = 30;
        
        for (let i = 0; i < particleCount; i++) {
            const particle = document.createElement('div');
            particle.className = 'particle';
            
            // Random properties
            const size = Math.random() * 4 + 2;
            const left = Math.random() * 100;
            const delay = Math.random() * 15;
            const duration = Math.random() * 10 + 10;
            const hue = Math.random() > 0.5 ? '262' : '186'; // Purple or cyan
            
            particle.style.cssText = `
                width: ${size}px;
                height: ${size}px;
                left: ${left}%;
                animation-delay: ${delay}s;
                animation-duration: ${duration}s;
                background: hsl(${hue}, 70%, 60%);
            `;
            
            container.appendChild(particle);
        }
    }

    // === Audio Visualizers ===
    setupAudioVisualizers() {
        this.setupWaveformCanvas();
        this.setupFrequencyBars();
    }

    setupWaveformCanvas() {
        const canvases = document.querySelectorAll('.demo-waveform-canvas');
        
        canvases.forEach(canvas => {
            const ctx = canvas.getContext('2d');
            if (!ctx) return;

            // Set canvas size
            const resize = () => {
                canvas.width = canvas.parentElement.offsetWidth;
                canvas.height = canvas.parentElement.offsetHeight;
            };
            resize();
            window.addEventListener('resize', resize);

            // Animation variables
            let phase = 0;
            
            const draw = () => {
                const { width, height } = canvas;
                ctx.clearRect(0, 0, width, height);
                
                // Draw multiple waves
                this.drawWave(ctx, width, height, phase, 'rgba(124, 58, 237, 0.6)', 30, 1);
                this.drawWave(ctx, width, height, phase + 1, 'rgba(6, 182, 212, 0.4)', 20, 0.8);
                this.drawWave(ctx, width, height, phase + 2, 'rgba(16, 185, 129, 0.3)', 15, 0.6);
                
                phase += 0.02;
                requestAnimationFrame(draw);
            };
            
            draw();
        });
    }

    drawWave(ctx, width, height, phase, color, amplitude, frequency) {
        ctx.beginPath();
        ctx.strokeStyle = color;
        ctx.lineWidth = 2;
        
        const centerY = height / 2;
        
        for (let x = 0; x <= width; x++) {
            const y = centerY + Math.sin(x * 0.02 * frequency + phase) * amplitude;
            
            if (x === 0) {
                ctx.moveTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }
        }
        
        ctx.stroke();
    }

    setupFrequencyBars() {
        const containers = document.querySelectorAll('.frequency-bars');
        
        containers.forEach(container => {
            // Create bars if not already present
            if (container.children.length === 0) {
                for (let i = 0; i < 16; i++) {
                    const bar = document.createElement('div');
                    bar.className = 'frequency-bar';
                    container.appendChild(bar);
                }
            }
            
            // Animate bars randomly
            const bars = container.querySelectorAll('.frequency-bar');
            
            const animate = () => {
                bars.forEach(bar => {
                    const height = Math.random() * 80 + 20;
                    bar.style.height = `${height}%`;
                });
            };
            
            // Initial animation
            animate();
            
            // Continuous animation
            setInterval(animate, 150);
        });
    }
}

// === Audio Wave Component ===
class AudioWaveVisualizer {
    constructor(container, options = {}) {
        this.container = container;
        this.options = {
            barCount: options.barCount || 8,
            minHeight: options.minHeight || 20,
            maxHeight: options.maxHeight || 100,
            color: options.color || 'linear-gradient(to top, var(--primary), var(--secondary))',
            speed: options.speed || 100,
            ...options
        };
        
        this.init();
    }

    init() {
        this.container.classList.add('audio-waves');
        this.container.innerHTML = '';
        
        for (let i = 0; i < this.options.barCount; i++) {
            const bar = document.createElement('div');
            bar.className = 'bar';
            bar.style.animationDelay = `${i * 0.1}s`;
            this.container.appendChild(bar);
        }
    }

    start() {
        this.container.classList.add('playing');
    }

    stop() {
        this.container.classList.remove('playing');
    }
}

// === Typewriter Effect ===
class Typewriter {
    constructor(element, options = {}) {
        this.element = element;
        this.text = options.text || element.textContent;
        this.speed = options.speed || 50;
        this.delay = options.delay || 0;
        this.loop = options.loop || false;
        this.cursor = options.cursor || true;
        
        this.init();
    }

    init() {
        this.element.textContent = '';
        if (this.cursor) {
            this.element.classList.add('typing-cursor');
        }
        
        setTimeout(() => this.type(), this.delay);
    }

    type() {
        let i = 0;
        
        const typing = setInterval(() => {
            if (i < this.text.length) {
                this.element.textContent += this.text.charAt(i);
                i++;
            } else {
                clearInterval(typing);
                
                if (this.loop) {
                    setTimeout(() => {
                        this.element.textContent = '';
                        this.type();
                    }, 2000);
                }
            }
        }, this.speed);
    }
}

// === Counter Animation ===
class CounterAnimation {
    constructor(element, options = {}) {
        this.element = element;
        this.target = parseInt(element.textContent) || options.target || 0;
        this.duration = options.duration || 2000;
        this.prefix = options.prefix || '';
        this.suffix = options.suffix || '';
        
        this.init();
    }

    init() {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    this.animate();
                    observer.unobserve(entry.target);
                }
            });
        });
        
        observer.observe(this.element);
    }

    animate() {
        const start = 0;
        const startTime = performance.now();
        
        const update = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / this.duration, 1);
            const eased = this.easeOutQuart(progress);
            const current = Math.floor(start + (this.target - start) * eased);
            
            this.element.textContent = this.prefix + current + this.suffix;
            
            if (progress < 1) {
                requestAnimationFrame(update);
            }
        };
        
        requestAnimationFrame(update);
    }

    easeOutQuart(x) {
        return 1 - Math.pow(1 - x, 4);
    }
}

// Initialize animations when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.animationManager = new AnimationManager();
});

// Export for use in other modules
window.AudioWaveVisualizer = AudioWaveVisualizer;
window.Typewriter = Typewriter;
window.CounterAnimation = CounterAnimation;
