// /deep-review-flow — competency-based code review на детерминированных рельсах.
// Перенос skill `deep-review` в workflow: parallel-ревьюеры → adversarial verify → карточки → triage.
// args: { base?: string, target?: string, runId?: string }
//   base   — git ref для diff (дефолт origin/main); target — путь/паттерн (дефолт весь diff)

export const meta = {
  name: 'deep-review-flow',
  description: 'Competency-review (security/perf/arch/...) с adversarial-верификацией и карточкой на косяк',
  phases: [
    { title: 'Review', detail: 'параллельные ревьюеры по компетенциям' },
    { title: 'Verify', detail: 'adversarial проверка каждой находки' },
    { title: 'Report', detail: 'карточки + triage FIX/DEFER/ACCEPT' },
  ],
}

const COMPETENCIES = [
  { key: 'security',   lens: 'инъекции, authz/authn, утечки секретов, небезопасный SQL, trust boundary с LLM-вводом' },
  { key: 'perf',       lens: 'N+1 запросы, лишние аллокации, блокирующий IO, неэффективные циклы' },
  { key: 'arch',       lens: 'нарушение слоёв, протекание абстракций, дублирование, связность' },
  { key: 'concurrency',lens: 'гонки, дедлоки, незащищённое общее состояние, неатомарные операции' },
  { key: 'errors',     lens: 'проглоченные исключения, отсутствие обработки, тихие сбои, неверная пропагация' },
  { key: 'tests',      lens: 'непокрытые ветки, отсутствие edge-case тестов, хрупкие/замоканные мимо сути' },
]

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
          line: { type: 'string' },
          severity: { type: 'string', enum: ['low', 'medium', 'high', 'critical'] },
          evidence: { type: 'string' },
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
    triage: { type: 'string', enum: ['FIX', 'DEFER', 'ACCEPT'] },
    reason: { type: 'string' },
  },
  required: ['real', 'confidence', 'triage'],
}

async function withRetry(makeAgent, n, label) {
  let lastErr = 'null-результат (агент вернул пусто или пропущен)'
  for (let a = 0; a <= n; a++) {
    try { const r = await makeAgent(a); if (r != null) return r }
    catch (e) { lastErr = (e && e.message) ? e.message : String(e) }
  }
  log(`${label}: ретраи исчерпаны (${lastErr})`)  // ТЕКСТ ошибки обязателен - иначе тихий фейл неотличим от "0 находок"
  return null
}

const base = (args && args.base) || 'origin/main'
const target = (args && args.target) || `git diff ${base}...HEAD`
const runId = (args && args.runId) || 'review'
log(`deep-review-flow: base=${base}, target=${target}`)

// Phase Review — параллельные ревьюеры, каждый со своей линзой (perspective-diverse)
const raw = (await parallel(
  COMPETENCIES.map((c) => () => withRetry((att) =>
    agent(
      `Ты ревьюер компетенции "${c.key}". Изучи изменения: ${target} ` +
      `(если это git-выражение — выполни его и прочитай затронутые файлы целиком, не только хунки).\n` +
      `Ищи ТОЛЬКО: ${c.lens}.\n` +
      `Каждой находке дай уникальный id вида ${c.key}-NN, файл, строку, severity, evidence (цитата кода).`,
      { label: `review:${c.key}#${att}`, phase: 'Review', schema: FINDINGS },
    ), 1, `review:${c.key}`)),
)).filter(Boolean).flatMap((r) => r.findings)

// Барьер оправдан: dedup по всему множеству перед дорогой верификацией
const seen = new Set()
const unique = raw.filter((f) => {
  const k = `${f.file || ''}:${f.line || ''}:${f.title}`
  if (seen.has(k)) return false
  seen.add(k); return true
})
log(`находок: ${raw.length} сырых, ${unique.length} уникальных`)

// Phase Verify — pipeline: каждая находка независимо проходит adversarial-скептика
const judged = (await pipeline(
  unique,
  (f) => agent(
    `Adversarially проверь находку ревью. По умолчанию real=false, если доказательство неубедительно.\n` +
    `Находка: "${f.title}" (${f.severity}) в ${f.file}:${f.line || '?'}. Evidence: ${f.evidence || 'нет'}.\n` +
    `Перечитай реальный код в этом месте. Это настоящая проблема? Дай triage: FIX (чинить сейчас), ` +
    `DEFER (тикет), ACCEPT (не проблема/by design).\n` +
    `Ответь СТРОГО вызовом structured output (только поля схемы). НЕ пиши длинный текстовый разбор - ` +
    `краткое reason в поле схемы. Обязательно заверши вызовом инструмента.`,
    { label: `verify:${f.id}`, phase: 'Verify', schema: VERDICT },
  ),
  (v, f) => {
    if (v == null) return { ...f, status: 'verify-failed' }
    if (v.confidence < 0.5) return { ...f, status: 'low-confidence', reason: v.reason }
    return { ...f, status: v.real ? 'confirmed' : 'rejected', triage: v.triage, reason: v.reason }
  },
)).filter(Boolean)

const confirmed = judged.filter((f) => f.status === 'confirmed')
const fixNow = confirmed.filter((f) => f.triage === 'FIX')
log(`подтверждено ${confirmed.length}, из них FIX-сейчас: ${fixNow.length}`)

// Phase Report — карточка на каждый подтверждённый косяк (идея «не только вердикт»)
phase('Report')
await parallel(
  confirmed.map((f) => () => agent(
    `Оформи карточку находки в .runs/${runId}/findings/${f.id}.md: ` +
    `title "${f.title}", severity ${f.severity}, triage ${f.triage}, ${f.file}:${f.line || '?'}, ` +
    `evidence, repro-шаги, конкретный предлагаемый фикс (диффом если уместно). Верни путь.`,
    { label: `card:${f.id}`, phase: 'Report' },
  )),
)

const summary = await agent(
  `Сведи ревью в .runs/${runId}/summary.md: число находок по компетенциям, triage-разбивка, ` +
  `топ FIX-сейчас. Данные: ${JSON.stringify(confirmed.map((f) => ({ id: f.id, t: f.title, s: f.severity, tr: f.triage })))}. ` +
  `Верни короткое резюме и путь.`,
  { label: 'summary', phase: 'Report' },
)

return {
  runId,
  raw: raw.length,
  confirmed: confirmed.length,
  fixNow: fixNow.length,
  byTriage: {
    FIX: confirmed.filter((f) => f.triage === 'FIX').length,
    DEFER: confirmed.filter((f) => f.triage === 'DEFER').length,
    ACCEPT: judged.filter((f) => f.status === 'rejected').length,
  },
  findings: confirmed,
  summary,
}
