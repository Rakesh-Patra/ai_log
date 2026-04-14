kubectl exec vault-0 -- sh -c "vault auth enable kubernetes || true"
kubectl exec vault-0 -- sh -c 'vault write auth/kubernetes/config kubernetes_host=https://$KUBERNETES_SERVICE_HOST:$KUBERNETES_SERVICE_PORT'
kubectl exec vault-0 -- sh -c 'echo "path \"secret/data/db-credentials\" { capabilities = [\"read\"] } path \"secret/data/redis-credentials\" { capabilities = [\"read\"] }" > /tmp/app-policy.hcl && vault policy write app-policy /tmp/app-policy.hcl'
kubectl exec vault-0 -- sh -c 'vault write auth/kubernetes/role/app-role bound_service_account_names=voting-app bound_service_account_namespaces=default policies=app-policy ttl=24h'
