# Design Specification: Professional Trading Interface
**Project Focus:** Minimalist, High-Performance, Elegant UX
**Reference Aesthetic:** RabbitX (Modern High-Density Trading)

---

## 1. Design Philosophy
The UI should feel like a high-end financial instrument: **functional, precise, and unobtrusive.** It prioritizes data clarity while using motion to provide "premium" tactile feedback.

* **Clarity over Decoration:** Use whitespace and subtle borders instead of heavy backgrounds to separate sections.
* **Contextual Density:** High information density for desktop (pro-tools), transitioning to a focused, hierarchical layout for mobile.
* **Consistency:** Every component (Buttons, Inputs, Modals) must follow the same corner radius and border-weight logic.

---

## 2. Visual Foundation

### Color Architecture (Tailwind Semantic Tokens)
The app utilizes a dual-theme system. Do not use hardcoded hex values; use the following CSS variables mapped in `tailwind.config.js`.

| Token | Dark Mode (Default) | Light Mode |
| :--- | :--- | :--- |
| `--background` | `#0B0E11` (Deep Matte) | `#F6F7F9` (Soft Gray) |
| `--surface` | `#15191E` (Elevated) | `#FFFFFF` (Pure White) |
| `--primary` | `#9D7BFF` (Electric Purple) | `#7C3AED` (Deep Violet) |
| `--accent` | `#2B3139` (Subtle Borders) | `#E2E8F0` (Light Borders) |
| `--success` | `#22C55E` | `#16A34A` |
| `--danger` | `#EF4444` | `#DC2626` |

### Typography & Geometry
* **Font Stack:** `Inter` or `Geist Sans` for UI. `JetBrains Mono` for all price data, balances, and numbers to ensure tabular alignment.
* **Radius:** * `Container`: `12px` (xl)
    * `Components`: `8px` (lg)
    * `Inputs/Tags`: `6px` (md)

---

## 3. Motion & Interaction (Framer Motion)
Animations must be "dampened" to feel professional—avoid bouncy or cartoonish easing.

### Micro-Interactions
* **State Changes:** Use `whileTap={{ scale: 0.97 }}` and `whileHover={{ opacity: 0.9 }}` for all interactive elements.
* **Live Data Tickers:** When values change, use a vertical slide-and-fade transition. 
    * *Up:* New value slides in from bottom to top.
    * *Down:* New value slides in from top to bottom.
* **Focus States:** Inputs should have a subtle outer glow transition using `box-shadow` on focus.

### Layout Transitions
* **Staggered Entrance:** On page load, child widgets should fade in and move up by `10px` with a stagger delay of `0.05s`.
* **Smooth Resizing:** Use the `layout` prop on `motion.div` for containers that change size (e.g., expanding the order book or switching tabs) to ensure fluid transitions.

---

## 4. Component Guidelines (Shadcn UI Integration)

### Dashboard Layout (Responsive)
* **Desktop:** 12-column grid system.
    * *Left/Center (8 cols):* Charting area and Trade History.
    * *Right (4 cols):* Order Entry and Portfolio Summary.
* **Mobile:** * Charts prioritized at the top.
    * Order Entry moved to a **Fixed Bottom Sheet** or a dedicated "Trade" tab.
    * Lists (Positions/Orders) converted to expandable cards.

### Widgets (Cards)
* Remove default Shadcn shadows. 
* Use a `1px` solid border (`--accent`).
* In Dark Mode, use a very subtle linear gradient (top to bottom) from `#1C2127` to `#15191E`.

---

## 5. Implementation Instructions for AI Agent
1.  **Theming:** Implement `next-themes` for seamless Dark/Light switching.
2.  **Number Formatting:** Create a utility to handle `toLocaleString` with fixed decimals based on asset precision.
3.  **Optimization:** Use `memo` for high-frequency components (Price Tickers) to prevent unnecessary re-renders during market volatility.
4.  **Charts:** Style any charting library (e.g., Lightweight Charts) to use the CSS variable `--background` for the pane and `--accent` for grid lines.