# Design Systems

## Table of Contents
- [What is a Design System](#what-is-a-design-system)
- [Design Tokens](#design-tokens)
- [Component Library](#component-library)
- [Documentation](#documentation)
- [Implementation](#implementation)
- [Maintenance](#maintenance)

## What is a Design System

### Components of a Design System

```
Design System
├── Design Tokens (colors, spacing, typography)
├── Component Library (buttons, inputs, cards)
├── Patterns (forms, navigation, layouts)
├── Guidelines (accessibility, content, tone)
└── Documentation (usage, examples, dos/don'ts)
```

### Benefits

1. **Consistency** - Same look and feel everywhere
2. **Efficiency** - Reuse instead of recreate
3. **Scalability** - Grow without chaos
4. **Quality** - Built-in best practices
5. **Collaboration** - Shared language between teams

## Design Tokens

### Color Tokens

```javascript
// tokens/colors.js
export const colors = {
  // Brand
  primary: {
    50: '#eff6ff',
    100: '#dbeafe',
    500: '#3b82f6',  // Main
    600: '#2563eb',  // Hover
    700: '#1d4ed8',  // Active
    900: '#1e3a8a',
  },

  // Semantic
  success: {
    light: '#dcfce7',
    DEFAULT: '#22c55e',
    dark: '#166534',
  },
  warning: {
    light: '#fef3c7',
    DEFAULT: '#f59e0b',
    dark: '#92400e',
  },
  error: {
    light: '#fee2e2',
    DEFAULT: '#ef4444',
    dark: '#991b1b',
  },

  // Neutral
  gray: {
    50: '#f9fafb',
    100: '#f3f4f6',
    200: '#e5e7eb',
    300: '#d1d5db',
    400: '#9ca3af',
    500: '#6b7280',
    600: '#4b5563',
    700: '#374151',
    800: '#1f2937',
    900: '#111827',
  },
};
```

### Typography Tokens

```javascript
// tokens/typography.js
export const typography = {
  fontFamily: {
    sans: ['Inter', 'system-ui', 'sans-serif'],
    mono: ['JetBrains Mono', 'monospace'],
  },

  fontSize: {
    xs: ['0.75rem', { lineHeight: '1rem' }],
    sm: ['0.875rem', { lineHeight: '1.25rem' }],
    base: ['1rem', { lineHeight: '1.5rem' }],
    lg: ['1.125rem', { lineHeight: '1.75rem' }],
    xl: ['1.25rem', { lineHeight: '1.75rem' }],
    '2xl': ['1.5rem', { lineHeight: '2rem' }],
    '3xl': ['1.875rem', { lineHeight: '2.25rem' }],
    '4xl': ['2.25rem', { lineHeight: '2.5rem' }],
  },

  fontWeight: {
    normal: '400',
    medium: '500',
    semibold: '600',
    bold: '700',
  },
};
```

### Spacing Tokens

```javascript
// tokens/spacing.js
export const spacing = {
  0: '0',
  1: '0.25rem',   // 4px
  2: '0.5rem',    // 8px
  3: '0.75rem',   // 12px
  4: '1rem',      // 16px
  5: '1.25rem',   // 20px
  6: '1.5rem',    // 24px
  8: '2rem',      // 32px
  10: '2.5rem',   // 40px
  12: '3rem',     // 48px
  16: '4rem',     // 64px
};
```

### Shadow Tokens

```javascript
// tokens/shadows.js
export const shadows = {
  sm: '0 1px 2px 0 rgb(0 0 0 / 0.05)',
  DEFAULT: '0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)',
  md: '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
  lg: '0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)',
  xl: '0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)',
};
```

### Tailwind Config Integration

```javascript
// tailwind.config.js
const { colors, typography, spacing, shadows } = require('./tokens');

module.exports = {
  theme: {
    colors,
    fontFamily: typography.fontFamily,
    fontSize: typography.fontSize,
    fontWeight: typography.fontWeight,
    spacing,
    boxShadow: shadows,
    extend: {},
  },
};
```

## Component Library

### Component Structure

```
components/
├── primitives/          # Base elements
│   ├── Button/
│   ├── Input/
│   └── Text/
├── composites/          # Combined primitives
│   ├── Form/
│   ├── Card/
│   └── Modal/
└── patterns/            # Complex layouts
    ├── TaskList/
    ├── Navigation/
    └── Dashboard/
```

### Component Anatomy

```tsx
// components/Button/Button.tsx
import { cva, type VariantProps } from 'class-variance-authority';

const buttonVariants = cva(
  // Base styles
  'inline-flex items-center justify-center rounded-md font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none',
  {
    variants: {
      variant: {
        primary: 'bg-primary-600 text-white hover:bg-primary-700 focus:ring-primary-500',
        secondary: 'border border-gray-300 bg-white hover:bg-gray-50 focus:ring-primary-500',
        danger: 'bg-error text-white hover:bg-error-dark focus:ring-error',
        ghost: 'hover:bg-gray-100 focus:ring-gray-500',
      },
      size: {
        sm: 'h-8 px-3 text-sm',
        md: 'h-10 px-4',
        lg: 'h-12 px-6 text-lg',
      },
    },
    defaultVariants: {
      variant: 'primary',
      size: 'md',
    },
  }
);

interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  loading?: boolean;
}

export function Button({
  className,
  variant,
  size,
  loading,
  children,
  disabled,
  ...props
}: ButtonProps) {
  return (
    <button
      className={buttonVariants({ variant, size, className })}
      disabled={disabled || loading}
      {...props}
    >
      {loading && <Spinner className="mr-2 h-4 w-4" />}
      {children}
    </button>
  );
}
```

### Input Component

```tsx
// components/Input/Input.tsx
import { forwardRef } from 'react';
import { cn } from '@/lib/utils';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, label, error, helperText, id, ...props }, ref) => {
    const inputId = id || label?.toLowerCase().replace(/\s/g, '-');

    return (
      <div className="space-y-1">
        {label && (
          <label
            htmlFor={inputId}
            className="block text-sm font-medium text-gray-700"
          >
            {label}
          </label>
        )}

        <input
          id={inputId}
          ref={ref}
          className={cn(
            'block w-full rounded-md border px-3 py-2 shadow-sm',
            'focus:outline-none focus:ring-2 focus:ring-offset-0',
            error
              ? 'border-error focus:border-error focus:ring-error'
              : 'border-gray-300 focus:border-primary-500 focus:ring-primary-500',
            className
          )}
          aria-invalid={!!error}
          aria-describedby={
            error ? `${inputId}-error` : helperText ? `${inputId}-help` : undefined
          }
          {...props}
        />

        {error && (
          <p id={`${inputId}-error`} className="text-sm text-error">
            {error}
          </p>
        )}

        {helperText && !error && (
          <p id={`${inputId}-help`} className="text-sm text-gray-500">
            {helperText}
          </p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';
```

### Card Component

```tsx
// components/Card/Card.tsx
import { cn } from '@/lib/utils';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  padding?: 'none' | 'sm' | 'md' | 'lg';
}

export function Card({ children, className, padding = 'md' }: CardProps) {
  const paddingClasses = {
    none: '',
    sm: 'p-4',
    md: 'p-6',
    lg: 'p-8',
  };

  return (
    <div
      className={cn(
        'bg-white rounded-lg shadow-md',
        paddingClasses[padding],
        className
      )}
    >
      {children}
    </div>
  );
}

export function CardHeader({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={cn('border-b pb-4 mb-4', className)}>
      {children}
    </div>
  );
}

export function CardTitle({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <h3 className={cn('text-lg font-semibold text-gray-900', className)}>
      {children}
    </h3>
  );
}

export function CardContent({ children, className }: { children: React.ReactNode; className?: string }) {
  return <div className={className}>{children}</div>;
}

export function CardFooter({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={cn('border-t pt-4 mt-4 flex justify-end gap-3', className)}>
      {children}
    </div>
  );
}
```

## Documentation

### Component Documentation Template

```markdown
# Button

Buttons trigger actions or navigation.

## Usage

\`\`\`tsx
import { Button } from '@/components/Button';

<Button variant="primary" size="md">
  Click me
</Button>
\`\`\`

## Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| variant | 'primary' \| 'secondary' \| 'danger' \| 'ghost' | 'primary' | Visual style |
| size | 'sm' \| 'md' \| 'lg' | 'md' | Button size |
| loading | boolean | false | Show loading spinner |
| disabled | boolean | false | Disable interactions |

## Variants

### Primary
Use for main actions.

### Secondary
Use for secondary actions.

### Danger
Use for destructive actions.

## Accessibility

- Uses native `<button>` element
- Supports keyboard navigation
- `aria-disabled` set when loading
- Focus ring visible on keyboard focus

## Do's and Don'ts

✅ Do:
- Use clear, action-oriented labels
- Use primary for one main action per screen
- Provide loading state for async actions

❌ Don't:
- Use more than one primary button per section
- Use vague labels like "Click here"
- Disable without explanation
```

### Token Documentation

```markdown
# Colors

## Brand Colors

| Token | Value | Usage |
|-------|-------|-------|
| primary-500 | #3b82f6 | Main brand color |
| primary-600 | #2563eb | Hover state |
| primary-700 | #1d4ed8 | Active state |

## Semantic Colors

| Token | Value | Usage |
|-------|-------|-------|
| success | #22c55e | Success states |
| warning | #f59e0b | Warning states |
| error | #ef4444 | Error states |

## Gray Scale

Used for text, backgrounds, and borders.
```

## Implementation

### Utility Function

```typescript
// lib/utils.ts
import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
```

### Component Export Index

```typescript
// components/index.ts
export { Button } from './Button';
export { Input } from './Input';
export { Card, CardHeader, CardTitle, CardContent, CardFooter } from './Card';
export { Modal } from './Modal';
export { Badge } from './Badge';
// ... etc
```

### Theme Provider (for Dark Mode)

```tsx
// providers/ThemeProvider.tsx
'use client';

import { createContext, useContext, useEffect, useState } from 'react';

type Theme = 'light' | 'dark' | 'system';

const ThemeContext = createContext<{
  theme: Theme;
  setTheme: (theme: Theme) => void;
}>({
  theme: 'system',
  setTheme: () => {},
});

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setTheme] = useState<Theme>('system');

  useEffect(() => {
    const root = document.documentElement;
    const systemDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

    if (theme === 'dark' || (theme === 'system' && systemDark)) {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }
  }, [theme]);

  return (
    <ThemeContext.Provider value={{ theme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export const useTheme = () => useContext(ThemeContext);
```

## Maintenance

### Version Control

```
CHANGELOG.md

## [1.2.0] - 2025-01-15

### Added
- New `Badge` component
- Dark mode support for all components

### Changed
- Updated primary color palette
- Improved focus styles for accessibility

### Fixed
- Button loading state now properly disables
```

### Breaking Changes Protocol

1. Deprecation warning in current version
2. Migration guide in documentation
3. Removal in next major version

```tsx
// Example deprecation
/**
 * @deprecated Use `variant="danger"` instead. Will be removed in v2.0.
 */
export function DangerButton(props) {
  console.warn('DangerButton is deprecated. Use Button variant="danger"');
  return <Button variant="danger" {...props} />;
}
```

### Design System Checklist

- [ ] All tokens defined and documented
- [ ] Components follow consistent API patterns
- [ ] Accessibility tested (keyboard, screen reader)
- [ ] Responsive behavior verified
- [ ] Dark mode supported
- [ ] Documentation complete with examples
- [ ] Storybook/showcase available
- [ ] Changelog maintained
