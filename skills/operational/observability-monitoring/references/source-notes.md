# Source notes

## Supplied video

- Title: `Все, что нужно знать про мониторинг`
- Author: `Просто Devops`
- URL: https://www.youtube.com/watch?v=7uw3fCT6vvs
- Duration: 20:30
- Published: 2026-07-12
- Local evidence directory: `.tmp/video-analysis/monitoring-7uw3fCT6vvs`
- MP4: `.tmp/video-analysis/monitoring-7uw3fCT6vvs/7uw3fCT6vvs.mp4` — SHA-256 `CD06E72A6A1778FBEA8C0F38B9EC8D73D550A9294199B75D04C80978326C8E8F`
- Captions: `.tmp/video-analysis/monitoring-7uw3fCT6vvs/7uw3fCT6vvs.ru.vtt` — SHA-256 `4B0FF61A2F3C3349B86723039C4FD78447B2A958EC2271400BDCE05A7ACC48E3`
- Cleaned transcript: `.tmp/video-analysis/monitoring-7uw3fCT6vvs/transcript-cleaned.md` — SHA-256 `9DD5ABB665DF15EB5C95441F60ABB5AC84617092F2E6142A8973E0862DE0FE45`
- Extraction tools: `yt-dlp 2026.07.04`, `ffmpeg 8.1.2`, `Python 3.14.5`; VTT cleanup used the adjacent `parse_vtt.py` script.

The local transcript is YouTube automatic Russian caption output, cleaned mechanically from VTT overlap. It is a source aid, not an authoritative technical specification.

## Topic map

| Video time | Extracted concept |
|---|---|
| 00:00-00:48 | Monitoring detects failure before the user; monitoring is more than graphs |
| 00:55-03:17 | Host/infrastructure history; ping, syslog, SNMP, MRTG/RRD, Nagios/Cacti; USE |
| 04:16-06:22 | Monitoring layers, business metrics, synthetic checks, RUM |
| 06:22-09:05 | Containers/microservices; Prometheus pull/scrape, labels, TSDB, Grafana; RED |
| 09:05-12:00 | Metrics, logs, traces; OpenTelemetry as vendor-neutral transport/context |
| 12:06-13:42 | Continuous profiling, eBPF, attribution beyond application telemetry |
| 13:42-15:00 | Cardinality and why IDs/raw URLs do not belong in metric labels |
| 15:05-16:34 | SLI, SLO, SLA, error budgets |
| 16:41-18:37 | Alert fatigue, actionable pages, incident-rate heuristic, burn rate, postmortems |
| 18:40-20:18 | Example stack: Prometheus/VictoriaMetrics, Grafana, logs, traces, all-in-one vendors |

The platform promotion around 03:18-04:13 is not included in the operational guidance.

## Caption corrections used in the skill

The auto-captions contain predictable technical transcription errors. The skill normalizes these terms before using them in procedures:

- `Пинк` -> `ping`
- `CS` -> `syslog`
- `Нагиос` / `Какти` -> `Nagios` / `Cacti`
- `use` / `з` / `utilizли` / `saturation` / `ирс` -> `USE` / `Utilization` / `Saturation` / `Errors`
- `RAM` -> `RUM` (Real User Monitoring)
- `Промете` / `Прометеус` / `среп` -> `Prometheus` / `scrape`
- `endpите/matrix` -> HTTP endpoint `/metrics`
- `рейд` / `duration` -> `Rate` / `Duration` in RED
- `Open Temметри` -> `OpenTelemetry`
- `EBPF` -> `eBPF`
- `Zabкс` -> `Zabbix`

## Current-practice checks

The topic map and operational principles above are video-derived. The following current-practice safeguards are enrichment checked against primary documentation on 2026-07-13:

- Prometheus data model: https://prometheus.io/docs/concepts/
- Prometheus alerting guidance: https://prometheus.io/docs/practices/alerting/
- Prometheus label naming/cardinality warning: https://prometheus.io/docs/practices/naming/
- OpenTelemetry signals: https://opentelemetry.io/docs/concepts/signals/
- OpenTelemetry metrics and cardinality limits: https://opentelemetry.io/docs/concepts/signals/metrics/
- OpenTelemetry profiles specification: https://opentelemetry.io/docs/specs/otel/profiles/
- Google SRE error budgets and risk: https://sre.google/sre-book/embracing-risk/

Important nuance: OpenTelemetry currently describes profiles as under development, and the profiles specification is Alpha. Treat profiling as an optional attribution signal and verify backend/agent support before making it a production dependency.
