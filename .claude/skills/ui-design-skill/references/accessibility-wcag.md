# Accessibility (WCAG)

## Table of Contents
- [WCAG Overview](#wcag-overview)
- [Perceivable](#perceivable)
- [Operable](#operable)
- [Understandable](#understandable)
- [Robust](#robust)
- [ARIA Guidelines](#aria-guidelines)
- [Testing](#testing)
- [Common Patterns](#common-patterns)

## WCAG Overview

### Conformance Levels

| Level | Description | Target |
|-------|-------------|--------|
| A | Minimum accessibility | Basic compliance |
| AA | Addresses major barriers | **Standard target** |
| AAA | Highest accessibility | Enhanced experience |

### Four Principles (POUR)

1. **Perceivable** - Users can perceive the content
2. **Operable** - Users can operate the interface
3. **Understandable** - Users can understand the content
4. **Robust** - Content works with assistive technologies

## Perceivable

### Text Alternatives (1.1)

```html
<!-- Images -->
<img src="chart.png" alt="Sales increased 20% in Q4 2024" />

<!-- Decorative images -->
<img src="divider.png" alt="" role="presentation" />

<!-- Icons with meaning -->
<button aria-label="Delete task">
  <svg aria-hidden="true"><!-- trash icon --></svg>
</button>

<!-- Complex images -->
<figure>
  <img src="diagram.png" alt="System architecture diagram" />
  <figcaption>
    Detailed description of the architecture...
  </figcaption>
</figure>
```

### Color Contrast (1.4.3)

| Element | Minimum Ratio (AA) | Enhanced (AAA) |
|---------|-------------------|----------------|
| Normal text | 4.5:1 | 7:1 |
| Large text (18px+) | 3:1 | 4.5:1 |
| UI components | 3:1 | - |

```html
<!-- Good contrast -->
<p class="text-gray-900 bg-white">Good: 21:1 ratio</p>
<p class="text-gray-700 bg-white">Good: 8.6:1 ratio</p>

<!-- Bad contrast -->
<p class="text-gray-400 bg-white">Bad: 2.7:1 ratio</p>
```

### Color Independence (1.4.1)

```html
<!-- Bad: color only -->
<span class="text-red-500">Required</span>

<!-- Good: color + text/icon -->
<span class="text-red-500">* Required</span>
<span class="text-red-500">
  <svg><!-- warning icon --></svg>
  Error: Field required
</span>
```

### Text Resizing (1.4.4)

```css
/* Use relative units */
body {
  font-size: 100%;      /* Respects user settings */
}

h1 {
  font-size: 2rem;      /* Scales with root */
}

.container {
  max-width: 70ch;      /* Character-based width */
  padding: 1em;         /* Scales with font */
}
```

## Operable

### Keyboard Accessibility (2.1.1)

```html
<!-- All interactive elements must be focusable -->
<button>Click me</button>           <!-- Focusable by default -->
<a href="/page">Link</a>            <!-- Focusable by default -->

<!-- Custom elements need tabindex -->
<div role="button" tabindex="0" onclick="..." onkeydown="...">
  Custom button
</div>

<!-- Skip to main content -->
<a href="#main" class="sr-only focus:not-sr-only">
  Skip to main content
</a>

<main id="main" tabindex="-1">
  Main content
</main>
```

### Focus Management (2.4.7)

```css
/* Visible focus indicator */
:focus {
  outline: 2px solid #2563eb;
  outline-offset: 2px;
}

/* Focus-visible for keyboard only */
:focus:not(:focus-visible) {
  outline: none;
}

:focus-visible {
  outline: 2px solid #2563eb;
  outline-offset: 2px;
}
```

```html
<!-- Tailwind focus styles -->
<button class="focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2">
  Button
</button>
```

### Keyboard Navigation

```javascript
// Handle keyboard events
element.addEventListener('keydown', (e) => {
  switch (e.key) {
    case 'Enter':
    case ' ':
      e.preventDefault();
      activate();
      break;
    case 'Escape':
      close();
      break;
    case 'ArrowDown':
      focusNext();
      break;
    case 'ArrowUp':
      focusPrevious();
      break;
  }
});
```

### No Keyboard Traps (2.1.2)

```javascript
// Modal focus trap (correct implementation)
function trapFocus(modal) {
  const focusableElements = modal.querySelectorAll(
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
  );
  const firstFocusable = focusableElements[0];
  const lastFocusable = focusableElements[focusableElements.length - 1];

  modal.addEventListener('keydown', (e) => {
    if (e.key === 'Tab') {
      if (e.shiftKey && document.activeElement === firstFocusable) {
        e.preventDefault();
        lastFocusable.focus();
      } else if (!e.shiftKey && document.activeElement === lastFocusable) {
        e.preventDefault();
        firstFocusable.focus();
      }
    }

    // Allow escape to close
    if (e.key === 'Escape') {
      closeModal();
    }
  });
}
```

### Timing (2.2)

```html
<!-- Allow users to extend time limits -->
<div role="alert" aria-live="polite">
  Session expires in 2 minutes.
  <button>Extend session</button>
</div>
```

## Understandable

### Language (3.1)

```html
<html lang="en">
  <body>
    <p>English content</p>
    <p lang="es">Contenido en español</p>
  </body>
</html>
```

### Consistent Navigation (3.2.3)

```html
<!-- Same navigation order across pages -->
<nav aria-label="Main navigation">
  <ul>
    <li><a href="/">Home</a></li>
    <li><a href="/tasks">Tasks</a></li>
    <li><a href="/settings">Settings</a></li>
  </ul>
</nav>
```

### Error Identification (3.3.1)

```html
<div>
  <label for="email">Email</label>
  <input
    type="email"
    id="email"
    aria-invalid="true"
    aria-describedby="email-error"
  />
  <p id="email-error" class="text-red-600">
    Please enter a valid email address (e.g., user@example.com)
  </p>
</div>
```

### Labels and Instructions (3.3.2)

```html
<form>
  <!-- Explicit label -->
  <label for="title">Task Title (required)</label>
  <input type="text" id="title" required aria-required="true" />

  <!-- Helper text -->
  <label for="due">Due Date</label>
  <input type="date" id="due" aria-describedby="due-help" />
  <p id="due-help" class="text-gray-500 text-sm">
    Format: MM/DD/YYYY
  </p>
</form>
```

## Robust

### Valid HTML (4.1.1)

```html
<!-- Use semantic HTML -->
<header>...</header>
<nav>...</nav>
<main>...</main>
<article>...</article>
<section>...</section>
<aside>...</aside>
<footer>...</footer>

<!-- Proper heading hierarchy -->
<h1>Page Title</h1>
  <h2>Section</h2>
    <h3>Subsection</h3>
  <h2>Another Section</h2>
```

### Name, Role, Value (4.1.2)

```html
<!-- Native elements have built-in semantics -->
<button>Submit</button>
<input type="checkbox" checked />
<select><option>Choose</option></select>

<!-- Custom elements need ARIA -->
<div
  role="checkbox"
  aria-checked="true"
  aria-label="Accept terms"
  tabindex="0"
>
  ✓
</div>
```

## ARIA Guidelines

### ARIA Roles

```html
<!-- Landmarks -->
<div role="banner">Header</div>
<div role="navigation">Nav</div>
<div role="main">Content</div>
<div role="complementary">Sidebar</div>
<div role="contentinfo">Footer</div>

<!-- Widgets -->
<div role="dialog" aria-modal="true" aria-labelledby="dialog-title">
  <h2 id="dialog-title">Confirm Delete</h2>
  ...
</div>

<div role="alert">Error message</div>
<div role="status">Loading...</div>
```

### ARIA Properties

```html
<!-- Labels -->
<button aria-label="Close">×</button>
<input aria-labelledby="label1 label2" />

<!-- Descriptions -->
<input aria-describedby="help-text error-message" />

<!-- States -->
<button aria-pressed="true">Toggle</button>
<button aria-expanded="false" aria-controls="menu">Menu</button>
<input aria-invalid="true" />
<div aria-busy="true">Loading...</div>
<option aria-selected="true">Option</option>
```

### Live Regions

```html
<!-- Polite: Announced after current speech -->
<div aria-live="polite" aria-atomic="true">
  Task saved successfully
</div>

<!-- Assertive: Interrupts immediately -->
<div aria-live="assertive" role="alert">
  Error: Connection lost
</div>

<!-- Status updates -->
<div role="status" aria-live="polite">
  3 items remaining
</div>
```

### Common ARIA Patterns

```html
<!-- Tabs -->
<div role="tablist" aria-label="Task filters">
  <button role="tab" aria-selected="true" aria-controls="all-panel">All</button>
  <button role="tab" aria-selected="false" aria-controls="active-panel">Active</button>
</div>
<div role="tabpanel" id="all-panel">All tasks</div>
<div role="tabpanel" id="active-panel" hidden>Active tasks</div>

<!-- Menu -->
<button aria-haspopup="true" aria-expanded="false" aria-controls="menu">
  Options
</button>
<ul role="menu" id="menu" hidden>
  <li role="menuitem"><button>Edit</button></li>
  <li role="menuitem"><button>Delete</button></li>
</ul>

<!-- Accordion -->
<button aria-expanded="true" aria-controls="content1">Section 1</button>
<div id="content1">Content</div>

<button aria-expanded="false" aria-controls="content2">Section 2</button>
<div id="content2" hidden>Content</div>
```

## Testing

### Automated Tools

1. **axe DevTools** - Browser extension
2. **WAVE** - Web accessibility evaluation
3. **Lighthouse** - Chrome audit
4. **eslint-plugin-jsx-a11y** - React linting

### Manual Testing Checklist

- [ ] Navigate with keyboard only (Tab, Enter, Escape, Arrows)
- [ ] Test with screen reader (NVDA, VoiceOver, JAWS)
- [ ] Zoom to 200% - is content still usable?
- [ ] Disable CSS - is content order logical?
- [ ] Check color contrast with dropper tool
- [ ] Verify focus indicators are visible
- [ ] Test form validation announcements
- [ ] Verify skip links work
- [ ] Check heading hierarchy

### Screen Reader Commands

| Action | NVDA | VoiceOver (Mac) |
|--------|------|-----------------|
| Start/Stop | Ctrl+Alt+N | Cmd+F5 |
| Next element | Down Arrow | Ctrl+Opt+Right |
| Headings list | H | Ctrl+Opt+Cmd+H |
| Links list | K | Ctrl+Opt+Cmd+L |
| Forms mode | Enter | Ctrl+Opt+Shift+Down |

## Common Patterns

### Accessible Button

```tsx
function Button({ children, onClick, disabled, loading }) {
  return (
    <button
      onClick={onClick}
      disabled={disabled || loading}
      aria-disabled={disabled || loading}
      aria-busy={loading}
    >
      {loading && <span className="sr-only">Loading</span>}
      {loading && <Spinner aria-hidden="true" />}
      {children}
    </button>
  );
}
```

### Accessible Form

```tsx
function TaskForm() {
  const [errors, setErrors] = useState({});

  return (
    <form aria-label="Add new task">
      <div>
        <label htmlFor="title">
          Title <span aria-hidden="true">*</span>
          <span className="sr-only">(required)</span>
        </label>
        <input
          id="title"
          type="text"
          required
          aria-required="true"
          aria-invalid={!!errors.title}
          aria-describedby={errors.title ? "title-error" : undefined}
        />
        {errors.title && (
          <p id="title-error" role="alert" className="text-red-600">
            {errors.title}
          </p>
        )}
      </div>

      <button type="submit">Add Task</button>
    </form>
  );
}
```

### Screen Reader Only Text

```css
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border-width: 0;
}

/* Make visible on focus (for skip links) */
.sr-only-focusable:focus {
  position: static;
  width: auto;
  height: auto;
  padding: inherit;
  margin: inherit;
  overflow: visible;
  clip: auto;
  white-space: normal;
}
```

```html
<!-- Tailwind -->
<span class="sr-only">Screen reader only text</span>
<a href="#main" class="sr-only focus:not-sr-only">Skip to content</a>
```
