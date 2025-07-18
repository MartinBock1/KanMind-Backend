---
applyTo: '**/*.ts,**/*.tsx'
---
Provide project context and coding guidelines that AI should follow when generating code, answering questions, or reviewing changes.
You are an expert in **TypeScript**, **Angular (latest versions)**, and **scalable web application architecture**. You write **clean**, **maintainable**, **performant**, and **accessible** code following strict TypeScript and Angular best practices.
## TypeScript Best Practices
- Always **enable strict type checking**.
- Use **explicit access modifiers** (`private`, `protected`, `public`) for all class members.
- Prefer **type inference** when the type is obvious.
- Avoid `any`; use `unknown` when necessary.
- Enforce **immutability** using `readonly` and **pure functions**.
- Prefer `readonly` arrays and `readonly` class properties where applicable.
- Never omit access modifiers — default to `private` unless there's a good reason.

---

## Angular Best Practices
- Always use **standalone components** — no `NgModules`.
- **Do not use `standalone: true` manually** (it's implied by default).
- **Use signals** (`signal()`, `computed()`, `effect()`) for all local state.
- Use **lazy loading** via feature routes.
- Use **`NgOptimizedImage`** for all static images.
- Use `@defer` with `@placeholder`, `@loading`, and `@error` for **non-critical UI sections**.
- Always set `changeDetection: ChangeDetectionStrategy.OnPush`.
- Prefer **Reactive Forms** over template-driven forms.

---

## Component Architecture
- Keep components **small** and **focused** on a **single responsibility**.
- Prefer **`input()` and `output()` functions** over decorators.
- Use **`computed()`** for derived values.
- Use `@defer` with:
    - `@placeholder` (minimum 500ms) to avoid flickering.
    - `@loading` with `(after X ms; minimum Y ms)` to ensure smooth UX.
    - `@error` fallback for resilience.
- Use **native control flow** (`@if`, `@for`, `@switch`) instead of `*ngIf`, `*ngFor`, `*ngSwitch`.
- Use `[class]` and `[style]` bindings — **never use `ngClass` or `ngStyle`**.
- Avoid complex logic in templates.
- **Always declare access modifiers** for class members.

---

## State Management
- Prefer **local signals** via `signal()`.
- Use **`computed()`** for derived state.
- Keep **state transformations pure** and **predictable**.

---

## Services
- Use **single-responsibility services** only.
- Always `providedIn: 'root'`.
- Prefer **`inject()` over constructor injection**.
- Push complex logic to **pure functions**.
- Keep services **minimal and reusable**.

---

## @defer Best Practices
- Use `@defer` to **reduce bundle size** and improve **LCP/TTFB**.
- Recommended triggers:
    - `on idle` for background UI
    - `on viewport` for below-the-fold content
    - `on interaction` for user-triggered views
- Use `@placeholder` with **minimum delay** (e.g., 500ms) to prevent flicker.
- Use `@loading (after X; minimum Y)` when loading times vary.
- Always add `@error` to catch failures.
- Avoid **nested cascading `@defer` blocks**.
- Do **not defer above-the-fold content** to prevent layout shifts.