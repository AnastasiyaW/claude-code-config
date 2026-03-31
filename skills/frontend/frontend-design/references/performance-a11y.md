# Производительность, Доступность, SEO

## Core Web Vitals — метрики 2024

| Метрика | Значение | Что влияет |
|---------|---------|-----------|
| **LCP** (Largest Contentful Paint) | < 2.5s | Главное изображение/заголовок |
| **INP** (Interaction to Next Paint) | < 200ms | Обработчики событий |
| **CLS** (Cumulative Layout Shift) | < 0.1 | Изображения без размеров, шрифты |

---

## Оптимизация изображений

```html
<!-- AVIF → WebP → JPEG fallback -->
<picture>
  <source type="image/avif" srcset="hero.avif">
  <source type="image/webp" srcset="hero.webp">
  <img
    src="hero.jpg"
    alt="Описание"
    width="1200"    <!-- ОБЯЗАТЕЛЬНО указывать размеры → предотвращает CLS -->
    height="630"
    loading="lazy"  <!-- кроме изображений above-the-fold -->
    decoding="async"
  >
</picture>

<!-- Адаптивные изображения под разные экраны -->
<img
  srcset="img-480.webp 480w,
          img-800.webp 800w,
          img-1200.webp 1200w"
  sizes="(max-width: 600px) 480px,
         (max-width: 900px) 800px,
         1200px"
  src="img-1200.webp"
  alt="Описание"
>

<!-- Hero изображение — НЕ lazy, с preload в <head> -->
<link rel="preload" as="image" href="hero.avif" type="image/avif">
```

**Размеры по форматам:** AVIF ≈ 2× лучше WebP и JPEG.

---

## Code Splitting и Loading

```js
// React lazy loading
const Dashboard = React.lazy(() => import('./pages/Dashboard'));
const Settings = React.lazy(() => import('./pages/Settings'));

function App() {
  return (
    <Suspense fallback={<PageSkeleton />}>
      <Routes>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/settings" element={<Settings />} />
      </Routes>
    </Suspense>
  );
}
```

```html
<!-- Preload критичных ресурсов -->
<link rel="preload" href="critical.css" as="style">
<link rel="preload" href="main.js" as="script">
<link rel="preload" href="Inter.woff2" as="font" type="font/woff2" crossorigin>

<!-- Prefetch следующей страницы -->
<link rel="prefetch" href="/checkout">

<!-- Preconnect к внешним хостам -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="dns-prefetch" href="https://api.example.com">
```

---

## Service Workers и PWA

```js
// Регистрация SW
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js')
      .then(reg => console.log('SW зарегистрирован'))
      .catch(err => console.error('Ошибка SW:', err));
  });
}

// sw.js — стратегия Cache First для статики
const CACHE = 'v1';
const STATIC = ['/index.html', '/main.css', '/app.js'];

self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE)
      .then(cache => cache.addAll(STATIC))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;

  e.respondWith(
    caches.match(e.request)
      .then(cached => cached || fetch(e.request)
        .then(response => {
          const clone = response.clone();
          caches.open(CACHE).then(cache => cache.put(e.request, clone));
          return response;
        })
      )
  );
});
```

```json
// manifest.json (PWA)
{
  "name": "Моё приложение",
  "short_name": "App",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#09090b",
  "theme_color": "#6366f1",
  "icons": [
    { "src": "/icons/192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "/icons/512.png", "sizes": "512x512", "type": "image/png" }
  ]
}
```

---

## Виртуализация списков

```jsx
// @tanstack/react-virtual
import { useVirtualizer } from '@tanstack/react-virtual';

function VirtualList({ items }) {
  const parentRef = useRef();

  const virtualizer = useVirtualizer({
    count: items.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 60,  // примерная высота строки
    overscan: 5,             // рендерить 5 элементов за пределами видимости
  });

  return (
    <div
      ref={parentRef}
      style={{ height: '600px', overflow: 'auto' }}
    >
      <div style={{ height: virtualizer.getTotalSize() + 'px', position: 'relative' }}>
        {virtualizer.getVirtualItems().map(virtualItem => (
          <div
            key={virtualItem.key}
            style={{
              position: 'absolute',
              top: virtualItem.start + 'px',
              width: '100%',
            }}
          >
            <Item data={items[virtualItem.index]} />
          </div>
        ))}
      </div>
    </div>
  );
}
```

---

## Доступность (a11y)

### Семантика — первый шаг
```html
<!-- Плохо -->
<div class="nav"><div class="nav-item">Home</div></div>
<div class="btn" onclick="...">Click</div>

<!-- Хорошо -->
<nav aria-label="Основная навигация">
  <a href="/">Home</a>
</nav>
<button type="button">Click</button>
```

### ARIA для интерактивных компонентов
```html
<!-- Модальное окно -->
<div role="dialog" aria-modal="true" aria-labelledby="modal-title" aria-describedby="modal-desc">
  <h2 id="modal-title">Заголовок</h2>
  <p id="modal-desc">Описание</p>
  <button aria-label="Закрыть окно">✕</button>
</div>

<!-- Раскрывающееся меню -->
<button aria-expanded="false" aria-controls="menu-list">Меню</button>
<ul id="menu-list" role="menu" hidden>
  <li role="menuitem"><a href="/">Главная</a></li>
</ul>

<!-- Live-регион для уведомлений -->
<div aria-live="polite" aria-atomic="true" class="sr-only" id="notifications"></div>
```

### Focus management
```css
/* Никогда не убирай outline без замены */
:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
  border-radius: 4px;
}

/* Skip link (для скринридеров) */
.skip-link {
  position: absolute;
  transform: translateY(-100%);
  transition: transform 0.2s;
}
.skip-link:focus { transform: translateY(0); }
```

```html
<!-- В начале <body> -->
<a href="#main-content" class="skip-link">Перейти к содержимому</a>
<main id="main-content">...</main>
```

### Контрастность (WCAG AA)
- Обычный текст: минимум 4.5:1
- Крупный текст (18px+): минимум 3:1
- Компоненты UI (кнопки, инпуты): минимум 3:1

Инструменты: [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/), Chrome DevTools → Accessibility

---

## SEO

```html
<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Уникальный заголовок страницы | Сайт</title>
  <meta name="description" content="Описание страницы до 160 символов">
  <link rel="canonical" href="https://example.com/page">

  <!-- Open Graph (для соц. сетей) -->
  <meta property="og:title" content="Заголовок">
  <meta property="og:description" content="Описание">
  <meta property="og:image" content="https://example.com/og-image.jpg">
  <meta property="og:url" content="https://example.com/page">
  <meta property="og:type" content="website">

  <!-- Twitter Card -->
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="Заголовок">

  <!-- Alternate для i18n -->
  <link rel="alternate" hreflang="en" href="https://example.com/en/page">
  <link rel="alternate" hreflang="ru" href="https://example.com/ru/page">
</head>
```

### Структурированные данные (Schema.org)
```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "Название продукта",
  "description": "Описание",
  "image": "https://example.com/product.jpg",
  "offers": {
    "@type": "Offer",
    "price": "99.99",
    "priceCurrency": "RUB",
    "availability": "https://schema.org/InStock"
  }
}
</script>
```

---

## HTTP и кеширование

```
# Стратегии Cache-Control

# Статика с хешем в имени → кешировать надолго
Cache-Control: public, max-age=31536000, immutable
# Подходит для: app.a3f8b2.js, style.7c4d1e.css

# HTML → не кешировать (или короткий кеш)
Cache-Control: no-cache
# или:
Cache-Control: public, max-age=0, must-revalidate

# API ответы
Cache-Control: private, max-age=60
```

**HTTP/2 и HTTP/3:**
- HTTP/2: мультиплексирование, server push, сжатие заголовков
- HTTP/3 (QUIC): быстрый старт соединения, нет head-of-line blocking, работает при смене сети (мобильный → WiFi)

---

## Интернационализация (i18n)

```html
<html lang="ru" dir="ltr">
<!-- Для арабского/иврита: dir="rtl" -->
```

```js
// Intl API — нативно в браузере
const formatter = new Intl.NumberFormat('ru-RU', {
  style: 'currency',
  currency: 'RUB',
});
formatter.format(1234567.89);  // "1 234 567,89 ₽"

const dateFormatter = new Intl.DateTimeFormat('ru-RU', {
  year: 'numeric', month: 'long', day: 'numeric'
});
dateFormatter.format(new Date());  // "15 января 2025 г."

// RTL-совместимые стили (используй logical properties)
.card {
  margin-inline-start: 16px;  /* вместо margin-left */
  padding-inline: 24px;       /* вместо padding-left + padding-right */
  border-inline-start: 2px solid var(--accent); /* вместо border-left */
}
```

---

## Инструменты для проверки

| Инструмент | Для чего |
|-----------|---------|
| Lighthouse (Chrome DevTools) | Производительность, SEO, a11y |
| WebPageTest | Детальный анализ загрузки |
| axe DevTools | Проверка доступности |
| PageSpeed Insights | CWV в реальных условиях |
| Squoosh | Оптимизация изображений |
| BundlePhobia | Вес npm-пакетов |
