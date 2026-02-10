# Tailwind CSS Patterns

## Table of Contents
- [Setup](#setup)
- [Layout Patterns](#layout-patterns)
- [Component Patterns](#component-patterns)
- [Form Elements](#form-elements)
- [Feedback Components](#feedback-components)
- [Dark Mode](#dark-mode)
- [Responsive Design](#responsive-design)
- [Todo App Components](#todo-app-components)

## Setup

### Next.js 16 Installation

```bash
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

```javascript
// tailwind.config.js
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  darkMode: 'class',
  theme: {
    extend: {},
  },
  plugins: [],
}
```

```css
/* app/globals.css */
@tailwind base;
@tailwind components;
@tailwind utilities;
```

## Layout Patterns

### Container

```html
<!-- Centered container with max width -->
<div class="container mx-auto px-4 max-w-4xl">
  <!-- Content -->
</div>
```

### Flexbox Layouts

```html
<!-- Horizontal center -->
<div class="flex items-center justify-center">

<!-- Space between -->
<div class="flex items-center justify-between">

<!-- Vertical stack -->
<div class="flex flex-col gap-4">

<!-- Horizontal with wrap -->
<div class="flex flex-wrap gap-4">
```

### Grid Layouts

```html
<!-- Responsive grid -->
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
  <div>Item 1</div>
  <div>Item 2</div>
  <div>Item 3</div>
</div>

<!-- Sidebar layout -->
<div class="grid grid-cols-12 gap-4">
  <aside class="col-span-12 md:col-span-3">Sidebar</aside>
  <main class="col-span-12 md:col-span-9">Content</main>
</div>
```

### Page Layout

```html
<div class="min-h-screen flex flex-col">
  <header class="h-16 border-b bg-white">
    <!-- Nav -->
  </header>

  <main class="flex-1 container mx-auto px-4 py-8">
    <!-- Content -->
  </main>

  <footer class="h-16 border-t bg-gray-50">
    <!-- Footer -->
  </footer>
</div>
```

## Component Patterns

### Cards

```html
<!-- Basic card -->
<div class="bg-white rounded-lg shadow-md p-6">
  <h3 class="text-lg font-semibold text-gray-900">Title</h3>
  <p class="text-gray-600 mt-2">Description</p>
</div>

<!-- Interactive card -->
<div class="bg-white rounded-lg shadow-md p-6
            hover:shadow-lg transition-shadow
            cursor-pointer">
  <!-- Content -->
</div>

<!-- Card with header -->
<div class="bg-white rounded-lg shadow-md overflow-hidden">
  <div class="px-6 py-4 bg-gray-50 border-b">
    <h3 class="font-semibold">Header</h3>
  </div>
  <div class="p-6">
    <!-- Body -->
  </div>
</div>
```

### Buttons

```html
<!-- Primary -->
<button class="px-4 py-2 bg-blue-600 text-white rounded-md
               hover:bg-blue-700 focus:outline-none focus:ring-2
               focus:ring-blue-500 focus:ring-offset-2
               disabled:opacity-50 disabled:cursor-not-allowed
               transition-colors">
  Primary
</button>

<!-- Secondary -->
<button class="px-4 py-2 border border-gray-300 rounded-md
               hover:bg-gray-50 focus:outline-none focus:ring-2
               focus:ring-blue-500 focus:ring-offset-2
               transition-colors">
  Secondary
</button>

<!-- Danger -->
<button class="px-4 py-2 bg-red-600 text-white rounded-md
               hover:bg-red-700 focus:outline-none focus:ring-2
               focus:ring-red-500 focus:ring-offset-2
               transition-colors">
  Delete
</button>

<!-- Icon button -->
<button class="p-2 rounded-full hover:bg-gray-100
               focus:outline-none focus:ring-2 focus:ring-blue-500">
  <svg class="w-5 h-5" ...></svg>
</button>

<!-- Button sizes -->
<button class="px-3 py-1.5 text-sm ...">Small</button>
<button class="px-4 py-2 ...">Medium</button>
<button class="px-6 py-3 text-lg ...">Large</button>
```

### Badges

```html
<span class="px-2 py-1 text-xs font-medium rounded-full
             bg-green-100 text-green-800">
  Completed
</span>

<span class="px-2 py-1 text-xs font-medium rounded-full
             bg-yellow-100 text-yellow-800">
  Pending
</span>

<span class="px-2 py-1 text-xs font-medium rounded-full
             bg-red-100 text-red-800">
  Overdue
</span>
```

## Form Elements

### Text Input

```html
<div>
  <label for="title" class="block text-sm font-medium text-gray-700 mb-1">
    Task Title
  </label>
  <input
    type="text"
    id="title"
    class="w-full px-3 py-2 border border-gray-300 rounded-md
           focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500
           placeholder:text-gray-400"
    placeholder="Enter task title"
  />
</div>

<!-- With error -->
<div>
  <label class="block text-sm font-medium text-gray-700 mb-1">
    Task Title
  </label>
  <input
    type="text"
    class="w-full px-3 py-2 border border-red-500 rounded-md
           focus:outline-none focus:ring-2 focus:ring-red-500"
  />
  <p class="mt-1 text-sm text-red-600">Title is required</p>
</div>
```

### Textarea

```html
<textarea
  rows="4"
  class="w-full px-3 py-2 border border-gray-300 rounded-md
         focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500
         resize-none"
  placeholder="Enter description..."
></textarea>
```

### Checkbox

```html
<label class="flex items-center gap-2 cursor-pointer">
  <input
    type="checkbox"
    class="w-4 h-4 rounded border-gray-300
           text-blue-600 focus:ring-blue-500"
  />
  <span class="text-gray-700">Mark as complete</span>
</label>
```

### Select

```html
<select class="w-full px-3 py-2 border border-gray-300 rounded-md
               focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500">
  <option value="">Select priority</option>
  <option value="low">Low</option>
  <option value="medium">Medium</option>
  <option value="high">High</option>
</select>
```

## Feedback Components

### Alerts

```html
<!-- Success -->
<div class="p-4 rounded-md bg-green-50 border border-green-200">
  <div class="flex items-center gap-3">
    <svg class="w-5 h-5 text-green-600">...</svg>
    <p class="text-green-800">Task saved successfully!</p>
  </div>
</div>

<!-- Error -->
<div class="p-4 rounded-md bg-red-50 border border-red-200">
  <div class="flex items-center gap-3">
    <svg class="w-5 h-5 text-red-600">...</svg>
    <p class="text-red-800">Failed to save task.</p>
  </div>
</div>

<!-- Warning -->
<div class="p-4 rounded-md bg-yellow-50 border border-yellow-200">
  <div class="flex items-center gap-3">
    <svg class="w-5 h-5 text-yellow-600">...</svg>
    <p class="text-yellow-800">Task is overdue!</p>
  </div>
</div>
```

### Toast/Snackbar

```html
<div class="fixed bottom-4 right-4 z-50">
  <div class="bg-gray-900 text-white px-4 py-3 rounded-lg shadow-lg
              flex items-center gap-3">
    <span>Task deleted</span>
    <button class="text-blue-400 hover:text-blue-300 font-medium">
      Undo
    </button>
  </div>
</div>
```

### Loading States

```html
<!-- Spinner -->
<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>

<!-- Skeleton -->
<div class="animate-pulse space-y-4">
  <div class="h-4 bg-gray-200 rounded w-3/4"></div>
  <div class="h-4 bg-gray-200 rounded w-1/2"></div>
</div>

<!-- Button loading -->
<button class="px-4 py-2 bg-blue-600 text-white rounded-md flex items-center gap-2"
        disabled>
  <svg class="animate-spin h-4 w-4" ...></svg>
  Saving...
</button>
```

### Empty State

```html
<div class="text-center py-12">
  <svg class="mx-auto h-12 w-12 text-gray-400">...</svg>
  <h3 class="mt-4 text-lg font-medium text-gray-900">No tasks yet</h3>
  <p class="mt-2 text-gray-500">Get started by creating a new task.</p>
  <button class="mt-4 px-4 py-2 bg-blue-600 text-white rounded-md">
    Add Task
  </button>
</div>
```

## Dark Mode

### Configuration

```javascript
// tailwind.config.js
module.exports = {
  darkMode: 'class', // or 'media' for system preference
  // ...
}
```

### Dark Mode Classes

```html
<div class="bg-white dark:bg-gray-900">
  <h1 class="text-gray-900 dark:text-white">Title</h1>
  <p class="text-gray-600 dark:text-gray-400">Description</p>

  <div class="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
    <!-- Card content -->
  </div>
</div>
```

### Toggle Component

```tsx
function DarkModeToggle() {
  const [dark, setDark] = useState(false);

  useEffect(() => {
    document.documentElement.classList.toggle('dark', dark);
  }, [dark]);

  return (
    <button
      onClick={() => setDark(!dark)}
      className="p-2 rounded-lg bg-gray-100 dark:bg-gray-800"
    >
      {dark ? '☀️' : '🌙'}
    </button>
  );
}
```

## Responsive Design

### Breakpoints

```
sm:  640px   (mobile landscape)
md:  768px   (tablet)
lg:  1024px  (laptop)
xl:  1280px  (desktop)
2xl: 1536px  (large desktop)
```

### Responsive Patterns

```html
<!-- Hide/show -->
<div class="hidden md:block">Desktop only</div>
<div class="md:hidden">Mobile only</div>

<!-- Responsive flex -->
<div class="flex flex-col md:flex-row gap-4">
  <div class="w-full md:w-1/3">Sidebar</div>
  <div class="w-full md:w-2/3">Main</div>
</div>

<!-- Responsive text -->
<h1 class="text-2xl md:text-4xl lg:text-5xl font-bold">
  Heading
</h1>

<!-- Responsive padding -->
<div class="p-4 md:p-6 lg:p-8">
  Content
</div>
```

## Todo App Components

### Task List Item

```html
<div class="flex items-center gap-4 p-4 bg-white rounded-lg shadow-sm
            hover:shadow-md transition-shadow">
  <input
    type="checkbox"
    class="w-5 h-5 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
  />

  <div class="flex-1 min-w-0">
    <h3 class="font-medium text-gray-900 truncate">Buy groceries</h3>
    <p class="text-sm text-gray-500">Due tomorrow</p>
  </div>

  <span class="px-2 py-1 text-xs font-medium rounded-full bg-yellow-100 text-yellow-800">
    Pending
  </span>

  <button class="p-2 text-gray-400 hover:text-red-600 rounded-full hover:bg-gray-100">
    <svg class="w-5 h-5"><!-- trash icon --></svg>
  </button>
</div>
```

### Task Form

```html
<form class="space-y-4 bg-white p-6 rounded-lg shadow-md">
  <div>
    <label class="block text-sm font-medium text-gray-700 mb-1">
      Title
    </label>
    <input
      type="text"
      class="w-full px-3 py-2 border border-gray-300 rounded-md
             focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
      placeholder="What needs to be done?"
    />
  </div>

  <div>
    <label class="block text-sm font-medium text-gray-700 mb-1">
      Description
    </label>
    <textarea
      rows="3"
      class="w-full px-3 py-2 border border-gray-300 rounded-md
             focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
    ></textarea>
  </div>

  <div class="flex justify-end gap-3">
    <button type="button" class="px-4 py-2 border border-gray-300 rounded-md
                                  hover:bg-gray-50">
      Cancel
    </button>
    <button type="submit" class="px-4 py-2 bg-blue-600 text-white rounded-md
                                  hover:bg-blue-700">
      Add Task
    </button>
  </div>
</form>
```

### Dashboard Stats

```html
<div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
  <div class="bg-white p-6 rounded-lg shadow-sm">
    <p class="text-sm text-gray-500">Total Tasks</p>
    <p class="text-3xl font-bold text-gray-900">24</p>
  </div>

  <div class="bg-white p-6 rounded-lg shadow-sm">
    <p class="text-sm text-gray-500">Completed</p>
    <p class="text-3xl font-bold text-green-600">18</p>
  </div>

  <div class="bg-white p-6 rounded-lg shadow-sm">
    <p class="text-sm text-gray-500">Pending</p>
    <p class="text-3xl font-bold text-yellow-600">6</p>
  </div>
</div>
```
