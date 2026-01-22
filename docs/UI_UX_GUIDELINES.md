# UI/UX & Design Language

## 1. Educational Psychology Foundation
Design based on research from Nielsen Norman Group, cognitive psychology, and learning science:
- **Chunking (Miller's Law)**: 7±2 steps maximum for optimal working memory
- **Cognitive Load Theory**: Minimize extraneous load with clean design
- **Progressive Disclosure**: One step at a time reveals information gradually
- **Visual Hierarchy**: Typography scale guides attention from most to least important
- **Feedback Loops**: Immediate progress indication on every action

## 2. Design Tokens

### Colors (Research-Based)
- **Primary Blue**: #3b82f6 (promotes focus, calmness, trust)
- **Background**: #f8fafc (soft white reduces eye strain vs pure white)
- **Text**: #334155 (dark slate - WCAG AAA contrast)
- **Borders**: #e2e8f0 (subtle separation without harshness)

### Math Component Colors (Wolfram Alpha-Inspired)
- **Numbers**: #1e40af (blue 800 - primary focus)
- **Exponents**: #dc2626 (red 600 - visual distinction)
- **Operators**: #059669 (green 600 - action indicators)
- **Parentheses**: #7c3aed (purple 600 - grouping)
- **Variables**: #be123c (rose 700 italic - unknowns)
- **Display Boxes**: Linear gradient (#dbeafe → #eff6ff) with border and shadow

### Typography Scale
- **Step Title**: 1.4em (mobile) / 1.5em (desktop) - clear hierarchy
- **Body Text**: 1em / 1.125em (18px) - optimal reading size
- **Line Height**: 1.75 - proven optimal for comprehension
- **Max Line Width**: 65 characters - ideal for reading speed and comprehension
- **Font Family**: -apple-system, BlinkMacSystemFont, 'Segoe UI' (native system fonts)

### Spacing System
- **Desktop**:
  - Container padding: 40px
  - Step cards margin: 20px
  - Content padding: 32px
  - Section gaps: 24px
- **Mobile** (@media max-width: 768px):
  - Container padding: 16px
  - Step cards margin: 12px
  - Content padding: 20px
  - Section gaps: 16px

## 3. Component States

### Upload Section
- **Empty State**: Drag-and-drop area with cloud upload icon
- **Hover State**: Light blue background (#eff6ff)
- **Active State**: Preview image with "Start Learning" button
- **Loading State**: "Analyzing your homework..." with spinning icon

### Step Navigation
- **Previous Button**: Disabled on first step (opacity 0.5)
- **Continue Button**: Blue primary (#3b82f6), changes to "Finish 🎉" on last step
- **Progress Bar**: Animated width transition, blue gradient fill

### Step Cards
- **Inactive**: `display: none` (only active step visible)
- **Active**: `display: block` with slide-up animation (0.3s ease-out)
- **Step Number**: Blue circular badge (48px)
- **Content**: Generous padding, formatted text with lists and paragraphs

### Math Rendering
- **Inline Math**: Flows with text, color-coded components
- **Display Math**: Centered, large text (1.4em), gradient box background
- **Transitions**: Smooth reveal on step activation

## 4. Interaction Patterns

### Progressive Learning Flow
1. Upload image → Preview
2. Click "Start Learning" → Loading state (manages expectations)
3. Display Problem card → Context setting
4. Show Step 1 → Progressive reveal
5. Click "Continue" → Smooth transition to Step 2
6. Repeat → Navigate through all steps
7. Finish → Completion badge with "Try Another Problem"
8. Reset → Return to upload state

### Animations & Transitions
- **Step Transitions**: slideInUp (translateY: 15px → 0, opacity: 0 → 1)
- **Progress Bar**: Smooth width animation (0.3s ease)
- **Button Hovers**: Subtle transform scale(1.02) and shadow increase
- **Loading**: Spinning animation (2s infinite linear)

## 5. Accessibility

### Keyboard Navigation
- Tab through upload, Previous, Continue buttons
- Enter/Space to activate buttons
- Focus visible with outline

### Screen Readers
- Semantic HTML (`<button>`, `<div>` with roles)
- Progress bar with aria-label
- Step numbers for orientation

### Visual Clarity
- High contrast text (WCAG AA minimum)
- Clear visual hierarchy
- Generous touch targets (44px minimum on mobile)
- No reliance on color alone (text labels + icons)

## 6. Mobile Optimizations

### Layout
- Single column flow
- Full-width cards
- Larger touch targets
- Reduced padding to maximize content space

### Typography
- Slightly smaller fonts to fit more content
- Maintained line-height ratio for readability
- Preserved hierarchy with relative sizing

### Interactions
- No hover effects (touch-only)
- Larger tap areas for navigation buttons
- Simplified animations (performance)

## 7. Performance Considerations

### KaTeX Rendering
- Render only active step (not all steps at once)
- Re-render on step change (ensures consistency)
- `throwOnError: false` (graceful degradation)

### Image Handling
- Client-side preview (no server upload until analysis)
- Base64 encoding for API transmission
- No persistent storage (privacy + performance)

### CSS
- Embedded in HTML (no external requests)
- Critical CSS inline
- Minimal animations (GPU-accelerated only)