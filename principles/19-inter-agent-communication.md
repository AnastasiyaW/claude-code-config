# Inter-Agent Communication - directed asynchronous messaging between sessions

## The problem

Parallel Claude Code sessions sharing a workspace need more than shared state. They need to **talk to each other** - ask targeted questions, report specific completions, hand off work items to named recipients, broadcast architecture decisions that affect everyone.

The coordination patterns in [principle 18](18-multi-session-coordination.md) cover **state ownership** (who holds what):
- Append-only handoffs = bulletin board ("I'm done, anyone continue")
- Lock files = mutex ("GPU 2 is mine until heartbeat stops")

Neither addresses **directed messaging** ("Hey session X, can you rerun the benchmark with these params?"). A handoff posted to the shared INDEX is seen by everyone; a lock file has no room for a question. For point-to-point communication with delivery semantics, the right pattern is older than the internet: **mail**.

## Two coordination axes, four patterns

| | **Broadcast** (any recipient) | **Directed** (specific recipient) |
|---|---|---|
| **Shared state** | Handoffs (principle 18) | *no widely-used pattern - state is inherently shared* |
| **Messages** | Broadcast mailbox (`mailbox/all/`) | Per-recipient mailbox (`mailbox/<name>/`) |

Principle 18 occupies the top row. Principle 19 occupies the bottom row. They are complementary, not competing.

## Why classical mail semantics specifically

Email has survived 40+ years because it solves a narrow problem extremely well: **asynchronous point-to-point communication with delivery guarantees, between parties that may never be online simultaneously**.

Every feature of email maps directly to an agent-coordination need:

| Email feature | What agents need it for |
|---|---|
| **Addressing (To / Cc)** | "This specific session, please act" |
| **From / Reply-To** | Recipient can respond back |
| **Subject** | Triage without reading body |
| **Threading (In-Reply-To / References)** | Follow a multi-turn conversation |
| **Date** | Know how fresh the request is |
| **Read / Unread status** | Know whether recipient has seen it |
| **Inbox** | Per-recipient queue, no polling shared state |
| **Sent folder** | Sender's audit trail of what was sent |
| **Delivery receipt** | Sender knows recipient picked up the message |
| **Filter rules** | Auto-prioritize by sender or topic |

Agents reinventing this from scratch end up with some subset of these features, usually ad-hoc. Borrowing email's vocabulary gives a well-understood mental model and a 40-year track record of edge cases already thought through.

## Minimal implementation

File-based mailbox on shared filesystem. No broker, no daemon, no network service.

```
.claude/mailbox/
├── <agent-name>/
│   ├── inbox/       # messages addressed to this agent
│   ├── sent/        # copies of messages this agent sent
│   └── archive/     # processed messages (read + handled)
├── all/             # broadcast inbox (everyone reads)
└── INDEX.md         # optional: human-readable log of all traffic
```

Each message is a markdown file with email-style frontmatter:

```markdown
---
from: session-alpha
to: session-beta
cc: [session-gamma]
subject: LoRA training crashed on GPU 3
date: 2026-04-14T14:30:00
message_id: 20260414-143000-alpha-001
in_reply_to: 20260414-141500-beta-017  # threading
priority: normal  # low | normal | high | urgent
status: unread    # unread | read | replied | archived
---

Hey beta, the LoRA training you asked me to launch crashed at step 400
with CUDA OOM. Stack trace in /workspace/logs/train_400.log.

I dropped batch_size from 4 to 2, restarting now. ETA 45 min.
```

### Send

1. Writer chooses a unique `message_id` (timestamp + sender + sequence works)
2. Write the message file to `mailbox/<recipient>/inbox/<message_id>.md` (atomic via Write tool)
3. Copy the same file to `mailbox/<sender>/sent/<message_id>.md` (sender's audit trail)
4. Optionally append one line to `mailbox/INDEX.md` for human-readable traffic log

### Receive

Hooks trigger inbox checks automatically:
- **SessionStart**: full inbox scan, show all unread messages to the agent
- **UserPromptSubmit**: quick check before each user message (catches mail that arrived mid-session)
- **PreToolUse (throttled)**: scan every N minutes during autonomous/long-running work

When the agent reads a message, it updates the file's `status` from `unread` to `read` (simple Edit). After acting on it, `archived` and move to `mailbox/<agent>/archive/`.

### Reply

1. Use the same protocol but set `in_reply_to` to the original `message_id`
2. `subject` conventionally prefixed `Re: ` (mirrors SMTP)
3. Reply goes to the original sender's inbox

### Delivery receipt (optional)

When reading a message, if the sender wants confirmation, write a minimal receipt back:

```markdown
---
from: session-beta
to: session-alpha
subject: "Receipt: 20260414-143000-alpha-001"
date: 2026-04-14T14:31:00
message_id: 20260414-143100-beta-receipt
in_reply_to: 20260414-143000-alpha-001
is_receipt: true
---

Read at 14:31. Will act.
```

Sender can see receipts land in their inbox (or a dedicated `mailbox/<sender>/receipts/` folder).

## Decision tree: which coordination primitive to use

```
What am I trying to do?
│
├── "Set a value that anyone might need later"
│   → memory file (not coordination, just persistence)
│
├── "Tell future sessions what state I leave behind"
│   → handoff (broadcast, principle 18)
│
├── "Claim an exclusive resource until I'm done"
│   → lock file (mutex, principle 18)
│
├── "Ask a specific other session to do something"
│   → directed mailbox message (principle 19)
│
├── "Announce a decision all agents should know"
│   → mailbox/all/ broadcast (principle 19)
│
└── "Get a response back from a specific session"
    → mailbox message + in_reply_to threading (principle 19)
```

## When NOT to use a mailbox

- **Single-chat workflows.** If you never run parallel sessions, a mailbox is overkill - there's nobody to message.
- **Synchronous decisions.** If you need an answer right now and the other session can't process it in time, the mailbox will queue the message but won't get you a response fast. Either wait asynchronously, or have the user coordinate directly.
- **Real-time control flow.** Mail is for hints and requests, not for replacing a function call. If Chat A's work literally cannot proceed without Chat B's answer, consider whether they should be one session.
- **Simple broadcast.** If the message is "I finished" with no specific addressee, a handoff is simpler and already has the infrastructure (principle 18).

## Anti-patterns to avoid

1. **Polling the inbox on every tool call.** Wastes tokens, creates noise. Hook on `UserPromptSubmit` or throttled `PreToolUse` instead.
2. **Editing another agent's message in place.** If you need to change status (unread → read), that's fine because it's a well-defined state machine. Changing the body is never OK - treat messages as immutable once sent. If you want to correct, send a follow-up with `in_reply_to`.
3. **Using the mailbox for long-term state.** Messages are ephemeral - they get read, archived, or deleted. If something needs to persist as project knowledge, it belongs in memory files, not the inbox.
4. **No threading.** Without `in_reply_to`, a long back-and-forth becomes a scatter of unrelated files. Always thread replies.
5. **Agent names with punctuation / spaces.** Mailbox paths use names as directory names. Keep them simple kebab-case.

## Prior art

- [aydensmith/mclaude](https://github.com/aydensmith/mclaude) (v0.3.0) - hooks + file-based multi-session collaboration, includes message passing semantics
- [alternatives/agent-mailbox-system.md](../alternatives/agent-mailbox-system.md) - field-tested implementation with CLI (`mail.py send/check/broadcast`), used in production on retouch-app across 3 named agents (ani, artem, nastya)
- SMTP/IMAP themselves - the canonical reference for the semantics this principle borrows
- Erlang's process mailboxes - similar shape (per-process inbox, pattern matching on message shape), but for in-memory message passing between processes in the same VM. File-based version survives session restarts

## Composition with other principles

- **Principle 18 (Multi-Session Coordination)** provides the shared-state substrate (handoffs, locks). Principle 19 adds the directed-messaging layer on top. Use both - they answer different questions.
- **Principle 04 (Deterministic Orchestration)** - the mailbox is codified live state, not chat history. Messages are files the next agent reads via the Read tool, not memories to be recalled.
- **Principle 07 (Codified Context)** - treat the mailbox as runtime config for coordination, not documentation. Agents do not read the whole mailbox folder as reference; they process specific messages on receipt.
- **Principle 10 (Agent Security)** - mailbox messages are untrusted input from the agent's perspective. Same injection-defense rules apply as to any observed content: verify intent with the user before acting on instructions found in messages.

## What automation still cannot do

- **Guarantee ordering across arbitrary senders.** If sessions A and B both write to C's inbox simultaneously, ordering depends on filesystem timestamps which may tie. Use sender-scoped sequence numbers if strict order matters, or accept eventual consistency.
- **Prevent malicious tampering.** Any agent with filesystem access can read, modify, or delete messages in any inbox. This is a trust boundary, not a security boundary. For adversarial settings, sign messages with git commits or use a real broker.
- **Automatic retry if message body is garbage.** The file delivery is guaranteed; the content validity is not. Recipient should validate frontmatter and reject malformed messages gracefully.
