# DevOps usage example (Vault + Gateway API)

This repo runs the voting app on Kubernetes. Secrets are stored in **Vault** and injected into pods, and HTTP traffic is routed via **Gateway API** (Envoy Gateway).

## Prereqs

- `kubectl` configured to point at your cluster
- A Gateway API controller installed (this repo uses **Envoy Gateway**)
- Vault + Vault Agent Injector installed in the cluster

## 1) Vault: store application secrets

### What we store

- **DB** creds in: `secret/data/db-credentials`
  - keys: `username`, `password`
- **Redis** password in: `secret/data/redis-credentials`
  - key: `password`

### Create/update secrets (example)

Run these against the Vault pod:

```bash
kubectl exec vault-0 -- sh -c 'vault secrets enable -path=secret kv-v2 || true'

kubectl exec vault-0 -- sh -c 'vault kv put secret/data/db-credentials username=postgres password=postgres'
kubectl exec vault-0 -- sh -c 'vault kv put secret/data/redis-credentials password=redispass'
```

### Policy + role (who can read)

This project uses Kubernetes auth with:

- **Policy**: `app-policy` (read only the two paths)
- **Role**: `app-role` bound to `default` ServiceAccount in `default` namespace

If you re-create it:

```bash
kubectl exec vault-0 -- sh -c 'vault auth enable kubernetes || true'
kubectl exec vault-0 -- sh -c 'vault write auth/kubernetes/config kubernetes_host="https://$KUBERNETES_SERVICE_HOST:$KUBERNETES_SERVICE_PORT"'

kubectl exec vault-0 -- sh -c 'vault policy write app-policy - <<EOF
path "secret/data/db-credentials" { capabilities = ["read"] }
path "secret/data/redis-credentials" { capabilities = ["read"] }
EOF'

kubectl exec vault-0 -- sh -c 'vault write auth/kubernetes/role/app-role \
  bound_service_account_names=default \
  bound_service_account_namespaces=default \
  policies=app-policy \
  ttl=24h'
```

### How apps consume secrets (injector)

`k8s/db-deployment.yaml` and `k8s/redis-deployment.yaml` use `vault.hashicorp.com/*` annotations.

- Vault Injector writes files like:
  - `/vault/secrets/db-credentials`
  - `/vault/secrets/redis-credentials`
- Containers `source` those files before starting.

If you add a new secret, you typically:

- add a new `vault.hashicorp.com/agent-inject-secret-...` annotation
- add a matching `vault.hashicorp.com/agent-inject-template-...` template
- update the command/args to `source` the rendered file (or read it directly)
- update the Vault policy to allow reading the new path

### Rotation (example)

To rotate DB password:

```bash
kubectl exec vault-0 -- sh -c 'vault kv put secret/data/db-credentials username=postgres password=NEW_PASSWORD'
kubectl rollout restart deploy/db
```

## 2) Gateway API: expose Vote + Result

`k8s/gateway.yaml` defines:

- `GatewayClass` named `eg` (Envoy Gateway controller)
- `Gateway` named `voting-gateway`
- `HTTPRoute` for:
  - `/` and `/vote` → service `vote:5000` (with URL rewrite for `/vote`)
  - `/result` → service `result:5001` (with URL rewrite for `/result`)

Apply it:

```bash
kubectl apply -f k8s/gateway.yaml
```

### Access on kind (important)

On kind, the Gateway service may show `EXTERNAL-IP: <pending>` because it’s a `LoadBalancer` type without a cloud load balancer.

Use either:

- **port-forward**:

```bash
kubectl port-forward -n envoy-gateway-system svc/envoy-default-voting-gateway-bef65586 8080:80
```

Then open:

- `http://127.0.0.1:8080/` (vote)
- `http://127.0.0.1:8080/result` (result)

## 3) What we removed (old approach)

Previously, developers could create Kubernetes `Secret` YAMLs for DB/Redis (example templates still exist).
Now, DB/Redis credentials are sourced from Vault, so the real `k8s/db-secret.yaml` and `k8s/redis-secret.yaml` are intentionally not used.

## Minimal dev-safety hardening used here

- The app runs with a dedicated ServiceAccount: `voting-app`
- Vault Kubernetes auth role `app-role` is bound to `voting-app` (not the `default` ServiceAccount)

