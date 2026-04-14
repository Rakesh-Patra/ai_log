#!/bin/bash

echo "Waiting for Vault pod to be ready..."
kubectl wait --for=condition=Ready pod/vault-0 --timeout=90s

echo "Configuring Vault..."
kubectl exec vault-0 -- sh -c '
  # Enable KV secrets engine
  vault secrets enable -path=secret kv-v2 || true
  
  # Add DB secrets
  vault kv put secret/data/db-credentials username=postgres password=postgres
  
  # Add Redis secrets
  vault kv put secret/data/redis-credentials password=redispass
  
  # Enable K8s auth
  vault auth enable kubernetes || true
  
  # Configure K8s auth
  vault write auth/kubernetes/config \
    kubernetes_host="https://$KUBERNETES_SERVICE_HOST:$KUBERNETES_SERVICE_PORT"

  # Create policy
  vault policy write app-policy - <<EOF
path "secret/data/db-credentials" {
  capabilities = ["read"]
}
path "secret/data/redis-credentials" {
  capabilities = ["read"]
}
EOF

  # Create role bound to the voting-app service account in the default namespace
  vault write auth/kubernetes/role/app-role \
    bound_service_account_names=voting-app \
    bound_service_account_namespaces=default \
    policies=app-policy \
    ttl=24h
'

echo "Vault setup complete!"
