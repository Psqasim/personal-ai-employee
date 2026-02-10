# Responsive Design

## Table of Contents
- [Mobile-First Approach](#mobile-first-approach)
- [Breakpoints](#breakpoints)
- [Layout Patterns](#layout-patterns)
- [Typography](#typography)
- [Images & Media](#images--media)
- [Navigation Patterns](#navigation-patterns)
- [Touch Considerations](#touch-considerations)
- [Testing](#testing)

## Mobile-First Approach

### Philosophy

Design for mobile first, then enhance for larger screens.

```css
/* Mobile-first CSS */
.container {
  padding: 1rem;        /* Mobile default */
}

@media (min-width: 768px) {
  .container {
    padding: 2rem;      /* Tablet+ */
  }
}

@media (min-width: 1024px) {
  .container {
    padding: 3rem;      /* Desktop */
  }
}
```

```html
<!-- Tailwind mobile-first -->
<div class="p-4 md:p-8 lg:p-12">
  <!-- Starts small, grows larger -->
</div>
```

### Benefits

1. **Performance** - Mobile devices get minimal CSS
2. **Focus** - Forces prioritization of essential content
3. **Progressive enhancement** - Adds features as space allows
4. **Future-proof** - New small devices work by default

## Breakpoints

### Standard Breakpoints

| Name | Width | Target Devices |
|------|-------|----------------|
| xs | < 480px | Small phones |
| sm | 480px | Phones (landscape) |
| md | 768px | Tablets |
| lg | 1024px | Laptops |
| xl | 1280px | Desktops |
| 2xl | 1536px | Large monitors |

### Tailwind Breakpoints

```html
<!-- Responsive classes -->
<div class="
  w-full          /* All screens */
  sm:w-1/2        /* 640px+ */
  md:w-1/3        /* 768px+ */
  lg:w-1/4        /* 1024px+ */
">
```

### CSS Media Queries

```css
/* Common breakpoints */
@media (min-width: 480px) { }   /* Phone landscape */
@media (min-width: 768px) { }   /* Tablet */
@media (min-width: 1024px) { }  /* Laptop */
@media (min-width: 1280px) { }  /* Desktop */

/* Orientation */
@media (orientation: portrait) { }
@media (orientation: landscape) { }

/* Reduced motion */
@media (prefers-reduced-motion: reduce) {
  * {
    animation: none !important;
    transition: none !important;
  }
}
```

## Layout Patterns

### Single Column (Mobile)

```html
<div class="max-w-md mx-auto px-4">
  <header>Logo</header>
  <nav>Menu</nav>
  <main>Content</main>
  <footer>Footer</footer>
</div>
```

### Two Column (Tablet+)

```html
<div class="flex flex-col md:flex-row">
  <aside class="w-full md:w-64 md:shrink-0">
    Sidebar
  </aside>
  <main class="flex-1">
    Main content
  </main>
</div>
```

### Holy Grail Layout

```html
<div class="min-h-screen flex flex-col">
  <header class="h-16">Header</header>

  <div class="flex-1 flex flex-col md:flex-row">
    <nav class="order-2 md:order-1 md:w-48">Nav</nav>
    <main class="order-1 md:order-2 flex-1">Main</main>
    <aside class="order-3 md:w-48">Sidebar</aside>
  </div>

  <footer class="h-16">Footer</footer>
</div>
```

### Card Grid

```html
<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
  <!-- Cards automatically reflow -->
  <div class="bg-white p-4 rounded-lg shadow">Card 1</div>
  <div class="bg-white p-4 rounded-lg shadow">Card 2</div>
  <div class="bg-white p-4 rounded-lg shadow">Card 3</div>
  <div class="bg-white p-4 rounded-lg shadow">Card 4</div>
</div>
```

### Container Queries (Modern)

```css
/* Container query */
.card-container {
  container-type: inline-size;
}

@container (min-width: 400px) {
  .card {
    display: flex;
  }
}
```

```html
<div class="@container">
  <div class="block @md:flex">
    <!-- Responds to container, not viewport -->
  </div>
</div>
```

## Typography

### Responsive Font Sizes

```html
<!-- Tailwind responsive text -->
<h1 class="text-2xl sm:text-3xl md:text-4xl lg:text-5xl">
  Heading
</h1>

<p class="text-sm md:text-base lg:text-lg">
  Body text
</p>
```

### Fluid Typography

```css
/* Clamp for fluid sizing */
h1 {
  font-size: clamp(1.5rem, 4vw, 3rem);
}

p {
  font-size: clamp(1rem, 2vw, 1.25rem);
}
```

### Line Length

```html
<!-- Optimal reading width: 45-75 characters -->
<p class="max-w-prose">
  Long form content should be constrained for readability.
</p>

<!-- Or explicit width -->
<article class="max-w-2xl mx-auto">
  Content
</article>
```

## Images & Media

### Responsive Images

```html
<!-- HTML srcset -->
<img
  src="image-800.jpg"
  srcset="
    image-400.jpg 400w,
    image-800.jpg 800w,
    image-1200.jpg 1200w
  "
  sizes="
    (max-width: 600px) 100vw,
    (max-width: 1200px) 50vw,
    33vw
  "
  alt="Description"
/>

<!-- Tailwind responsive -->
<img
  src="image.jpg"
  class="w-full h-48 sm:h-64 md:h-80 object-cover"
  alt="Description"
/>
```

### Aspect Ratio

```html
<!-- Fixed aspect ratio -->
<div class="aspect-video">
  <iframe src="..." class="w-full h-full"></iframe>
</div>

<div class="aspect-square">
  <img src="..." class="w-full h-full object-cover" />
</div>
```

### Background Images

```html
<div class="
  bg-cover bg-center
  h-48 sm:h-64 md:h-80
  bg-[url('/hero-mobile.jpg')]
  sm:bg-[url('/hero-tablet.jpg')]
  lg:bg-[url('/hero-desktop.jpg')]
">
</div>
```

## Navigation Patterns

### Hamburger Menu (Mobile)

```html
<nav>
  <!-- Mobile menu button -->
  <button class="md:hidden p-2">
    <svg class="w-6 h-6"><!-- hamburger icon --></svg>
  </button>

  <!-- Desktop nav -->
  <ul class="hidden md:flex gap-6">
    <li><a href="/">Home</a></li>
    <li><a href="/tasks">Tasks</a></li>
    <li><a href="/settings">Settings</a></li>
  </ul>

  <!-- Mobile nav (shown when open) -->
  <div class="md:hidden absolute inset-x-0 top-16 bg-white shadow-lg">
    <ul class="flex flex-col p-4">
      <li><a href="/" class="block py-2">Home</a></li>
      <li><a href="/tasks" class="block py-2">Tasks</a></li>
      <li><a href="/settings" class="block py-2">Settings</a></li>
    </ul>
  </div>
</nav>
```

### Bottom Navigation (Mobile)

```html
<nav class="fixed bottom-0 inset-x-0 bg-white border-t md:hidden">
  <ul class="flex justify-around py-2">
    <li>
      <a href="/" class="flex flex-col items-center p-2">
        <svg class="w-6 h-6"><!-- icon --></svg>
        <span class="text-xs">Home</span>
      </a>
    </li>
    <li>
      <a href="/tasks" class="flex flex-col items-center p-2">
        <svg class="w-6 h-6"><!-- icon --></svg>
        <span class="text-xs">Tasks</span>
      </a>
    </li>
    <li>
      <a href="/settings" class="flex flex-col items-center p-2">
        <svg class="w-6 h-6"><!-- icon --></svg>
        <span class="text-xs">Settings</span>
      </a>
    </li>
  </ul>
</nav>
```

### Tab Bar

```html
<div class="border-b">
  <nav class="flex overflow-x-auto">
    <a href="#" class="px-4 py-2 border-b-2 border-blue-600 text-blue-600 whitespace-nowrap">
      Active Tab
    </a>
    <a href="#" class="px-4 py-2 text-gray-500 hover:text-gray-700 whitespace-nowrap">
      Tab 2
    </a>
    <a href="#" class="px-4 py-2 text-gray-500 hover:text-gray-700 whitespace-nowrap">
      Tab 3
    </a>
  </nav>
</div>
```

## Touch Considerations

### Touch Targets

```css
/* Minimum 44x44px touch targets */
.touch-target {
  min-width: 44px;
  min-height: 44px;
  padding: 12px;
}

/* Tailwind */
.btn {
  @apply min-w-[44px] min-h-[44px] p-3;
}
```

```html
<button class="p-3 min-w-[44px] min-h-[44px]">
  <svg class="w-6 h-6"><!-- icon --></svg>
</button>
```

### Spacing Between Targets

```html
<!-- Good: adequate spacing -->
<div class="flex gap-3">
  <button class="p-3">Action 1</button>
  <button class="p-3">Action 2</button>
</div>

<!-- Bad: too close together -->
<div class="flex gap-1">
  <button class="p-1">Action 1</button>
  <button class="p-1">Action 2</button>
</div>
```

### Hover States for Touch

```html
<!-- Works for both hover and touch -->
<button class="
  bg-blue-600
  hover:bg-blue-700
  active:bg-blue-800
  focus:ring-2 focus:ring-blue-500
">
  Button
</button>
```

## Testing

### Device Testing Checklist

- [ ] iPhone SE (375px)
- [ ] iPhone 14 (390px)
- [ ] iPad Mini (768px)
- [ ] iPad Pro (1024px)
- [ ] Laptop (1280px)
- [ ] Desktop (1536px+)

### Browser DevTools

```javascript
// Chrome DevTools device emulation
// Ctrl+Shift+M (Cmd+Shift+M on Mac)

// Test specific dimensions:
// - iPhone 12: 390 x 844
// - iPad: 768 x 1024
// - Desktop: 1920 x 1080
```

### Responsive Testing Tools

1. **Chrome DevTools** - Device toolbar
2. **Firefox Responsive Design Mode** - Ctrl+Shift+M
3. **Responsively App** - Multiple viewports
4. **BrowserStack** - Real device testing

### Common Issues to Check

1. **Horizontal overflow** - No horizontal scroll
2. **Touch target size** - Minimum 44x44px
3. **Text legibility** - Readable without zooming
4. **Image scaling** - No stretched/pixelated images
5. **Navigation access** - Menu reachable on all sizes
6. **Form usability** - Inputs keyboard accessible
7. **Load performance** - Acceptable on slow connections
