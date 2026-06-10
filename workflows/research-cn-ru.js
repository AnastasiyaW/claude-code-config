// /research-cn-ru — research с обязательными китайскими и русскими углами (наше правило ресерча).
// Структура как у /deep-research (scope → search → verify → synthesize), но углы поиска включают
// CN (Alibaba/Tencent/DeepSeek arxiv, ModelScope, Gitee, Zhihu, CSDN) и RU (Хабр, TG-каналы).
// args: { question: string, runId?: string }

export const meta = {
  name: 'research-cn-ru',
  description: 'Research с китайскими и русскими источниками + adversarial-проверка релевантности',
  phases: [
    { title: 'Scope', detail: 'декомпозиция вопроса на углы (вкл. CN и RU)' },
    { title: 'Search', detail: 'параллельный поиск по углам' },
    { title: 'Verify', detail: 'скептики отсеивают нерелевантное/недостоверное' },
    { title: 'Synthesize', detail: 'цитируемый отчёт' },
  ],
}

const question = (args && args.question) || 'НЕ ЗАДАН вопрос (передай args.question)'
const runId = (args && args.runId) || 'research'

// Фиксированные углы: всегда покрываем CN и RU, плюс динамические от scope-агента
const FIXED_ANGLES = [
  { key: 'web-en', hint: 'англоязычный веб, официальная документация, arxiv' },
  { key: 'cn',     hint: 'китайские источники: arxiv-лабы Alibaba/Tencent/DeepSeek, ModelScope, Gitee, Zhihu, CSDN. Ищи и на китайском (переведи ключевые термины).' },
  { key: 'ru',     hint: 'русские источники: Хабр, профильные Telegram-каналы, vc.ru. Ищи на русском.' },
]

const ANGLES_SCHEMA = {
  type: 'object',
  properties: { angles: { type: 'array', items: { type: 'string' }, minItems: 2 } },
  required: ['angles'],
}
const HITS_SCHEMA = {
  type: 'object',
  properties: {
    hits: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          claim: { type: 'string' },
          url: { type: 'string' },
          source_lang: { type: 'string' },
          relevance: { type: 'number' },
        },
        required: ['claim', 'url'],
      },
    },
  },
  required: ['hits'],
}
const KEEP_SCHEMA = {
  type: 'object',
  properties: { keep: { type: 'boolean' }, reason: { type: 'string' } },
  required: ['keep'],
}

log(`research-cn-ru: "${question}"`)

// Phase Scope — декомпозиция на содержательные под-вопросы
phase('Scope')
const scoped = await agent(
  `Декомпозируй исследовательский вопрос на 3-5 разных под-углов (аспектов): "${question}". ` +
  `Верни список коротких формулировок углов.`,
  { label: 'scope', phase: 'Scope', schema: ANGLES_SCHEMA },
)
const dynamicAngles = (scoped && scoped.angles ? scoped.angles : []).slice(0, 5)
  .map((a, i) => ({ key: `aspect-${i}`, hint: a }))
const allAngles = [...FIXED_ANGLES, ...dynamicAngles]

// Phase Search — параллельные воркеры, по одному на угол (fan-out)
const found = (await parallel(
  allAngles.map((ang) => () =>
    agent(
      `Исследуй вопрос «${question}» в разрезе угла: ${ang.hint}\n` +
      `Сделай несколько веб-поисков (для CN/RU-углов используй allowed_domains и запросы на ` +
      `соответствующем языке). Для каждого факта верни claim + url + source_lang + relevance (0..1). ` +
      `Только реально найденное в источниках, без догадок.`,
      { label: `search:${ang.key}`, phase: 'Search', schema: HITS_SCHEMA },
    ),
  ),
)).filter(Boolean).flatMap((r) => r.hits)

// Барьер оправдан: dedup по url + отбор top по релевантности перед верификацией
const byUrl = new Map()
for (const h of found) if (h.url && !byUrl.has(h.url)) byUrl.set(h.url, h)
const candidates = [...byUrl.values()]
  .sort((a, b) => (b.relevance || 0) - (a.relevance || 0))
  .slice(0, 30)
log(`найдено ${found.length} фактов, уникальных url ${byUrl.size}, в верификацию ${candidates.length}`)

// Phase Verify — скептик на каждый факт: релевантен ли вопросу и подтверждён ли источником
const verified = (await pipeline(
  candidates,
  (h) => agent(
    `Скептически проверь факт для вопроса «${question}».\n` +
    `Claim: "${h.claim}"\nИсточник: ${h.url} (${h.source_lang || '?'})\n` +
    `Открой источник. Подтверждает ли он claim и релевантен ли вопросу? ` +
    `keep=false если источник не подтверждает, нерелевантен, или это мусор/SEO.`,
    { label: `verify:${candidates.indexOf(h)}`, phase: 'Verify', schema: KEEP_SCHEMA },
  ),
  (v, h) => (v && v.keep ? h : null),
)).filter(Boolean)

log(`прошли верификацию: ${verified.length}/${candidates.length}`)

// Phase Synthesize — цитируемый отчёт, баланс языков отмечается явно
phase('Synthesize')
const report = await agent(
  `Синтезируй цитируемый отчёт по вопросу «${question}» из проверенных фактов: ${JSON.stringify(verified)}.\n` +
  `Запиши в .runs/${runId}/report.md. Каждое утверждение — со ссылкой на url. ` +
  `Явно отметь, что дали китайские и русские источники (если они добавили то, чего нет в англо-вебе). ` +
  `Верни короткое резюме (5-8 строк) и путь файла.`,
  { label: 'synthesize', phase: 'Synthesize' },
)

return {
  runId,
  question,
  angles: allAngles.length,
  rawHits: found.length,
  verified: verified.length,
  langs: [...new Set(verified.map((h) => h.source_lang).filter(Boolean))],
  report,
}
