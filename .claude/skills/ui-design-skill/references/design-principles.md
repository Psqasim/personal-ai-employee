# Design Principles

## User-Centered Design (UCD)

### The UCD Process

```
Research → Define → Ideate → Prototype → Test → Iterate
    ↑__________________________________________________|
```

### Key Principles

1. **Know Your Users**
   - Who are they? (demographics, tech-savviness)
   - What are their goals?
   - What are their pain points?
   - In what context do they use the product?

2. **Design for Mental Models**
   - Match user expectations
   - Use familiar patterns
   - Maintain consistency with similar tools

3. **Reduce Cognitive Load**
   - Show only what's needed
   - Group related items
   - Use progressive disclosure
   - Limit choices (5-7 items max)

## Gestalt Principles

### Proximity
Items close together are perceived as related.

```
Good:                    Bad:
[Label] [Input]         [Label]
[Label] [Input]                    [Input]
                        [Label]
                                   [Input]
```

### Similarity
Similar items are perceived as grouped.

```
[Primary Button]  [Primary Button]
[Secondary Btn]   [Secondary Btn]   [Danger Btn]
```

### Continuity
Eyes follow lines and curves naturally.

```
Step 1 ──→ Step 2 ──→ Step 3 ──→ Done
```

### Closure
Mind completes incomplete shapes.

```
Progress: [████████░░░░] 66%
```

### Figure-Ground
Distinguish foreground from background.

```
┌─────────────────────────┐
│  ┌─────────────────┐    │  Modal (figure)
│  │    Confirm?     │    │  on dimmed
│  │  [Yes]  [No]    │    │  background (ground)
│  └─────────────────┘    │
└─────────────────────────┘
```

## Feedback Design

### Types of Feedback

| Type | When | Example |
|------|------|---------|
| Immediate | During action | Button press animation |
| Progress | Long operations | Loading spinner, progress bar |
| Confirmation | After success | "Saved!" toast message |
| Error | On failure | Red border, error message |
| Validation | During input | Green checkmark for valid |

### Feedback Timing

```
Immediate:     < 100ms   (feels instant)
Acknowledged:  < 1s      (show spinner if longer)
Progress:      > 1s      (show progress indicator)
Background:    > 10s     (allow user to continue)
```

### Good Feedback Messages

```python
# Bad
"Error"
"Something went wrong"
"Invalid input"

# Good
"Could not save task. Check your internet connection."
"Email format invalid. Example: user@example.com"
"Password must be at least 8 characters"
```

## Information Architecture

### Content Hierarchy

```
Primary:    Core actions, main content
Secondary:  Supporting info, less common actions
Tertiary:   Metadata, advanced options
```

### Navigation Patterns

**Flat Navigation** (few sections)
```
[Home] [Tasks] [Settings]
```

**Hierarchical** (nested content)
```
Tasks/
├── Active/
│   ├── Today
│   └── This Week
└── Completed/
```

**Hub-and-Spoke** (central dashboard)
```
        [Task A]
           ↑
[Settings] ← [Dashboard] → [Task B]
           ↓
        [Reports]
```

## Interaction Design Patterns

### Affordances
Visual cues that suggest how to interact.

```
Button:     Raised, shadows → clickable
Link:       Underlined, colored → clickable
Input:      Border, placeholder → typeable
Slider:     Handle, track → draggable
```

### Signifiers
Explicit indicators of how to interact.

```
Hover tooltip:    "Click to edit"
Placeholder:      "Enter task name..."
Helper text:      "Press Enter to save"
Icon + label:     [+] Add Task
```

### State Communication

```
Default:     Normal appearance
Hover:       Subtle highlight
Focus:       Visible outline
Active:      Pressed/depressed
Disabled:    Grayed out, no cursor
Loading:     Spinner, skeleton
Error:       Red border/text
Success:     Green indicator
```

## Mobile-First Considerations

### Touch Targets
- Minimum: 44x44 pixels
- Recommended: 48x48 pixels
- Spacing: 8px between targets

### Thumb Zones
```
┌─────────────────┐
│   Hard to       │  ← Secondary actions
│   reach         │
├─────────────────┤
│   Natural       │  ← Primary content
│   reach         │
├─────────────────┤
│   Easy          │  ← Main navigation
│   reach         │
└─────────────────┘
```

### Mobile Patterns

| Pattern | Use Case |
|---------|----------|
| Bottom nav | Primary navigation |
| Floating action button | Main action |
| Pull to refresh | List updates |
| Swipe actions | Quick edits/delete |
| Bottom sheets | Contextual options |

## Error Prevention & Recovery

### Prevention Strategies

1. **Constraints** - Limit invalid options
   ```
   Date picker instead of free text
   Dropdown instead of open input
   ```

2. **Confirmation** - For destructive actions
   ```
   "Delete task? This cannot be undone."
   [Cancel] [Delete]
   ```

3. **Undo** - Allow reversal
   ```
   "Task deleted. [Undo]"
   ```

4. **Validation** - Catch errors early
   ```
   Real-time: Show error as user types
   On blur: Validate when leaving field
   On submit: Final validation
   ```

### Error Message Guidelines

```python
# Structure
"[What happened]. [Why]. [How to fix]."

# Examples
"Email not found. This address isn't registered. Try another or sign up."
"Password incorrect. Check caps lock. Forgot password?"
"Connection lost. Saving paused. Will retry automatically."
```

## Consistency Checklist

- [ ] Same action triggers same result everywhere
- [ ] Similar elements look and behave similarly
- [ ] Terminology is consistent throughout
- [ ] Icons have consistent meaning
- [ ] Spacing follows a system
- [ ] Colors have consistent meaning
- [ ] Feedback patterns are predictable
