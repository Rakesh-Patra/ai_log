# How to search logs in production (Loki + LogQL)

## WHY THIS EXISTS:
# Without log search, debugging a production issue means SSH-ing
# into the pod, which is slow, lossy, and unavailable after a crash.
# Logs are the ultimate source of truth when metrics show an anomaly.

## Common queries
| What you want | LogQL |
|---|---|
| All errors in vote service | `{app="vote"} |= "error"` |
| Agent exceptions last 1h | `{app="agent"} |= "Exception"` |
| High log volume (noise) | `topk(5, sum by (app) (rate({namespace="default"}[5m])))` |
| Logs around an incident time | `{app="worker"} |= "failed"` then set time range |
