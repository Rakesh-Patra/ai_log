# WHY THIS EXISTS:
# Disk full issues cause database corruption and silent data loss.
# Resolving this quickly prevents downtime.

## Symptom
PVCAlmostFull alert fires. Pod may be evicted.

## Why this happens
PostgreSQL data grows. Logs accumulate. No cleanup policy.

## Fix
# Expand the PVC (AWS EBS supports online expansion):
kubectl patch pvc postgres-data -p '{"spec":{"resources":{"requests":{"storage":"40Gi"}}}}'
# EBS resizes online — no downtime on K3s with EBS CSI driver

## Clean old data (if expansion not possible)
kubectl exec -it postgres-pod -- psql -U postgres
DELETE FROM votes WHERE created_at < NOW() - INTERVAL '90 days';
VACUUM ANALYZE;

## Prevention
Add PVC size monitoring to `prometheus-rules.yaml` (already done in Phase 2A)
