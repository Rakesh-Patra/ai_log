# WHY THIS EXISTS:
# NetworkPolicies are notoriously hard to debug. This saves hours of
# blind guessing.

## Symptom
Service worked yesterday. Now returns connection refused or timeout.
No code changes were deployed.

## Why this happens
A new NetworkPolicy was applied that blocks the traffic silently.
Kubernetes NetworkPolicies are deny-by-default — any policy applied to
a pod blocks all traffic not explicitly allowed.

## Debug
# Check if any policy applies to the pod:
kubectl get networkpolicy -A
kubectl describe networkpolicy <name> -n <namespace>

# Test connectivity from inside the cluster:
kubectl run debug --image=busybox -it --rm -- /bin/sh
  wget -qO- http://vote-svc:5000/health

# Check Kyverno audit for policy violations:
kubectl get policyreport -A

## Fix
Add an explicit allow rule to the NetworkPolicy for the blocked traffic.
Never delete a NetworkPolicy to fix connectivity — find the missing allow rule.
