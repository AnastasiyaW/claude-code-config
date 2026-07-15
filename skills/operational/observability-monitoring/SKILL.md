---
name: observability-monitoring
description: "Design, audit, and troubleshoot production monitoring and observability using user-impact checks, layered telemetry, USE/RED, SLI/SLO/SLA, error budgets, cardinality controls, actionable alerting, burn-rate response, and postmortems. Use when asked about monitoring, наблюдаемость, алерты, Prometheus, Grafana, OpenTelemetry, logs, traces, profiles, service health, or incident evidence. Do not use for generic dashboard styling, frontend-only UI work, or unrelated code review."
---

# Observability Monitoring

Use this skill to turn vague "is it working?" questions into evidence-backed monitoring, alerting, and incident workflows. Start from user or business impact, then move down through the system layers and choose the signal that can prove the current hypothesis.

## Operating rule

Do not treat a green dashboard as proof of health. A monitoring claim is complete only when it names:

1. the observed scope and time window;
2. the user, business, or operator outcome being protected;
3. the signal and exact query/probe that supports the claim;
4. the threshold or SLO that defines bad;
5. the next human action and its runbook/evidence link.

Keep code review, live runtime proof, UI/render proof, and release readiness as separate verdicts.

Investigation is read-only by default. A restart, alert suppression, metric-schema/label change, sampling or retention change, or vendor reconfiguration is a production mutation: involve the responsible owner or incident authority, preserve the relevant evidence first, capture the exact config/command diff, state the rollback condition, and verify the user probe plus SLI after the change.

## Workflow

### 1. Freeze scope and collect live facts

Before changing a monitor, alert, host, or service:

- Read the repository `AGENTS.md`, relevant rules, runbooks, and deployment docs.
- Establish the actual checkout/branch, deployment, process, host, port, proxy/tunnel, and data source.
- Record the observation time, environment, query/probe, and whether the result is current or historical.
- Inspect the source code/config that emits or consumes the signal before changing it.
- Never infer health from an old screenshot, a stale handoff, a single PID, or a dashboard with no successful user probe.

For infrastructure fixes, document the traffic path (DNS, proxy, tunnel, ingress, service, backend) before touching a surprising value such as `127.0.0.1`, a non-default port, or a disabled check.

### 2. Define the outcome before the metric

Write the protected outcome in concrete terms:

- **User:** can open the page, submit the request, download the result, or complete the workflow.
- **Business:** orders, successful jobs, conversions, revenue, or another domain event continue to occur.
- **Operator:** an on-call engineer receives a page early enough to act and can identify the next step.

Add at least one black-box or synthetic check for the user-facing path. Add real-user telemetry when the experience can vary by browser, geography, device, or network. Technical resource health is not a substitute for a user or business signal.

### 3. Map the monitored layers

Inspect the layers from bottom to top and state which ones are in scope:

1. **Hardware/infrastructure:** CPU, memory, disk capacity and latency, network, temperature, power, GPU, host availability.
2. **Host/OS:** load, processes, file descriptors, swap, service state, kernel/resource pressure.
3. **Network:** reachability, packet loss, latency, port state, DNS, TLS, ingress/proxy health.
4. **Application/APM:** request rate, errors, latency, saturation, dependency calls, queue depth.
5. **Databases and queues:** throughput, slow queries, connection pools, replication lag, backlog, consumer health.
6. **Containers/orchestration:** desired versus ready replicas, restarts, scheduling, evictions, resource limits, ephemeral identity.
7. **Business:** successful workflows, jobs, orders, revenue, conversion, or domain-specific zero-activity checks.

Do not stop at the infrastructure layer when the business outcome is failing. A system with green CPU and memory can still have a broken payment, form, queue consumer, or model job.

### 4. Choose the right signal

Use the signal that answers the question instead of collecting everything indiscriminately:

| Question | Primary signal | Practical method |
|---|---|---|
| Is a resource busy, queued, or failing? | Metrics | USE: utilization, saturation, errors |
| Is a service serving users correctly? | Metrics | RED: rate, errors, duration |
| What happened at a specific time? | Structured logs | Search by timestamp, service, severity, request/trace ID |
| Where did a distributed request slow or fail? | Traces | Follow the trace across services and spans |
| Why is code or a process consuming resources? | Profiles | Inspect sampled stacks, CPU, memory, locks, or I/O |
| Do users actually succeed? | Synthetic/RUM/business probes | Run the workflow and inspect the domain result |

Metrics answer aggregate **how much/how often**. Logs answer **what happened**. Traces answer **where in the path**. Profiles answer **which code or process consumed the resource**. Correlate them with stable resource identity, timestamps, and trace/request context.

### 5. Design metrics without cardinality accidents

Treat every unique metric-name plus label set as a time series. Before adding a label, estimate its possible values and lifetime.

- Good metric dimensions are bounded and useful for aggregation: method, status class/code, service, region, queue, job type, or environment.
- Keep high-cardinality or per-event values in logs/traces: user ID, request ID, email, raw URL with parameters, exception text, or arbitrary object IDs.
- Prefer route templates over raw URLs.
- Set explicit cardinality limits or views where the telemetry SDK supports them, and monitor overflow/dropped-attribute indicators.
- Prefer histograms for fleet-wide aggregatable latency SLOs. Client-side summaries/quantiles generally cannot be aggregated across instances without changing their meaning; use them only when that limitation is understood. Never hide tail latency behind an average.

If a query needs a unique ID to be useful, that ID belongs in a trace or structured log field, not in a metric label.

### 6. Define SLI, SLO, SLA, and error budget

Use the terms precisely:

- **SLI:** a measured indicator, such as successful requests divided by valid requests or p95 latency for a workflow.
- **SLO:** the internal target and time window for that indicator.
- **SLA:** an external agreement with consequences if the target is missed.
- **Error budget:** the allowed unreliability implied by the SLO during the window.

Choose the SLI from the user-facing outcome, not from whichever metric is easiest to collect. Define the valid-request population, exclusions, time window, aggregation, and owner. Treat an SLO as a control loop: remaining budget informs release pace, risk, testing, and reliability work.

### 7. Build actionable alerts

Alert on symptoms that indicate user or service pain. Use dashboards and drill-downs to investigate causes.

Every paging alert must include:

- symptom and affected scope;
- exact query, threshold, duration, and evaluation window;
- severity and owner;
- a link to the dashboard/query and runbook;
- concrete first actions, rollback criteria, and escalation path;
- a test or smoke procedure proving the alert route works.

If no immediate action exists, make it a dashboard annotation, ticket, or recording rule instead of a page. Use a pending duration (`for`) to suppress short blips. If using hysteresis, define separate fire and clear thresholds; if using multi-window evaluation, define each window and its condition. Do not confuse either control with Slack/chat routing. Treat "more than two incidents per shift" as a review heuristic, not a universal law: frequent pages mean the system or alert policy needs repair.

Prefer multi-window or burn-rate alerts for SLOs when the backend supports them. A burn rate near 1 spends the budget at the planned rate; a materially higher rate requires faster response. Verify the math against the actual SLO window and alert implementation.

### Portable examples

Adapt metric and label names to the live schema; these are patterns, not copy-paste production queries:

```promql
# RED error ratio for one service over five minutes.
sum(rate(http_requests_total{service="checkout",code=~"5.."}[5m]))
/
sum(rate(http_requests_total{service="checkout"}[5m]))

# Aggregatable fleet-wide p95 from a histogram.
histogram_quantile(0.95,
  sum by (le, service) (
    rate(http_request_duration_seconds_bucket{service="checkout"}[5m])
  )
)
```

Use a synthetic/domain probe that asserts the real outcome, not only HTTP reachability. Prefer a read-only endpoint or a sandbox/test tenant. If a write path is unavoidable, require a dry-run or idempotency key, a bounded fixture, explicit cleanup, and an owner-approved change window: `submit safe test request -> assert expected status and domain result/job ID -> record latency and trace ID -> clean up`. Never send an arbitrary representative request into production.

A burn rate is `observed error ratio / allowed error ratio`, where `allowed error ratio = 1 - SLO`. Worked example: for an SLO of 99.9% (`allowed = 0.001`), a 5-minute observed error ratio of 1.0% (`0.010`) gives burn rate `10`; if the local paging policy is the illustrative `>=10 for 5m AND >=5 for 1h`, page, otherwise route it according to the lower-severity policy. The query pattern is:

```promql
(
  sum(rate(http_request_errors_total{service="checkout"}[5m]))
  /
  sum(rate(http_requests_total{service="checkout"}[5m]))
) / 0.001
```

The thresholds and windows are examples only; derive and test them from the real SLO, traffic population, exclusions, and paging budget.

### 8. Triage in evidence order

For a live incident, follow this sequence and keep a short timeline. Apply the change-control boundary above before any mutation:

1. Confirm the user/business symptom with a fresh probe.
2. Bound blast radius: service, region, tenant, job type, version, and start time.
3. Check RED for the affected service and USE for saturated dependencies/resources.
4. Correlate logs by time, service, severity, and trace/request ID.
5. Follow a failing or slow trace to the first bad span/dependency.
6. Use a profile only when resource/code attribution remains unclear or the issue is intermittent.
7. Compare deploys, config changes, feature flags, capacity, and external dependencies.
8. Apply the smallest reversible mitigation with an explicit rollback condition.
9. Re-run the user probe and the relevant SLI query; confirm recovery over a meaningful window.
10. Record the evidence, unresolved uncertainty, and follow-up owner.

Do not restart or reconfigure a service merely because a check is red. First establish whether the check is stale, misrouted, a false positive, or a real symptom, and preserve the evidence needed to explain the decision.

### 9. Close the loop

After recovery:

- Verify the original symptom is gone, not only that the process is alive.
- Record detection time, acknowledgement, mitigation, recovery, and customer impact.
- Review alert quality: actionable, correctly routed, deduplicated, and linked to evidence.
- Write a blameless postmortem for material incidents: timeline, impact, contributing/systemic causes, what went well, what failed, and tracked prevention items.
- Update the runbook, monitor, test, or architecture so the same failure is easier to detect and diagnose next time.

## Vendor mapping

Use the actual stack discovered in the repository/runtime. Common roles from the source video are:

- Prometheus or VictoriaMetrics: scrape and store metrics;
- Grafana: visualize and query multiple sources;
- Loki or Elasticsearch/OpenSearch: logs;
- Jaeger or Tempo: traces;
- OpenTelemetry: vendor-neutral collection and export of telemetry signals;
- Mimir or Thanos: longer-term or larger-scale metric storage;
- Zabbix/Nagios: host and infrastructure checks.

Historical names in the video (ping, syslog, SNMP, MRTG/RRD, Nagios, and Cacti; 00:55-03:17) explain the evolution of monitoring and are not default deployment recommendations.

These are roles, not defaults. Do not install, replace, or reconfigure a vendor component without checking the live architecture, documentation, compatibility, retention, cost, authorization, and rollback path.

## Minimal runbook template

Use this shape for every new page:

```text
Name:
User symptom:
SLI/query:
Trigger and duration:
Scope labels:
Severity/owner:
Dashboard and raw query:
First safe action:
Rollback condition:
Verification probe:
Escalation:
Known false positives:
Last tested:
```

## Gotchas

- A host can be healthy while the business workflow is broken.
- Averages hide tail latency; inspect percentiles and failed requests.
- A metric label creates a new series for every unique combination; raw URLs and IDs can exhaust memory.
- A trace without stable service/resource context is hard to correlate; a log without timestamps or IDs is weak evidence.
- A page without a concrete action trains the operator to ignore pages.
- A synthetics-only check misses real-user variance; RUM-only telemetry can discover pain too late.
- Profiles are an attribution signal, not a replacement for service-level metrics, logs, or traces.
- An SLO target is not an SLA promise unless an external contract says so.
- Auto-generated captions and copied vendor names can be wrong; verify terms before putting them into code or runbooks. See `references/source-notes.md`.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Dashboard is green but users fail | Missing black-box/business SLI, wrong route, or stale data source | Run a fresh user probe, verify timestamps/labels, add the missing outcome signal |
| One deploy creates a huge series spike | High-cardinality label or unbounded route/ID | Remove the label from metrics, normalize routes, move detail to logs/traces, cap SDK cardinality |
| Alert fires but nobody acts | Alert is a cause guess, too sensitive, unowned, or lacks a runbook | Alert on a user symptom, add owner/action/query/runbook, add `for`; if using hysteresis define separate fire/clear thresholds, and if using multi-window define each condition; test delivery |
| Error rate rises but cause is unclear | Logs are unstructured or traces are not correlated | Add structured fields and trace IDs, sample a failing trace, inspect dependency spans |
| Service is slow but RED looks normal | Low traffic, bad aggregation, or resource contention outside the app | Check synthetic latency, USE for host/queue/storage, tail percentiles, and profiles |
| Dashboard is blank or stale | Target/scrape/exporter/collector/backend failure, retention gap, or clock skew | Check last-sample time, target and collector health, dropped/ingestion counters, retention, and time synchronization; do not interpret blank as zero |
| A query shows zero but the system may be uninstrumented | The series is absent, filtered out, or genuinely zero | Test absent-series semantics, inspect raw labels and last sample, and add an explicit freshness/telemetry-health check |
| Trace is incomplete | Sampling, context propagation, collector drops, or backend retention | Check trace ID propagation, sampling decision, collector drop counters, backend ingestion, and clock synchronization |
| Page storm during one incident | No grouping/deduplication or too many low-value alerts | Group by incident/service, keep one page for the symptom, demote diagnostic signals |
| Burn-rate alert disagrees with the dashboard | Different SLI population, window, exclusions, or recording rule | Reconcile the numerator/denominator, window, and query; test against known scenarios |
| Restart appears to fix it but it returns | Mitigation hid a systemic cause or destroyed evidence | Capture logs/metrics first, record the restart, identify the recurring trigger, add prevention |

## Source and current-practice notes

The reusable concepts in this skill were extracted from the supplied video and cross-checked against current primary documentation. See `references/source-notes.md` for the source URL, timestamp map, caption corrections, and official references.
