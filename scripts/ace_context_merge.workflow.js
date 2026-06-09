// ace_context_merge.workflow.js
// Run via the Workflow tool: Workflow({scriptPath: "<this file>", args: {...}})
//
// ACE delta-merge for self-improving rules/CLAUDE.md/memory (arXiv 2510.04618).
// Generator (the session that just ran) → Reflector (proposes adressable DELTAS,
// never a rewrite) → Curator (applies them) → fresh Verifier (reads git diff).
// See rules/ace-context-merge.md for the protocol and why rewriting causes
// "context collapse".
//
// NOTE on the runtime: the workflow JS sandbox has NO filesystem access. So the
// file is read/edited BY THE SUBAGENTS (which have Read/Edit tools), not by this
// script. This script does the deterministic orchestration + dedup of the delta
// LIST, and forces structured output so nothing is a free-form rewrite.
//
// args = {
//   targetFile: "~/.claude/CLAUDE.md",   // file to improve (required) — use an absolute path at call time
//   trajectory: "what worked / what failed / user corrections this session",  // required
//   maxDeltas: 12                                     // optional cap
// }

export const meta = {
  name: 'ace-context-merge',
  description: 'Self-improve a rules/CLAUDE.md/memory file via addressable deltas (no rewrite) — ACE Generator/Reflector/Curator',
  phases: [
    { title: 'Reflect', detail: 'propose addressable deltas vs the current file' },
    { title: 'Curate', detail: 'apply deduped deltas with surgical edits' },
    { title: 'Verify', detail: 'fresh agent reads the git diff, confirms no collapse' },
  ],
}

const a = args || {}
if (!a.targetFile || !a.trajectory) {
  throw new Error('ace-context-merge: args.targetFile and args.trajectory are required')
}
const maxDeltas = a.maxDeltas || 12

const DELTA_SCHEMA = {
  type: 'object',
  required: ['deltas'],
  properties: {
    deltas: {
      type: 'array',
      items: {
        type: 'object',
        required: ['op', 'rationale'],
        properties: {
          op: { type: 'string', enum: ['ADD', 'EDIT', 'DELETE'] },
          anchor: { type: 'string', description: 'For EDIT/DELETE: exact unique quote of the existing text to locate' },
          old_text: { type: 'string', description: 'For EDIT/DELETE: the current text being changed (must match file exactly)' },
          new_text: { type: 'string', description: 'For ADD/EDIT: the text to insert/replace with' },
          rationale: { type: 'string', description: 'Why this delta — trace to the trajectory' },
          section: { type: 'string', description: 'For ADD: which section/heading to append under' },
        },
      },
    },
  },
}

const VERDICT_SCHEMA = {
  type: 'object',
  required: ['verdict', 'reasons'],
  properties: {
    verdict: { type: 'string', enum: ['PASS', 'NEEDS_WORK'] },
    reasons: { type: 'array', items: { type: 'string' } },
    collapse_detected: { type: 'boolean', description: 'true if the file got shorter/vaguer (lost nuance)' },
  },
}

phase('Reflect')
const reflection = await agent(
  `You are the Reflector in an ACE delta-merge. Read the CURRENT file at:
  ${a.targetFile}
Then, from this session trajectory, propose ONLY addressable deltas — never a rewrite.

Trajectory (what to encode):
<<<
${a.trajectory}
>>>

Rules:
- Propose at most ${maxDeltas} deltas.
- op=ADD for genuinely new lessons (give 'section' = heading to append under, 'new_text').
- op=EDIT to sharpen an existing line (give 'anchor'+'old_text' = exact current text, 'new_text').
- op=DELETE only for text that is now WRONG/stale (give 'anchor'+'old_text', 'rationale').
- DEDUP: do NOT propose an ADD if the point already exists in the file. Read carefully first.
- Each delta must be self-contained and trace to the trajectory in 'rationale'.
- Do NOT shorten or "clean up" the file. Preserve accumulated nuance. Additive/surgical only.
Return the deltas object.`,
  { phase: 'Reflect', schema: DELTA_SCHEMA },
)

// Deterministic dedup of the delta LIST itself (identical/near-identical proposals).
const seen = new Set()
const deltas = (reflection.deltas || []).filter((d) => {
  const key = `${d.op}|${(d.new_text || d.old_text || '').trim().slice(0, 120)}`
  if (seen.has(key)) return false
  seen.add(key)
  return true
})
log(`Reflector proposed ${reflection.deltas?.length || 0} deltas, ${deltas.length} after dedup`)
if (!deltas.length) {
  return { applied: 0, note: 'No deltas to apply — file already covers the trajectory.' }
}

phase('Curate')
const curation = await agent(
  `You are the Curator. Apply EXACTLY these deltas to ${a.targetFile} using surgical edits
(search/replace for EDIT/DELETE, append-under-section for ADD). Do NOT rewrite the whole file.
Do NOT add anything not in this list. Preserve all other content verbatim.

Deltas (JSON):
${JSON.stringify(deltas, null, 2)}

After applying, report how many you applied and any you could not (and why).`,
  { phase: 'Curate' },
)
log('Curator: ' + String(curation).slice(0, 300))

phase('Verify')
const verdict = await agent(
  `You are a fresh-context Verifier. Run \`git -C <repo of ${a.targetFile}> diff -- ${a.targetFile}\`
(or read the file's current diff). Confirm:
(1) changes are additive/surgical, not a full rewrite;
(2) no accumulated nuance was lost (context collapse) — the file did NOT get shorter/vaguer;
(3) each change is sensible and not a duplicate of existing content.
Return PASS only if all three hold. Set collapse_detected=true if the file lost content/nuance.`,
  { phase: 'Verify', schema: VERDICT_SCHEMA },
)

return {
  applied: deltas.length,
  curator: String(curation).slice(0, 500),
  verdict: verdict.verdict,
  collapse_detected: verdict.collapse_detected,
  reasons: verdict.reasons,
}
