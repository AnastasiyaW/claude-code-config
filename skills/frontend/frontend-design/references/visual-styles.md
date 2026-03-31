# Визуальные стили, Цвет, Типографика, Эффекты

## Актуальные стили 2024–2025

### 1. Dark Minimal (самый популярный)
Тёмный фон, акцентные цвета, минимум декора. Используется в Vercel, Linear, Raycast.

```css
:root {
  --bg: #09090b;
  --surface: #18181b;
  --surface-2: #27272a;
  --border: rgba(255,255,255,0.07);
  --text: #fafafa;
  --text-muted: #a1a1aa;
  --accent: #6366f1;   /* indigo */
  --accent-2: #8b5cf6; /* violet */
}
```

### 2. Glassmorphism
Полупрозрачность + blur. Работает только поверх интересного фона (градиент, изображение).

```css
.glass-card {
  background: rgba(255, 255, 255, 0.07);
  backdrop-filter: blur(20px) saturate(180%);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  /* Важно: нужен интересный фон позади */
}

/* Часто используется с анимированным градиентным фоном */
.gradient-bg {
  background: linear-gradient(
    135deg,
    #667eea 0%,
    #764ba2 25%,
    #f093fb 50%,
    #4facfe 75%,
    #43e97b 100%
  );
  background-size: 400% 400%;
  animation: gradientShift 15s ease infinite;
}

@keyframes gradientShift {
  0%, 100% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
}
```

**⚠️ Ошибки glassmorphism:**
- Размытие без интересного фона → просто серая карточка
- Слишком высокая прозрачность → нечитаемый текст
- Использовать везде → перегруженность

### 3. Neomorphism (мягкий UI)

```css
/* Светлый неоморфизм */
.neu-raised {
  background: #e0e5ec;
  border-radius: 16px;
  box-shadow:
    8px 8px 20px #b8bec7,
    -8px -8px 20px #ffffff;
}

.neu-inset {
  background: #e0e5ec;
  border-radius: 16px;
  box-shadow:
    inset 6px 6px 14px #b8bec7,
    inset -6px -6px 14px #ffffff;
}

/* Тёмный неоморфизм */
.neu-dark {
  background: #2d3436;
  box-shadow:
    6px 6px 14px #1e2426,
    -6px -6px 14px #3c4648;
}
```

**Подходит для:** калькуляторы, плееры, дашборды с аналоговым ощущением.
**Не подходит для:** интерфейсы со многими элементами — теряется иерархия.

### 4. Gradient Everything (тренд 2024)

```css
/* Градиентные кнопки */
.btn-gradient {
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  border: none;
  color: white;
  padding: 12px 24px;
  border-radius: 10px;
  position: relative;
  transition: opacity 0.2s, transform 0.2s;
}
.btn-gradient::before {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: inherit;
  background: linear-gradient(135deg, #4f46e5, #7c3aed);
  opacity: 0;
  transition: opacity 0.2s;
}
.btn-gradient:hover::before { opacity: 1; }
.btn-gradient:hover { transform: translateY(-1px); }

/* Gradient border */
.gradient-border {
  position: relative;
  border-radius: 12px;
  background: var(--surface);
}
.gradient-border::before {
  content: '';
  position: absolute;
  inset: -1px;
  border-radius: 13px;
  background: linear-gradient(135deg, #6366f1, #ec4899);
  z-index: -1;
}
```

### 5. Material Design 3 (You)
Google's current system — адаптируется к цветам контента.

```css
/* MD3 tokens subset */
:root {
  --md-primary: #6750A4;
  --md-on-primary: #FFFFFF;
  --md-surface: #FFFBFE;
  --md-surface-variant: #E7E0EC;
  --md-on-surface: #1C1B1F;
  --md-outline: #79747E;
  --md-radius: 12px;
  /* MD3 использует elevation через box-shadow, не непрозрачность */
  --md-elevation-1: 0 1px 2px rgba(0,0,0,.3), 0 1px 3px 1px rgba(0,0,0,.15);
  --md-elevation-2: 0 1px 2px rgba(0,0,0,.3), 0 2px 6px 2px rgba(0,0,0,.15);
}
```

---

## Цвет: практические правила

### Цветовые роли (не просто "синий")
```
Primary    — главный акцент, CTA-кнопки
Secondary  — второстепенные действия
Neutral    — фон, поверхности, границы
Semantic   — success/warning/error/info
```

### 60-30-10 правило
- 60% — нейтральный (фон, поверхности)
- 30% — второстепенный
- 10% — акцентный

### Палитра от одного цвета (CSS)
```css
/* Генерация оттенков через HSL */
:root {
  --hue: 238;              /* синий/индиго */
  --accent-50:  hsl(var(--hue), 90%, 95%);
  --accent-100: hsl(var(--hue), 85%, 90%);
  --accent-200: hsl(var(--hue), 80%, 80%);
  --accent-300: hsl(var(--hue), 75%, 70%);
  --accent-400: hsl(var(--hue), 70%, 60%);
  --accent-500: hsl(var(--hue), 65%, 50%);  /* base */
  --accent-600: hsl(var(--hue), 70%, 42%);
  --accent-700: hsl(var(--hue), 75%, 35%);
  --accent-800: hsl(var(--hue), 80%, 25%);
  --accent-900: hsl(var(--hue), 85%, 15%);
}
```

---

## Анимации и переходы

### Easing функции
```css
/* Встроенные (базовые) */
transition: all 0.2s ease;
transition: all 0.2s ease-in-out;

/* Cubic-bezier (профессиональные) */
--ease-in:        cubic-bezier(0.4, 0, 1, 1);
--ease-out:       cubic-bezier(0, 0, 0.2, 1);    /* большинство UI */
--ease-in-out:    cubic-bezier(0.4, 0, 0.2, 1);   /* transitions */
--ease-spring:    cubic-bezier(0.34, 1.56, 0.64, 1); /* пружинящий */
--ease-bounce:    cubic-bezier(0.175, 0.885, 0.32, 1.275);
```

### Ключевые анимации для UI

```css
/* Появление снизу (самое естественное) */
@keyframes slideUp {
  from { opacity: 0; transform: translateY(16px); }
  to   { opacity: 1; transform: translateY(0); }
}

/* Масштабирование (для модалок/поповеров) */
@keyframes scaleIn {
  from { opacity: 0; transform: scale(0.95); }
  to   { opacity: 1; transform: scale(1); }
}

/* Мерцание (skeleton loading) */
@keyframes shimmer {
  0%   { background-position: -200% center; }
  100% { background-position: 200% center; }
}
.skeleton {
  background: linear-gradient(
    90deg,
    var(--surface) 25%,
    var(--surface-2) 50%,
    var(--surface) 75%
  );
  background-size: 200% auto;
  animation: shimmer 1.5s linear infinite;
  border-radius: var(--radius-sm);
}

/* Пульсация (badge, уведомления) */
@keyframes pulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(99, 102, 241, 0.4); }
  50% { box-shadow: 0 0 0 8px rgba(99, 102, 241, 0); }
}
```

### Правила скорости
| Тип | Длительность |
|-----|-------------|
| Мгновенный feedback (hover, press) | 100–150ms |
| Стандартный переход | 200–250ms |
| Вход элемента на страницу | 300–400ms |
| Сложная анимация / hero | 400–600ms |
| Никогда больше | 700ms |

---

## Тени — профессиональная система

```css
/* Многослойные тени (реалистичнее) */
--shadow-xs: 0 1px 2px rgba(0,0,0,.05);
--shadow-sm: 0 1px 3px rgba(0,0,0,.06), 0 1px 2px rgba(0,0,0,.04);
--shadow-md: 0 4px 6px rgba(0,0,0,.05), 0 2px 4px rgba(0,0,0,.04);
--shadow-lg: 0 10px 15px rgba(0,0,0,.04), 0 4px 6px rgba(0,0,0,.04);
--shadow-xl: 0 20px 25px rgba(0,0,0,.05), 0 10px 10px rgba(0,0,0,.04);

/* Цветные тени (на акцентных элементах) */
.btn-primary {
  box-shadow: 0 4px 14px rgba(99, 102, 241, 0.4);
}
.btn-primary:hover {
  box-shadow: 0 8px 20px rgba(99, 102, 241, 0.5);
}
```

---

## Dark Mode

```css
/* Метод 1: prefers-color-scheme */
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #09090b;
    --surface: #18181b;
    /* ... */
  }
}

/* Метод 2: data-theme атрибут (с JS-переключением) */
[data-theme="dark"] { /* ... */ }

/* JS переключение */
const toggle = () => {
  const html = document.documentElement;
  html.dataset.theme = html.dataset.theme === 'dark' ? 'light' : 'dark';
  localStorage.setItem('theme', html.dataset.theme);
};

/* Предотвратить FOUC — в <head> до загрузки CSS */
const saved = localStorage.getItem('theme');
const preferred = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
document.documentElement.dataset.theme = saved || preferred;
```
