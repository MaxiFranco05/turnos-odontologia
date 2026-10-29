---
name: vercel-react-best-practices
description: Production-grade React engineering guidelines based on Vercel best practices, modern hooks, composition patterns, performance optimization, and strict TypeScript patterns.
---

# Vercel React Best Practices

Guidelines for building high-performance, maintainable, and type-safe React applications.

## 1. Component Architecture & Composition
- **Single Responsibility Principle**: Each component should solve exactly one UI concern.
- **Compound Components**: Prefer compound component patterns (e.g., `Dialog`, `DialogTrigger`, `DialogContent`) over giant prop-heavy components.
- **Children as Props**: Use composition (`children`) to eliminate prop drilling and prevent unnecessary re-renders of nested trees.
- **Strict TypeScript Contracts**:
  - Explicit prop types with `interface ComponentProps { ... }`.
  - Never use `any`. Use generics or discriminated unions for variable state.
  - Export component types for reuse.

## 2. State & Data Fetching
- **Server State vs Client State**:
  - Do NOT use `useEffect` for data fetching.
  - Use TanStack Query (`@tanstack/react-query`) or dedicated query hooks for caching, deduplication, retry, and background revalidation.
  - Keep client state local where possible; lift state only as far as necessary.
- **Form State**:
  - Prefer uncontrolled forms with React Hook Form or Zod validation for performance and zero re-renders per keystroke.
  - Validate at form submission and on blur for seamless user experience.

## 3. Rendering & Performance Optimization
- **Stable References**:
  - Avoid object or array literals created inline inside JSX when passed to memoized children.
  - Use `useCallback` and `useMemo` strictly when dependencies trigger expensive computations or re-render heavy subtrees.
- **Code Splitting & Lazy Loading**:
  - Lazy load heavy route-level components and isolated modal dialogues (`React.lazy` + `Suspense`).
  - Keep initial bundle minimal.
- **Avoid Layout Shifts (CLS)**:
  - Reserve space for dynamic content, images, and asynchronous data with skeleton placeholders (`Skeleton`).

## 4. Accessibility (A11Y) & Polish
- Ensure all interactive elements have accessible names (`aria-label`, visible text, or `aria-labelledby`).
- Support keyboard navigation (`Tab`, `Enter`, `Escape`, arrow keys).
- Respect user motion preferences (`prefers-reduced-motion`).
