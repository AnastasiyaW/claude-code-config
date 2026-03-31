# Компоненты, Фреймворки, React/Vue/Tailwind

## Компонентная библиотека (готовые паттерны)

### Кнопки
```html
<!-- Базовые варианты -->
<button class="btn btn-primary">Primary</button>
<button class="btn btn-secondary">Secondary</button>
<button class="btn btn-ghost">Ghost</button>
<button class="btn btn-danger">Danger</button>
```

```css
.btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  font-size: 0.9375rem;
  font-weight: 500;
  border-radius: var(--radius-md);
  border: none;
  cursor: pointer;
  transition: all var(--transition-base);
  white-space: nowrap;
  user-select: none;
}
.btn:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}
.btn:active { transform: scale(0.98); }

.btn-primary {
  background: var(--accent);
  color: white;
  box-shadow: 0 1px 3px rgba(0,0,0,.1);
}
.btn-primary:hover {
  background: var(--accent-hover);
  box-shadow: 0 4px 12px rgba(99,102,241,.35);
  transform: translateY(-1px);
}

.btn-secondary {
  background: var(--surface);
  color: var(--text);
  border: 1px solid var(--border);
}
.btn-secondary:hover {
  background: var(--surface-2);
  border-color: var(--accent);
}

.btn-ghost {
  background: transparent;
  color: var(--text-muted);
  border: 1px solid transparent;
}
.btn-ghost:hover {
  background: var(--surface);
  color: var(--text);
}
```

### Карточки
```css
.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 24px;
  transition: box-shadow var(--transition-base), transform var(--transition-base);
}
.card:hover {
  box-shadow: var(--shadow-lg);
  transform: translateY(-2px);
}

/* Интерактивная карточка */
.card-interactive {
  cursor: pointer;
}
.card-interactive:hover {
  border-color: var(--accent);
  box-shadow: 0 0 0 1px var(--accent), var(--shadow-md);
}
```

### Инпуты / Формы
```css
.input {
  width: 100%;
  padding: 10px 14px;
  font-size: 0.9375rem;
  background: var(--surface);
  border: 1.5px solid var(--border);
  border-radius: var(--radius-md);
  color: var(--text);
  transition: border-color var(--transition-fast), box-shadow var(--transition-fast);
  outline: none;
}
.input::placeholder { color: var(--text-muted); }
.input:hover { border-color: var(--text-muted); }
.input:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(99,102,241,.15);
}
.input.error {
  border-color: #ef4444;
  box-shadow: 0 0 0 3px rgba(239,68,68,.15);
}

.label {
  display: block;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--text);
  margin-bottom: 6px;
}
.hint {
  font-size: 0.8125rem;
  color: var(--text-muted);
  margin-top: 4px;
}
.error-msg {
  font-size: 0.8125rem;
  color: #ef4444;
  margin-top: 4px;
}
```

### Навбар
```css
.navbar {
  position: sticky;
  top: 0;
  z-index: var(--z-sticky);
  height: 60px;
  display: flex;
  align-items: center;
  padding: 0 clamp(16px, 5vw, 40px);
  background: rgba(255,255,255,0.85);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--border);
}

/* Dark navbar */
.navbar-dark {
  background: rgba(9,9,11,0.85);
}
```

### Модалки
```css
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,.5);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: var(--z-modal);
  animation: fadeIn 0.15s ease-out;
}

.modal {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-xl);
  padding: 32px;
  width: min(90vw, 520px);
  max-height: 85vh;
  overflow-y: auto;
  animation: scaleIn 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
  box-shadow: var(--shadow-xl);
}

@keyframes fadeIn {
  from { opacity: 0; }
  to   { opacity: 1; }
}
@keyframes scaleIn {
  from { opacity: 0; transform: scale(0.93); }
  to   { opacity: 1; transform: scale(1); }
}
```

### Toast / Уведомления
```css
.toast-container {
  position: fixed;
  bottom: 24px;
  right: 24px;
  z-index: var(--z-toast);
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.toast {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 18px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-xl);
  font-size: 0.9rem;
  min-width: 280px;
  animation: slideUp 0.3s cubic-bezier(0, 0, 0.2, 1);
}
.toast.success { border-left: 3px solid #22c55e; }
.toast.error   { border-left: 3px solid #ef4444; }
.toast.warning { border-left: 3px solid #f59e0b; }
```

### Badge / Chip
```css
.badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 10px;
  font-size: 0.75rem;
  font-weight: 500;
  border-radius: var(--radius-full);
}
.badge-default  { background: var(--surface-2); color: var(--text-muted); }
.badge-primary  { background: rgba(99,102,241,.12); color: #6366f1; }
.badge-success  { background: rgba(34,197,94,.12);  color: #16a34a; }
.badge-warning  { background: rgba(245,158,11,.12);  color: #d97706; }
.badge-danger   { background: rgba(239,68,68,.12);   color: #dc2626; }
```

### Skeleton loader
```html
<div class="skeleton" style="height: 20px; width: 60%; border-radius: 6px;"></div>
<div class="skeleton" style="height: 16px; width: 80%; border-radius: 6px; margin-top: 8px;"></div>
<div class="skeleton" style="height: 16px; width: 45%; border-radius: 6px; margin-top: 8px;"></div>
```

---

## Tailwind CSS — профессиональные паттерны

### Установка и конфиг
```js
// tailwind.config.js
module.exports = {
  content: ['./src/**/*.{js,jsx,ts,tsx,html}'],
  darkMode: 'class',  // или 'media'
  theme: {
    extend: {
      colors: {
        accent: {
          50: '#eef2ff',
          500: '#6366f1',
          600: '#4f46e5',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      borderRadius: {
        'xl': '12px',
        '2xl': '16px',
        '3xl': '24px',
      },
      boxShadow: {
        'glow': '0 0 20px rgba(99,102,241,.35)',
        'card': '0 1px 3px rgba(0,0,0,.06), 0 1px 2px rgba(0,0,0,.04)',
      }
    }
  }
}
```

### Часто используемые классы (шпаргалка)
```html
<!-- Карточка -->
<div class="bg-white dark:bg-zinc-900 rounded-2xl border border-zinc-200 dark:border-zinc-800 p-6 shadow-sm hover:shadow-md transition-shadow">

<!-- Кнопка primary -->
<button class="bg-indigo-500 hover:bg-indigo-600 text-white font-medium px-5 py-2.5 rounded-xl transition-all hover:-translate-y-0.5 hover:shadow-lg hover:shadow-indigo-500/30 active:scale-[0.98]">

<!-- Инпут -->
<input class="w-full bg-zinc-50 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded-xl px-4 py-2.5 text-sm outline-none focus:ring-2 focus:ring-indigo-500/30 focus:border-indigo-500 transition-all">

<!-- Gradient text -->
<h1 class="bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 bg-clip-text text-transparent font-bold text-4xl">

<!-- Glass card -->
<div class="bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl p-6">
```

---

## React — паттерны

### Структура компонента (современная)
```jsx
// Хорошая структура
function ProductCard({ product, onAddToCart }) {
  const [isAdding, setIsAdding] = useState(false);

  const handleAdd = async () => {
    setIsAdding(true);
    await onAddToCart(product.id);
    setIsAdding(false);
  };

  return (
    <article className="card card-interactive">
      <img
        src={product.image}
        alt={product.name}
        loading="lazy"
        className="rounded-lg aspect-square object-cover"
      />
      <div className="mt-4">
        <h3 className="font-semibold text-lg">{product.name}</h3>
        <p className="text-muted mt-1">{product.price}</p>
      </div>
      <button
        onClick={handleAdd}
        disabled={isAdding}
        className="btn btn-primary w-full mt-4"
      >
        {isAdding ? <Spinner size="sm" /> : 'Add to Cart'}
      </button>
    </article>
  );
}
```

### Custom Hook для анимации появления
```jsx
function useIntersection(ref, options) {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting) setIsVisible(true); },
      { threshold: 0.1, ...options }
    );
    if (ref.current) observer.observe(ref.current);
    return () => observer.disconnect();
  }, [ref]);

  return isVisible;
}

// Использование
function AnimatedSection({ children }) {
  const ref = useRef();
  const isVisible = useIntersection(ref);

  return (
    <div
      ref={ref}
      style={{
        opacity: isVisible ? 1 : 0,
        transform: isVisible ? 'translateY(0)' : 'translateY(20px)',
        transition: 'opacity 0.5s ease, transform 0.5s ease',
      }}
    >
      {children}
    </div>
  );
}
```

---

## Популярные библиотеки (выбор)

| Задача | Библиотека | Почему |
|--------|-----------|--------|
| Иконки | `lucide-react`, `@heroicons/react` | SVG, легковесные, консистентные |
| Анимации | `framer-motion` | API, spring-анимации |
| Модалки | `@radix-ui/react-dialog` | headless, доступность из коробки |
| Таблицы | `@tanstack/react-table` | Мощная, headless |
| Графики | `recharts`, `chart.js` | Простые в React/HTML |
| Даты | `date-fns` | Легче moment.js |
| Формы | `react-hook-form` + `zod` | Производительность + типизация |
| Виртуализация | `@tanstack/react-virtual` | Длинные списки |
| Toast | `sonner` | Современный, простой |

---

## Drag and Drop

```css
/* CSS для DnD */
.draggable {
  cursor: grab;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
  touch-action: none;  /* важно для мобильных */
}
.draggable:active { cursor: grabbing; }
.draggable.dragging {
  transform: rotate(2deg) scale(1.02);
  box-shadow: var(--shadow-xl);
  opacity: 0.9;
  z-index: 100;
}

/* Зона сброса */
.drop-zone {
  border: 2px dashed var(--border);
  border-radius: var(--radius-lg);
  transition: border-color 0.15s, background 0.15s;
}
.drop-zone.drag-over {
  border-color: var(--accent);
  background: rgba(99,102,241,.05);
}
```
