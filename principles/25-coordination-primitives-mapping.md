# 25 - Coordination Primitives: Map to Classical Distributed Systems

When you build coordination for AI agents, you are not inventing new
primitives. You are re-deriving the same primitives that distributed
systems literature has documented for forty years. This is not bad - it
is good. The classical primitives have well-understood failure modes,
and naming the analog tells you exactly when your implementation works
and when it does not.

## The principle

Before designing any coordination layer (locks, queues, handoffs,
messaging, leases), find its classical analog and read the failure
mode discussion. Then ask: **does my deployment topology fall inside
the analog's working scope?** If not, do not retrofit the analog -
pick a different primitive.

This is the cheapest form of defensive engineering. A name that maps
to literature pulls thirty years of operator experience into your
design review.

## The mapping (file-based agent coordination)

| Agent-coordination primitive | Classical analog | Defining work |
|---|---|---|
| Atomic claim via `O_CREAT \| O_EXCL` + heartbeat | Chubby session lease | Burrows 2006 |
| Append-only INDEX of work / handoffs | Write-Ahead Log (WAL) | Database systems 1970s+ |
| Per-folder mailbox with YAML envelope | SMTP / RFC 822 | Crocker 1982 |
| Heartbeat refresh + stale detection | Lease renewal | Gray & Cheriton 1989 |
| Per-session structured handoff file | 2-Phase Commit log | Lampson & Sturgis 1979 |
| Hierarchical knowledge graph (Wings/Rooms) | Wiki / hierarchical KB | Engelbart 1968+ |
| Atomic file write (tmp + fsync + rename) | Crash-safe replacement | POSIX rename(2) |
| Pre-commit guard for lock leaks | Advisory lock leak detection | git hook conventions |

## Why this matters for agent systems

When CoAlly Nexus reviewed mclaude they wrote: "переизобрели
Chubby/ZooKeeper на файлах. И это комплимент, не критика." That framing
is the most useful technical response possible. It tells potential users:

1. **Failure modes are well-known.** Chubby loses correctness on
   network filesystems with stale caches. Therefore your agent locks
   on shared NFS mounts will lose correctness too. Read Burrows 2006.
2. **Scope is single-cluster.** Chubby was designed for a single Google
   cluster, not WAN. Your file-based locks have the same scope.
3. **Accelerator stories are proven.** Chubby has a master + slaves
   for HA. Your equivalent is the optional Hub server with file
   fallback - same pattern, smaller scale.

The corollary: **do not market "we work everywhere across all IDEs and
machines"** if your primitive is `O_CREAT | O_EXCL`. Mark scope
explicitly. Send users with broader scope to a network coordinator.

## How to apply

When designing an agent coordination feature:

1. **Name the primitive.** Lock? Lease? Log? Mailbox? Memory?
2. **Find the classical analog.** One sentence: "this is X, like Chubby
   leases."
3. **Read the failure mode for the analog.** Spend 30 minutes on the
   defining paper. You do not need to understand all of it - you need
   to understand where it breaks.
4. **Document the scope.** "Works on single POSIX FS. Does not work on
   NFS with multiple writers." Be explicit, not aspirational.
5. **Point users with out-of-scope deployments to the right tool.**
   "If you need cross-machine real-time, use Redis / etcd / a managed
   service like CoAlly." Honesty here builds trust; vagueness here
   ships bugs.

## Anti-patterns

- **Inventing a primitive without naming the analog.** "Our novel
  coordination layer..." If you cannot name the analog, you have
  probably re-derived a known broken pattern.
- **Claiming general purpose when scope is narrow.** "Works in any
  deployment" usually means "we have not tested NFS, SMB, S3, or
  multi-region."
- **Marketing the wrong primitive.** Treating a Chubby-class file lock
  as a Paxos consensus is a recipe for production incidents.
- **Skipping the failure mode read.** The classical paper documents
  exactly what breaks. Skipping it = re-discovering it in production.

## Real example

mclaude (file-based coordination for parallel Claude Code sessions)
explicitly maps each primitive to its analog in
`docs/coordination-primitives.md`. README scope: "single POSIX FS,
three deployment topologies (one machine, shared SSH server, git as
async transport)." Where it does not work: NFS/SMB multi-writer,
real-time cross-machine. Users with that scope are pointed to CoAlly
Nexus or similar network coordinators.

This explicit scope statement, combined with the analog mapping, has
been the most useful documentation in mclaude for both contributors
(who can reason about edge cases by analogy) and reviewers (who can
quickly assess whether mclaude is the right tool).

## References

- Burrows, M. (2006). The Chubby lock service for loosely-coupled
  distributed systems. OSDI'06. - the canonical paper for file-like
  lock services.
- Crocker, D. (1982). RFC 822 - email message format and async
  delivery semantics.
- Gray, C. & Cheriton, D. (1989). Leases. SOSP'89 - heartbeat /
  lease renewal semantics.
- Lampson & Sturgis (1979). Crash Recovery - foundational 2PC paper.
- POSIX rename(2) - atomicity guarantee for same-filesystem rename.
