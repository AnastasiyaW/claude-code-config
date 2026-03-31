# Верстка, CSS, Flexbox, Grid, Адаптив

## Современная единица измерения

```css
/* Предпочтения 2024 */
font-size: clamp(1rem, 2.5vw, 1.5rem);  /* fluid typography */
padding: clamp(1rem, 5vw, 3rem);         /* fluid spacing */
width: min(100%, 1280px);                /* smart max-width */
```

**Шкала отступов** — только степени двойки × 4:
`4 / 8 / 12 / 16 / 24 / 32 / 48 / 64 / 96 / 128px`

---

## Flexbox — ключевые паттерны

```css
/* Центрирование (самый частый кейс) */
.center { display: flex; align-items: center; justify-content: center; }

/* Навбар: лого слева, меню справа */
.navbar { display: flex; justify-content: space-between; align-items: center; }

/* Карточки с авто-переносом */
.cards {
  display: flex;
  flex-wrap: wrap;
  gap: 24px;
}
.card { flex: 1 1 280px; } /* min 280px, растягиваются равномерно */

/* Sidebar layout */
.layout { display: flex; gap: 32px; }
.sidebar { flex: 0 0 260px; }
.main { flex: 1; min-width: 0; } /* min-width: 0 — важно! */
```

### Частые ошибки Flexbox
- Забыть `min-width: 0` на flex-item с overflow → текст вылезает
- `flex: 1` без `min-width: 0` ломает длинные слова
- Использовать `margin: auto` для push (работает, но неочевидно)

---

## CSS Grid — ключевые паттерны

```css
/* Авто-адаптивная сетка (без медиазапросов!) */
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 24px;
}

/* 12-колоночная базовая сетка */
.grid-12 {
  display: grid;
  grid-template-columns: repeat(12, 1fr);
  gap: 16px;
}
.col-4 { grid-column: span 4; }

/* Holy Grail layout */
.page {
  display: grid;
  grid-template:
    "header header" auto
    "sidebar main" 1fr
    "footer footer" auto
    / 260px 1fr;
  min-height: 100vh;
}

/* Overlapping (карточка поверх изображения) */
.hero {
  display: grid;
  grid-template-areas: "stack";
}
.hero > * { grid-area: stack; }
```

---

## Container Queries (2023+, все браузеры)

```css
/* Контейнер должен быть помечен */
.card-wrapper {
  container-type: inline-size;
  container-name: card;
}

/* Компонент адаптируется к СВОЕМУ контейнеру */
@container card (min-width: 400px) {
  .card {
    display: grid;
    grid-template-columns: 2fr 1fr;
  }
}

@container card (min-width: 600px) {
  .card-title { font-size: 1.5rem; }
}
```

**Зачем лучше media queries:** компонент всегда корректно выглядит,
независимо от того, где он размещён на странице.

---

## Медиазапросы — современные брейкпоинты

```css
/* Mobile-first: начинаем с мобилки, расширяем */
/* sm */  @media (min-width: 640px)  { ... }
/* md */  @media (min-width: 768px)  { ... }
/* lg */  @media (min-width: 1024px) { ... }
/* xl */  @media (min-width: 1280px) { ... }
/* 2xl */ @media (min-width: 1536px) { ... }

/* Тёмная тема */
@media (prefers-color-scheme: dark) { ... }

/* Меньше анимаций (accessibility) */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}

/* Hover только на устройствах с мышью */
@media (hover: hover) {
  .btn:hover { background: var(--accent); }
}
```

---

## CSS Custom Properties (переменные)

```css
/* Дизайн-токены — основа системы */
:root {
  /* Цвета */
  --color-bg: #ffffff;
  --color-surface: #f8fafc;
  --color-border: #e2e8f0;
  --color-text: #0f172a;
  --color-text-muted: #64748b;
  --color-accent: #6366f1;
  --color-accent-hover: #4f46e5;

  /* Радиусы */
  --radius-sm: 6px;
  --radius-md: 10px;
  --radius-lg: 16px;
  --radius-xl: 24px;
  --radius-full: 9999px;

  /* Тени */
  --shadow-sm: 0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04);
  --shadow-md: 0 4px 16px rgba(0,0,0,0.08), 0 2px 4px rgba(0,0,0,0.04);
  --shadow-lg: 0 20px 40px rgba(0,0,0,0.12);

  /* Шрифты */
  --font-sans: 'Inter', system-ui, -apple-system, sans-serif;
  --font-mono: 'JetBrains Mono', 'Fira Code', monospace;

  /* Скорости анимаций */
  --transition-fast: 150ms cubic-bezier(0.4, 0, 0.2, 1);
  --transition-base: 200ms cubic-bezier(0.4, 0, 0.2, 1);
  --transition-slow: 300ms cubic-bezier(0.4, 0, 0.2, 1);
}

/* Тёмная тема через те же переменные */
[data-theme="dark"] {
  --color-bg: #0f172a;
  --color-surface: #1e293b;
  --color-border: rgba(255,255,255,0.08);
  --color-text: #f1f5f9;
  --color-text-muted: #94a3b8;
}
```

---

## Типографика

```css
/* Системный шрифтовой стек (без загрузки) */
font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;

/* Google Fonts с оптимизацией */
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">

/* Fluid type scale */
--text-xs:   clamp(0.75rem, 1.5vw, 0.875rem);
--text-sm:   clamp(0.875rem, 1.8vw, 1rem);
--text-base: clamp(1rem, 2vw, 1.125rem);
--text-lg:   clamp(1.125rem, 2.5vw, 1.25rem);
--text-xl:   clamp(1.25rem, 3vw, 1.5rem);
--text-2xl:  clamp(1.5rem, 4vw, 2rem);
--text-3xl:  clamp(2rem, 5vw, 3rem);
--text-4xl:  clamp(2.5rem, 7vw, 4rem);

/* Читаемость длинного текста */
.prose {
  max-width: 65ch;         /* оптимальная длина строки */
  line-height: 1.7;
  font-size: 1.0625rem;
}
```

---

## Сброс и базовые стили (современный reset)

```css
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html { -webkit-text-size-adjust: 100%; scroll-behavior: smooth; }
body { line-height: 1.5; -webkit-font-smoothing: antialiased; }
img, picture, video, canvas, svg { display: block; max-width: 100%; }
input, button, textarea, select { font: inherit; }
p, h1, h2, h3, h4, h5, h6 { overflow-wrap: break-word; }
#root, #__next { isolation: isolate; }
```

---

## Позиционирование и z-index система

```css
/* Z-index шкала — никогда не используй "999" */
:root {
  --z-base: 1;
  --z-dropdown: 100;
  --z-sticky: 200;
  --z-overlay: 300;
  --z-modal: 400;
  --z-toast: 500;
}

/* Sticky header */
.header {
  position: sticky;
  top: 0;
  z-index: var(--z-sticky);
  background: var(--color-bg);
  backdrop-filter: blur(12px);
}
```
