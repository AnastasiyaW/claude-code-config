// /rlm-explore — RLM-style разбор БОЛЬШОГО текстового артефакта (лог/дамп/jsonl/листинг),
// который не влезает в окно контекста. Паттерн Recursive Language Models на нашем стеке:
// root видит только метаданные → partition+map по чанкам (sub-agent на чанк) → синтез.
// Разбор/цитаты: knowledge reference_recursive_language_models + rule rlm-context-as-program.
// args: { path: string, question: string, chunkLines?: number, maxChunks?: number,
//         model?: string, mapModel?: string, runId?: string }

export const meta = {
  name: 'rlm-explore',
  description: 'RLM-style: огромный артефакт → root peek → partition+map по чанкам → синтез',
  phases: [
    { title: 'Peek', detail: 'root читает только метаданные (число строк, структура), даёт план' },
    { title: 'Map', detail: 'sub-agent на каждый чанк извлекает findings по вопросу (fan-out)' },
    { title: 'Synthesize', detail: 'свести findings в цитируемый ответ' },
  ],
}

const path = (args && args.path) || ''
const question = (args && args.question) || 'НЕ ЗАДАН вопрос (передай args.question)'
const CHUNK = (args && args.chunkLines) || 4000      // строк на чанк по умолчанию
const MAXCHUNKS = (args && args.maxChunks) || 40     // потолок числа чанков (billing-гард)
const mapModel = (args && args.mapModel) || undefined // дешёвую модель на map (тиринг)
const runId = (args && args.runId) || 'rlm'

if (!path) {
  log('rlm-explore: НЕ задан args.path — нечего разбирать. Передай путь к большому файлу.')
  return { error: 'missing args.path' }
}

const PEEK_SCHEMA = {
  type: 'object',
  properties: {
    total_lines: { type: 'number' },
    note: { type: 'string' },        // короткая заметка о структуре (формат, что внутри)
    focus_hint: { type: 'string' },  // на что смотреть map-агентам (опц., regex/термы)
  },
  required: ['total_lines'],
}
const MAP_SCHEMA = {
  type: 'object',
  properties: {
    findings: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          fact: { type: 'string' },
          line_ref: { type: 'string' }, // напр. "L12030-12055" или ключ/таймштамп
        },
        required: ['fact'],
      },
    },
  },
  required: ['findings'],
}

log(`rlm-explore: "${question}" над ${path}`)

// Phase Peek — root видит ТОЛЬКО метаданные, не весь контент (ядро RLM)
phase('Peek')
const peek = await agent(
  `Ты root в RLM-разборе. НЕ читай весь файл целиком. Определи метаданные артефакта по пути:\n` +
  `${path}\n` +
  `Сделай дешёвые операции: посчитай число строк (wc -l), глянь первые ~40 строк (head) и пару ` +
  `срезов из середины/конца, определи формат (текст-лог / jsonl / md / csv-листинг) и что внутри.\n` +
  `Вопрос, ради которого разбираем: «${question}».\n` +
  `Верни total_lines, короткую note о структуре, и focus_hint — на что смотреть при чанк-разборе ` +
  `(ключевые термины/regex/поля), если очевидно. Не выдумывай содержимое — только реально увиденное.`,
  { label: 'peek', phase: 'Peek', schema: PEEK_SCHEMA },
)

const total = Math.max(1, Math.round((peek && peek.total_lines) || 0))
const focus = (peek && peek.focus_hint) || ''

// JS детерминированно считает диапазоны. Покрываем ВЕСЬ файл: если чанков получается больше
// потолка — РАСШИРЯЕМ чанк (а не отбрасываем хвост), чтобы не было молчаливой обрезки покрытия.
const wantChunks = Math.ceil(total / CHUNK)
const effChunks = Math.min(wantChunks, MAXCHUNKS)
const effChunkLines = Math.ceil(total / effChunks)
if (wantChunks > MAXCHUNKS) {
  log(`файл крупный: ${total} строк → ${wantChunks} чанков по ${CHUNK} превысило бы потолок ` +
      `${MAXCHUNKS}; расширил чанк до ${effChunkLines} строк, покрываю ВЕСЬ файл за ${effChunks} ` +
      `чанков (без отброса хвоста).`)
} else {
  log(`${total} строк → ${effChunks} чанков по ~${effChunkLines} строк.`)
}
if (budget && budget.total) {
  log(`budget: осталось ~${Math.round(budget.remaining() / 1000)}k токенов на прогон (${effChunks} map-агентов).`)
}

const ranges = []
for (let i = 0; i < effChunks; i++) {
  const start = i * effChunkLines + 1
  const end = Math.min(total, (i + 1) * effChunkLines)
  if (start > total) break
  ranges.push({ idx: i, start, end })
}

// Phase Map — fan-out: один sub-agent на чанк, читает СВОЙ диапазон строк и извлекает findings.
// pipeline без барьера: чанк i синтезируется не дожидаясь всех (но здесь синтез после всех — ок,
// барьер на Synthesize естественный: финальный ответ нужен по ВСЕМ чанкам разом).
const mapped = (await pipeline(
  ranges,
  (r) => agent(
    `Ты sub-RLM (depth=1) на ОДНОМ чанке большого артефакта. Прочитай ТОЛЬКО строки ` +
    `${r.start}–${r.end} файла:\n${path}\n` +
    `(используй Read с offset=${r.start - 1}/limit=${r.end - r.start + 1}, либо ` +
    `sed -n '${r.start},${r.end}p'). Не читай вне диапазона.\n` +
    `Извлеки только факты, релевантные вопросу: «${question}».` +
    (focus ? ` Фокус: ${focus}.` : '') +
    ` Для каждого факта верни fact + line_ref (например "L${r.start}+offset"). ` +
    `Если в этом чанке релевантного нет — верни пустой findings. Не выдумывай.`,
    { label: `map:${r.start}-${r.end}`, phase: 'Map', schema: MAP_SCHEMA, model: mapModel },
  ),
)).filter(Boolean)

const findings = mapped.flatMap((m) => (m && m.findings) ? m.findings : [])
log(`собрано findings: ${findings.length} из ${ranges.length} чанков.`)

// Phase Synthesize — свести в цитируемый ответ
phase('Synthesize')
const answer = await agent(
  `Синтезируй ответ на вопрос «${question}» из findings, собранных по чанкам большого артефакта ` +
  `${path} (всего ${total} строк, ${ranges.length} чанков).\n` +
  `Findings: ${JSON.stringify(findings)}\n` +
  `Дай связный ответ со ссылками на line_ref. Если данных не хватает — скажи прямо, какие чанки/что ` +
  `ещё смотреть. Запиши полный ответ в .runs/${runId}/rlm-report.md и верни короткое резюме (5-8 строк) ` +
  `+ путь файла.`,
  { label: 'synthesize', phase: 'Synthesize' },
)

return {
  runId,
  path,
  question,
  total_lines: total,
  chunks: ranges.length,
  chunk_lines: effChunkLines,
  widened: wantChunks > MAXCHUNKS,
  findings: findings.length,
  answer,
}
