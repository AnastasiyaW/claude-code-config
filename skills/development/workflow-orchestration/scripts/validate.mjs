#!/usr/bin/env node
// L1-валидатор workflow-скриптов. Оборачивает тело в async-функцию (как runtime),
// ловит SyntaxError без выполнения. Проверяет также наличие meta.name / meta.description.
// Запуск: node validate.mjs <file1.js> [file2.js ...]
import { readFileSync } from 'node:fs'

const RUNTIME_GLOBALS = ['agent', 'parallel', 'pipeline', 'phase', 'log', 'workflow', 'args', 'budget']
const files = process.argv.slice(2)
if (!files.length) { console.error('usage: node validate.mjs <file...>'); process.exit(2) }

let failed = 0
for (const file of files) {
  let src
  try { src = readFileSync(file, 'utf8') } catch (e) { console.log(`FAIL ${file}: не читается (${e.message})`); failed++; continue }

  // meta — pure literal эвристика: есть name и description, нет вызовов функций до тела
  const hasName = /export\s+const\s+meta\s*=\s*\{[\s\S]*?\bname\s*:/.test(src)
  const hasDesc = /\bdescription\s*:/.test(src)

  // Workflow runtime сканирует ИСХОДНИК подстрокой (не AST): запрещённые имена недетерминизма
  // отвергаются даже в строковых литералах/комментах. Ловим это ДО запуска.
  const banned = [/Date\s*\.\s*now/, /Math\s*\.\s*random/, /new\s+Date\b/]
    .filter((re) => re.test(src))
  if (banned.length) {
    console.log(`FAIL ${file}: runtime отвергнет - упоминание недетерминизма в исходнике ` +
      `(даже в строке/комменте): ${banned.map((re) => re.source).join(', ')}. Переформулируй описательно.`)
    failed++
    continue
  }

  // export const meta → const meta; затем тело в async arrow с runtime-глобалами как параметрами
  const body = src.replace(/export\s+const\s+meta\s*=/, 'const meta =')
  const wrapped = `return (async function (${RUNTIME_GLOBALS.join(', ')}) {\n${body}\n});`

  try {
    new Function(wrapped) // парсит тело арроу целиком; не выполняет
    const notes = []
    if (!hasName) notes.push('нет meta.name')
    if (!hasDesc) notes.push('нет meta.description')
    if (notes.length) { console.log(`WARN ${file}: синтаксис ок, но ${notes.join(', ')}`); }
    else console.log(`OK   ${file}`)
  } catch (e) {
    console.log(`FAIL ${file}: ${e.name}: ${e.message}`)
    failed++
  }
}
console.log(`\n${files.length - failed}/${files.length} прошли L1`)
process.exit(failed ? 1 : 0)
