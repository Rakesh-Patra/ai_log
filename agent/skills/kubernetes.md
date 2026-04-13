# Kubernetes CLI Skill

You have access to a **shell tool** for running CLI commands. Use this skill reference
to construct correct `kubectl` and `helm` commands.

---

## kubectl Quick Reference

### Read Operations
```
kubectl get <resource> [-n <ns>] [-o wide|yaml|json] [--all-namespaces] [-l <selector>]
kubectl describe <resource> <name> [-n <ns>]
kubectl logs <pod> [-n <ns>] [-c <container>] [--tail=<N>] [--previous]
kubectl top nodes|pods [-n <ns>]
kubectl get events --sort-by=.lastTimestamp [-n <ns>] [--all-namespaces]
kubectl api-resources --verbs=list --sort-by=name
kubectl explain <resource>[.<field>]
```

### Debugging & Access
```
kubectl port-forward <pod|svc>/<name> <local_port>:<remote_port> [-n <ns>]
kubectl rollout status <resource>/<name> [-n <ns>]
kubectl auth can-i <verb> <resource> [-n <ns>]
```

### Cluster & Context
```
kubectl cluster-info
kubectl config get-contexts
kubectl config use-context <name>
kubectl get namespaces
```

### Mutating Operations (⚠️ always use --dry-run=client first)
```
kubectl apply -f <file> [-n <ns>] [--dry-run=client]
kubectl delete <resource> <name> [-n <ns>] [--dry-run=client]
kubectl scale <resource>/<name> --replicas=<N> [-n <ns>] [--dry-run=client]
kubectl rollout restart|status|undo|history <resource>/<name> [-n <ns>]
kubectl exec <pod> [-n <ns>] [-c <container>] -- <command>
```

---

## Helm Quick Reference

### Read Operations
```
helm list [-n <ns>] [--all-namespaces]
helm status <release> [-n <ns>]
helm repo list
helm history <release> [-n <ns>]
```

### Mutating Operations (⚠️ always use --dry-run first)
```
helm install <release> <chart> [-n <ns>] [--create-namespace] [-f values.yaml] [--set key=val] [--dry-run]
helm upgrade <release> <chart> [-n <ns>] [-f values.yaml] [--set key=val] [--dry-run]
helm uninstall <release> [-n <ns>] [--dry-run]
helm repo add <name> <url> && helm repo update
```

---

## Safety Rules

1. **Dry-run first** — Always run destructive commands with `--dry-run=client` (kubectl) or `--dry-run` (helm) before executing for real.
2. **Never delete** `kube-system`, `kube-public`, or `kube-node-lease` namespaces.
3. **Confirm context** — Run `kubectl config current-context` before any mutation.
4. **Explain clearly** — Tell the user what command you will run and why before executing.
5. **Format output** — Use markdown tables when listing resources.
