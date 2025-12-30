# Design System Documentation

**Version:** 1.0.0  
**Last Updated:** December 30, 2025  
**Author:** Stephane El Khoury

---

## Overview

The Harmonix Design System provides a consistent visual language across the application. This document covers all design tokens, components, and patterns.

---

## Table of Contents

1. [Color Palette](#1-color-palette)
2. [Typography](#2-typography)
3. [Spacing](#3-spacing)
4. [Shadows & Effects](#4-shadows--effects)
5. [Components](#5-components)
6. [Layout Patterns](#6-layout-patterns)
7. [Responsive Design](#7-responsive-design)
8. [Accessibility](#8-accessibility)
9. [Animation Guidelines](#9-animation-guidelines)

---

## 1. Color Palette

### 1.1 Primary Colors

The primary color is **Purple** (`#7c3aed`), representing creativity and audio processing.

| Token | Hex | Usage |
|-------|-----|-------|
| `--primary` | `#7c3aed` | Primary buttons, active states, brand elements |
| `--primary-light` | `#a78bfa` | Hover states, highlights |
| `--primary-dark` | `#6d28d9` | Active/pressed states |

### 1.2 Secondary Colors

The secondary color is **Cyan** (`#06b6d4`), complementing the purple.

| Token | Hex | Usage |
|-------|-----|-------|
| `--secondary` | `#06b6d4` | Secondary actions, links |
| `--secondary-light` | `#22d3ee` | Hover states |
| `--secondary-dark` | `#0891b2` | Active states |

### 1.3 Accent Colors

| Token | Hex | Usage |
|-------|-----|-------|
| `--accent` | `#10b981` | Success, positive actions |
| `--accent-light` | `#34d399` | Highlights |
| `--accent-dark` | `#059669` | Active states |

### 1.4 Status Colors

| Token | Hex | Usage |
|-------|-----|-------|
| `--success` | `#10b981` | Success messages, completed states |
| `--warning` | `#f59e0b` | Warnings, caution states |
| `--error` | `#ef4444` | Errors, destructive actions |
| `--info` | `#3b82f6` | Information, tips |

### 1.5 Stem Colors

Each audio stem has a dedicated color for visual identification:

| Token | Hex | Stem | Icon |
|-------|-----|------|------|
| `--stem-vocals` | `#ef4444` | Vocals | microphone |
| `--stem-drums` | `#f59e0b` | Drums | drum |
| `--stem-bass` | `#8b5cf6` | Bass | guitar |
| `--stem-other` | `#06b6d4` | Other | music |
| `--stem-guitar` | `#10b981` | Guitar | guitar |
| `--stem-piano` | `#ec4899` | Piano | keyboard |

### 1.6 Background Colors (Dark Theme - Default)

| Token | Hex | Usage |
|-------|-----|-------|
| `--bg-dark` | `#0a0a0f` | Main background |
| `--bg-darker` | `#050508` | Deeper sections |
| `--bg-card` | `#12121a` | Card backgrounds |
| `--bg-input` | `#0d0d12` | Form inputs |

### 1.7 Background Colors (Light Theme)

| Token | Hex | Usage |
|-------|-----|-------|
| `--bg-dark` | `#ffffff` | Main background |
| `--bg-darker` | `#f1f5f9` | Deeper sections |
| `--bg-card` | `#ffffff` | Card backgrounds |
| `--bg-input` | `#f8fafc` | Form inputs |

### 1.8 Text Colors

| Token | Dark Theme | Light Theme | Usage |
|-------|------------|-------------|-------|
| `--text` | `#ffffff` | `#0f172a` | Primary text |
| `--text-muted` | `#a1a1aa` | `#475569` | Secondary text |
| `--text-dim` | `#71717a` | `#64748b` | Tertiary text, placeholders |

### 1.9 Border & Divider Colors

| Token | Dark Theme | Light Theme |
|-------|------------|-------------|
| `--border` | `rgba(255, 255, 255, 0.1)` | `rgba(0, 0, 0, 0.1)` |
| `--divider` | `rgba(255, 255, 255, 0.05)` | `rgba(0, 0, 0, 0.05)` |

---

## 2. Typography

### 2.1 Font Families

```css
:root {
    --font-primary: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    --font-mono: 'JetBrains Mono', 'Fira Code', 'SF Mono', Consolas, monospace;
}
```

### 2.2 Font Sizes

| Token | Size | Usage |
|-------|------|-------|
| `--font-size-xs` | 11px | Small labels, captions |
| `--font-size-sm` | 13px | Secondary text, metadata |
| `--font-size-base` | 15px | Body text |
| `--font-size-lg` | 18px | Large body, emphasis |
| `--font-size-xl` | 22px | Section titles |
| `--font-size-2xl` | 28px | Page subtitles |
| `--font-size-3xl` | 36px | Page titles |
| `--font-size-4xl` | 48px | Hero headlines |

### 2.3 Font Weights

| Token | Weight | Usage |
|-------|--------|-------|
| `--font-weight-normal` | 400 | Body text |
| `--font-weight-medium` | 500 | Emphasis, labels |
| `--font-weight-semibold` | 600 | Subheadings |
| `--font-weight-bold` | 700 | Headings |

### 2.4 Line Heights

| Token | Value | Usage |
|-------|-------|-------|
| `--line-height-tight` | 1.2 | Headings |
| `--line-height-normal` | 1.5 | Body text |
| `--line-height-relaxed` | 1.75 | Long-form content |

### 2.5 Typography Classes

```html
<h1 class="heading-xl">Hero Heading</h1>
<h2 class="heading-lg">Page Title</h2>
<h3 class="heading-md">Section Title</h3>
<p class="text-base">Regular paragraph text.</p>
<p class="text-sm text-muted">Secondary information.</p>
<code class="text-mono">code_example()</code>
```

---

## 3. Spacing

### 3.1 Spacing Scale

Based on a 4px grid system:

| Token | Size | Pixels |
|-------|------|--------|
| `--space-xs` | 4px | 0.25rem |
| `--space-sm` | 8px | 0.5rem |
| `--space-md` | 16px | 1rem |
| `--space-lg` | 24px | 1.5rem |
| `--space-xl` | 32px | 2rem |
| `--space-2xl` | 48px | 3rem |
| `--space-3xl` | 64px | 4rem |
| `--space-4xl` | 96px | 6rem |

### 3.2 Usage Guidelines

```css
/* Component internal spacing */
.card {
    padding: var(--space-lg);
    gap: var(--space-md);
}

/* Section spacing */
.section {
    padding: var(--space-3xl) 0;
}

/* Element spacing */
.button-group {
    gap: var(--space-sm);
}
```

---

## 4. Shadows & Effects

### 4.1 Shadow Scale

| Token | Value | Usage |
|-------|-------|-------|
| `--shadow-sm` | `0 1px 2px rgba(0,0,0,0.1)` | Subtle elevation |
| `--shadow-md` | `0 4px 12px rgba(0,0,0,0.15)` | Cards, dropdowns |
| `--shadow-lg` | `0 10px 30px rgba(0,0,0,0.2)` | Modals, popovers |
| `--shadow-xl` | `0 20px 50px rgba(0,0,0,0.3)` | Hero elements |

### 4.2 Glow Effects

```css
/* Primary glow */
.glow-primary {
    box-shadow: 0 0 20px rgba(124, 58, 237, 0.3);
}

/* Focus ring */
.focus-ring {
    box-shadow: 0 0 0 3px rgba(124, 58, 237, 0.2);
}

/* Stem glow */
.stem-vocals.active {
    box-shadow: 0 0 15px rgba(239, 68, 68, 0.4);
}
```

### 4.3 Gradients

```css
/* Primary gradient */
.gradient-primary {
    background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
}

/* Hero gradient */
.gradient-hero {
    background: linear-gradient(180deg, var(--bg-darker) 0%, var(--bg-dark) 100%);
}

/* Text gradient */
.text-gradient {
    background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
```

### 4.4 Border Radius

| Token | Size | Usage |
|-------|------|-------|
| `--radius-sm` | 4px | Small elements, badges |
| `--radius-md` | 8px | Buttons, inputs |
| `--radius-lg` | 12px | Cards |
| `--radius-xl` | 16px | Large cards, modals |
| `--radius-2xl` | 24px | Hero sections |
| `--radius-full` | 9999px | Circular elements, pills |

---

## 5. Components

### 5.1 Buttons

#### Button Variants

```html
<!-- Primary Button -->
<button class="btn btn-primary">Primary Action</button>

<!-- Secondary Button -->
<button class="btn btn-secondary">Secondary Action</button>

<!-- Ghost Button -->
<button class="btn btn-ghost">Ghost Action</button>

<!-- Danger Button -->
<button class="btn btn-danger">Delete</button>
```

#### Button Sizes

```html
<button class="btn btn-primary btn-sm">Small</button>
<button class="btn btn-primary">Default</button>
<button class="btn btn-primary btn-lg">Large</button>
```

#### Button with Icon

```html
<button class="btn btn-primary">
    <i class="fas fa-upload"></i>
    Upload File
</button>
```

#### Button CSS

```css
.btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: var(--space-sm);
    padding: 12px 24px;
    font-size: var(--font-size-base);
    font-weight: var(--font-weight-medium);
    border-radius: var(--radius-md);
    border: none;
    cursor: pointer;
    transition: all 0.2s ease;
}

.btn-primary {
    background: var(--primary);
    color: white;
}

.btn-primary:hover {
    background: var(--primary-light);
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(124, 58, 237, 0.3);
}

.btn-secondary {
    background: transparent;
    border: 1px solid var(--border);
    color: var(--text);
}

.btn-ghost {
    background: transparent;
    color: var(--text-muted);
}

.btn-ghost:hover {
    background: rgba(255, 255, 255, 0.05);
    color: var(--text);
}
```

### 5.2 Cards

```html
<div class="card">
    <div class="card-header">
        <h3 class="card-title">Card Title</h3>
        <p class="card-description">Card description text</p>
    </div>
    <div class="card-body">
        <!-- Card content -->
    </div>
    <div class="card-footer">
        <button class="btn btn-primary">Action</button>
    </div>
</div>
```

```css
.card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
    overflow: hidden;
}

.card-header {
    padding: var(--space-lg);
    border-bottom: 1px solid var(--border);
}

.card-title {
    font-size: var(--font-size-lg);
    font-weight: var(--font-weight-semibold);
    color: var(--text);
    margin: 0;
}

.card-description {
    font-size: var(--font-size-sm);
    color: var(--text-muted);
    margin-top: var(--space-xs);
}

.card-body {
    padding: var(--space-lg);
}

.card-footer {
    padding: var(--space-lg);
    border-top: 1px solid var(--border);
    background: rgba(0, 0, 0, 0.2);
}
```

### 5.3 Form Elements

#### Form Group

```html
<div class="form-group">
    <label class="form-label">Email Address</label>
    <input type="email" class="form-control" placeholder="you@example.com">
    <span class="form-hint">We'll never share your email.</span>
</div>
```

#### Form Input CSS

```css
.form-group {
    margin-bottom: var(--space-lg);
}

.form-label {
    display: block;
    font-size: var(--font-size-sm);
    font-weight: var(--font-weight-medium);
    color: var(--text);
    margin-bottom: var(--space-xs);
}

.form-control {
    width: 100%;
    padding: 12px 16px;
    font-size: var(--font-size-base);
    color: var(--text);
    background: var(--bg-input);
    border: 1px solid var(--border);
    border-radius: var(--radius-md);
    transition: all 0.2s ease;
}

.form-control:focus {
    outline: none;
    border-color: var(--primary);
    box-shadow: 0 0 0 3px rgba(124, 58, 237, 0.15);
}

.form-control::placeholder {
    color: var(--text-dim);
}

.form-hint {
    display: block;
    font-size: var(--font-size-xs);
    color: var(--text-dim);
    margin-top: var(--space-xs);
}

/* Light theme */
[data-theme="light"] .form-control {
    background: var(--bg-input);
    color: var(--text);
    border-color: rgba(0, 0, 0, 0.2);
}

[data-theme="light"] .form-control:focus {
    border-color: var(--primary);
}
```

#### Select

```html
<select class="form-control">
    <option value="">Select an option</option>
    <option value="1">Option 1</option>
    <option value="2">Option 2</option>
</select>
```

#### Textarea

```html
<textarea class="form-control" rows="4" placeholder="Your message..."></textarea>
```

### 5.4 Badges

```html
<span class="badge">Default</span>
<span class="badge badge-primary">Primary</span>
<span class="badge badge-success">Success</span>
<span class="badge badge-warning">Warning</span>
<span class="badge badge-error">Error</span>
```

```css
.badge {
    display: inline-flex;
    align-items: center;
    padding: 4px 10px;
    font-size: var(--font-size-xs);
    font-weight: var(--font-weight-medium);
    border-radius: var(--radius-full);
    background: rgba(255, 255, 255, 0.1);
    color: var(--text-muted);
}

.badge-primary {
    background: rgba(124, 58, 237, 0.2);
    color: var(--primary-light);
}

.badge-success {
    background: rgba(16, 185, 129, 0.2);
    color: var(--success);
}

.badge-warning {
    background: rgba(245, 158, 11, 0.2);
    color: var(--warning);
}

.badge-error {
    background: rgba(239, 68, 68, 0.2);
    color: var(--error);
}
```

### 5.5 Alerts

```html
<div class="alert alert-info">
    <i class="fas fa-info-circle"></i>
    <span>This is an informational message.</span>
</div>

<div class="alert alert-success">
    <i class="fas fa-check-circle"></i>
    <span>Operation completed successfully!</span>
</div>

<div class="alert alert-warning">
    <i class="fas fa-exclamation-triangle"></i>
    <span>Please review before continuing.</span>
</div>

<div class="alert alert-error">
    <i class="fas fa-times-circle"></i>
    <span>An error occurred. Please try again.</span>
</div>
```

### 5.6 Progress Bar

```html
<div class="progress">
    <div class="progress-bar" style="width: 65%"></div>
</div>
```

```css
.progress {
    height: 8px;
    background: rgba(255, 255, 255, 0.1);
    border-radius: var(--radius-full);
    overflow: hidden;
}

.progress-bar {
    height: 100%;
    background: linear-gradient(90deg, var(--primary), var(--secondary));
    border-radius: var(--radius-full);
    transition: width 0.3s ease;
}
```

---

## 6. Layout Patterns

### 6.1 Container

```html
<div class="container">
    <!-- Content limited to max-width -->
</div>
```

```css
.container {
    width: 100%;
    max-width: 1280px;
    margin: 0 auto;
    padding: 0 var(--space-lg);
}
```

### 6.2 Grid System

```html
<div class="grid grid-cols-3 gap-lg">
    <div>Column 1</div>
    <div>Column 2</div>
    <div>Column 3</div>
</div>
```

```css
.grid {
    display: grid;
}

.grid-cols-2 { grid-template-columns: repeat(2, 1fr); }
.grid-cols-3 { grid-template-columns: repeat(3, 1fr); }
.grid-cols-4 { grid-template-columns: repeat(4, 1fr); }

.gap-sm { gap: var(--space-sm); }
.gap-md { gap: var(--space-md); }
.gap-lg { gap: var(--space-lg); }
```

### 6.3 Flexbox Utilities

```html
<div class="flex items-center justify-between">
    <span>Left</span>
    <span>Right</span>
</div>
```

```css
.flex { display: flex; }
.flex-col { flex-direction: column; }
.items-center { align-items: center; }
.items-start { align-items: flex-start; }
.items-end { align-items: flex-end; }
.justify-center { justify-content: center; }
.justify-between { justify-content: space-between; }
.justify-end { justify-content: flex-end; }
```

### 6.4 Section Layout

```html
<section class="section">
    <div class="container">
        <div class="section-header">
            <h2 class="section-title">Section Title</h2>
            <p class="section-description">Description text</p>
        </div>
        <div class="section-content">
            <!-- Content -->
        </div>
    </div>
</section>
```

---

## 7. Responsive Design

### 7.1 Breakpoints

| Token | Width | Target |
|-------|-------|--------|
| `--breakpoint-sm` | 640px | Mobile landscape |
| `--breakpoint-md` | 768px | Tablet |
| `--breakpoint-lg` | 1024px | Desktop |
| `--breakpoint-xl` | 1280px | Large desktop |
| `--breakpoint-2xl` | 1536px | Extra large |

### 7.2 Media Queries

```css
/* Mobile first approach */
.element {
    padding: var(--space-md);
}

/* Tablet and up */
@media (min-width: 768px) {
    .element {
        padding: var(--space-lg);
    }
}

/* Desktop and up */
@media (min-width: 1024px) {
    .element {
        padding: var(--space-xl);
    }
}
```

### 7.3 Responsive Grid

```css
.grid {
    display: grid;
    grid-template-columns: 1fr;
    gap: var(--space-md);
}

@media (min-width: 640px) {
    .grid {
        grid-template-columns: repeat(2, 1fr);
    }
}

@media (min-width: 1024px) {
    .grid {
        grid-template-columns: repeat(3, 1fr);
        gap: var(--space-lg);
    }
}
```

### 7.4 Responsive Navigation

```css
.nav-links {
    display: none;
}

.mobile-menu-btn {
    display: block;
}

@media (min-width: 768px) {
    .nav-links {
        display: flex;
    }
    
    .mobile-menu-btn {
        display: none;
    }
}
```

---

## 8. Accessibility

### 8.1 Focus States

All interactive elements must have visible focus states:

```css
button:focus-visible,
a:focus-visible,
input:focus-visible {
    outline: none;
    box-shadow: 0 0 0 3px rgba(124, 58, 237, 0.3);
}
```

### 8.2 Color Contrast

- **Text on dark backgrounds**: Minimum 4.5:1 contrast ratio
- **Large text (18px+)**: Minimum 3:1 contrast ratio
- **UI components**: Minimum 3:1 contrast ratio

### 8.3 Screen Reader Support

```html
<!-- Skip link -->
<a href="#main-content" class="sr-only focus:not-sr-only">
    Skip to main content
</a>

<!-- Screen reader only -->
<span class="sr-only">Loading...</span>

<!-- Aria labels -->
<button aria-label="Close modal">
    <i class="fas fa-times"></i>
</button>
```

### 8.4 Reduced Motion

```css
@media (prefers-reduced-motion: reduce) {
    *,
    *::before,
    *::after {
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
    }
}
```

---

## 9. Animation Guidelines

### 9.1 Timing Functions

| Token | Value | Usage |
|-------|-------|-------|
| `--ease-in` | `cubic-bezier(0.4, 0, 1, 1)` | Elements entering |
| `--ease-out` | `cubic-bezier(0, 0, 0.2, 1)` | Elements leaving |
| `--ease-in-out` | `cubic-bezier(0.4, 0, 0.2, 1)` | General transitions |
| `--ease-bounce` | `cubic-bezier(0.34, 1.56, 0.64, 1)` | Playful animations |

### 9.2 Duration Scale

| Token | Duration | Usage |
|-------|----------|-------|
| `--duration-fast` | 100ms | Micro-interactions |
| `--duration-normal` | 200ms | Standard transitions |
| `--duration-slow` | 300ms | Complex animations |
| `--duration-slower` | 500ms | Major transitions |

### 9.3 Common Animations

```css
/* Fade in */
@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}

/* Slide up */
@keyframes slideUp {
    from {
        opacity: 0;
        transform: translateY(20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

/* Scale in */
@keyframes scaleIn {
    from {
        opacity: 0;
        transform: scale(0.95);
    }
    to {
        opacity: 1;
        transform: scale(1);
    }
}

/* Pulse */
@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}

/* Spin */
@keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
}
```

### 9.4 Animation Classes

```html
<div class="animate-fadeIn">Fade in content</div>
<div class="animate-slideUp">Slide up content</div>
<div class="animate-pulse">Pulsing element</div>
<div class="animate-spin">Spinning loader</div>
```

```css
.animate-fadeIn {
    animation: fadeIn var(--duration-normal) var(--ease-out);
}

.animate-slideUp {
    animation: slideUp var(--duration-slow) var(--ease-out);
}

.animate-pulse {
    animation: pulse 2s var(--ease-in-out) infinite;
}

.animate-spin {
    animation: spin 1s linear infinite;
}
```

### 9.5 Hover Transitions

```css
.hover-lift {
    transition: transform var(--duration-normal) var(--ease-out);
}

.hover-lift:hover {
    transform: translateY(-4px);
}

.hover-glow {
    transition: box-shadow var(--duration-normal) var(--ease-out);
}

.hover-glow:hover {
    box-shadow: 0 0 20px rgba(124, 58, 237, 0.4);
}
```

---

## Implementation Checklist

When creating new components:

- [ ] Use CSS custom properties for colors, spacing, typography
- [ ] Include dark and light theme variants
- [ ] Add focus states for accessibility
- [ ] Include hover/active states
- [ ] Test at all breakpoints
- [ ] Respect reduced motion preferences
- [ ] Use semantic HTML elements
- [ ] Include ARIA labels where needed

---

**Last Updated:** December 30, 2025  
**© 2025 Harmonix. All rights reserved.**
