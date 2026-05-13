# <Layer name> -- Gotchas

Layer-scoped known foot-guns. **Each entry comes from a real failure.**
Speculative "things to watch out for" do not belong here; they belong
in `patterns.md` as positive guidance.

## Identity and format

- IDs are stable per layer (`G-1`, `G-2`, ...). Never reuse retired IDs.
- Each entry has: symptom -> cause -> fix -> link to the feature/incident
  that surfaced it.

## G-1 -- <short gotcha title>

**Symptom:** <what you observe>. <Example output, log line, or
stack trace excerpt if useful>.

**Cause:** <one sentence root cause>.

**Fix:** <concrete steps or code change>.

**Surfaced by:** F-NNN, incident YYYY-MM-DD, or review L-N F-N.

<!-- Copy the block above per new gotcha. -->
