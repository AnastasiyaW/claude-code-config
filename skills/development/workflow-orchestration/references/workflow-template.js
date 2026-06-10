// workflow-template.js — аннотированный эталон со всеми нашими паттернами.
// Копируй секции по нужде. Это reference, не запускаемая команда (хотя синтаксис валиден).
// Валидация L1: node scripts/validate.mjs. В скрипте недопустимы недетерминизм (системные
// часы, генератор случайных чисел) и прямой fs/shell - даже упоминанием точных имён API в
// строках/комментах (рантайм сканирует исходник подстрокой, не AST - см. SKILL).

export const meta = {
  name: 'template',
  description: 'Эталонный workflow со всеми паттернами (retry, multisample, error policy, .runs)',
  phases: [
    { title: 'Find', detail: 'параллельные finders' },
    { title: 'Verify', detail: 'adversarial проверка находок' },
    { title: 'Report', detail: 'карточки + сводка' },
  ],
}

// ── Schemas (валидируют вывод агента, дают авто-ретрай на mismatch) ──────────
const FINDINGS = {
  type: 'object',
  properties: {
    findings: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          id: { type: 'string' },
          title: { type: 'string' },
          file: { type: 'string' },
          severity: { type: 'string', enum: ['low', 'medium', 'high', 'critical'] },
        },
        required: ['id', 'title', 'severity'],
      },
    },
  },
  required: ['findings'],
}
const VERDICT = {
  type: 'object',
  properties: {
    real: { type: 'boolean' },
    confidence: { type: 'number' },
    reason: { type: 'string' },
  },
  required: ['real', 'confidence'],
}

// ── Gap 1: retry при null/throw (платформа ретраит только schema-mismatch) ───
async function withRetry(makeAgent, n = 2, baseLabel = 'task') {
  for (let attempt = 0; attempt <= n; attempt++) {
    try {
      const r = await makeAgent(attempt)
      if (r != null) return r
    } catch (e) {
      if (attempt === n) {
        log(`${baseLabel}: исчерпаны ретраи (${e && e.message ? e.message : e})`)
        return null
      }
    }
  }
  return null
}

// ── Gap 2: multisampling + голосование большинством (чистая функция) ─────────
function majority(items, keyFn) {
  const counts = new Map()
  for (const it of items) {
    const k = keyFn(it)
    counts.set(k, (counts.get(k) || 0) + 1)
  }
  let best = null
  let bestN = 0
  for (const [k, n] of counts) if (n > bestN) { best = k; bestN = n }
  return { value: best, votes: bestN, total: items.length }
}

// ── runId из args (в скрипте нет доступа к часам) — штампует main-loop перед запуском ─
const runId = (args && args.runId) || 'run-unstamped'
const target = (args && args.target) || 'src/'
log(`template flow стартует: target=${target}, runId=${runId}`)

// ── Phase Find — параллельные finders с разными линзами + retry ──────────────
const FINDERS = [
  { key: 'security', lens: 'уязвимости, инъекции, утечки секретов' },
  { key: 'logic', lens: 'логические ошибки, граничные случаи' },
  { key: 'perf', lens: 'неэффективности, N+1, лишние аллокации' },
]
const found = (await parallel(
  FINDERS.map((f) => () =>
    withRetry(
      (att) =>
        agent(`Просканируй ${target} на: ${f.lens}. Верни находки.`, {
          label: `find:${f.key}#${att}`,
          phase: 'Find',
          schema: FINDINGS,
        }),
      2,
      `find:${f.key}`,
    ),
  ),
))
  .filter(Boolean)
  .flatMap((r) => r.findings)

log(`найдено сырых находок: ${found.length}`)

// ── Барьер ОПРАВДАН: dedup по всему множеству перед дорогой верификацией ──────
const seen = new Set()
const unique = found.filter((f) => {
  const k = `${f.file}:${f.title}`
  if (seen.has(k)) return false
  seen.add(k)
  return true
})

// ── Phase Verify — pipeline (БЕЗ барьера): каждая находка верифицируется ──────
//    + Gap 3 error policy: low-confidence не попадает в confirmed, но не теряется
const judged = await pipeline(
  unique,
  (f) =>
    agent(`Adversarially проверь находку (по умолчанию real=false если не уверен): ${f.title} в ${f.file}`, {
      label: `verify:${f.id}`,
      phase: 'Verify',
      schema: VERDICT,
    }),
  (v, f) => {
    if (v == null) return { ...f, status: 'verify-failed' }
    if (v.confidence < 0.5) return { ...f, status: 'low-confidence', reason: v.reason }
    return { ...f, status: v.real ? 'confirmed' : 'rejected', reason: v.reason }
  },
)
const confirmed = judged.filter(Boolean).filter((f) => f.status === 'confirmed')
log(`подтверждено: ${confirmed.length} / ${unique.length}`)

// ── Phase Report — Gap 4: агент оформляет карточку на каждый косяк в .runs/ ───
phase('Report')
await parallel(
  confirmed.map((f) => () =>
    agent(
      `Оформи карточку находки в .runs/${runId}/findings/${f.id}.md: ` +
        `заголовок "${f.title}", severity ${f.severity}, файл ${f.file}, ` +
        `+ repro и предложенный фикс. Верни путь файла.`,
      { label: `card:${f.id}`, phase: 'Report' },
    ),
  ),
)

// Независимая проверка (имя ≠ поведение): считаем карточки, не доверяем «оформил»
const audit = await agent(
  `Сосчитай .md файлы в .runs/${runId}/findings/ и верни их число.`,
  {
    label: 'audit:cards',
    phase: 'Report',
    schema: { type: 'object', properties: { count: { type: 'number' } }, required: ['count'] },
  },
)
if (audit && audit.count !== confirmed.length) {
  log(`⚠️ рассинхрон: карточек ${audit.count}, подтверждённых ${confirmed.length}`)
}

// Финальная сводка возвращается в контекст Claude (только она, не промежуточное)
return {
  runId,
  raw: found.length,
  unique: unique.length,
  confirmed: confirmed.length,
  lowConfidence: judged.filter(Boolean).filter((f) => f.status === 'low-confidence').length,
  findings: confirmed,
}
