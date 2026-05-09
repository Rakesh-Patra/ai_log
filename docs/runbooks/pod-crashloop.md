# WHY THIS EXISTS:
# The first time you debug a production problem you spend 2 hours on it.
# If you write a runbook, the second time takes 5 minutes.

## Symptom
kubectl get pods shows STATUS = CrashLoopBackOff, RESTARTS > 3

## Why this happens (3 most common causes)
1. OOMKill: app uses more memory than limits allow → raise limits or fix memory leak
2. Bad env var: secret missing from Vault/Infisical → check ESO sync status
3. Startup probe too aggressive: readiness probe fires before app is ready → increase initialDelaySeconds

## Fix (in order of likelihood)
1. `kubectl logs <pod> --previous`  ← logs from LAST crash
2. `kubectl describe pod <pod>`     ← look for OOMKilled or Error
3. `kubectl get externalsecret -A`  ← check if ESO synced secrets
4. Increase memory limit by 50%, redeploy, watch for 10 minutes
