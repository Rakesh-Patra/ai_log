# vault-fix.ps1 - Complete Vault Kubernetes Auth Fix for Kind Cluster
# This script properly configures Vault auth with explicit CA + JWT from a long-lived token

Write-Host "=== Step 1: Extract CA cert and JWT from vault-reviewer-token secret ===" -ForegroundColor Cyan

# Get base64-encoded values
$CA_B64 = kubectl get secret vault-reviewer-token -o jsonpath="{.data.ca\.crt}"
$JWT_B64 = kubectl get secret vault-reviewer-token -o jsonpath="{.data.token}"

# Decode JWT to plain text (Vault needs the raw JWT, not base64)
$JWT = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($JWT_B64))

Write-Host "  CA cert length (base64): $($CA_B64.Length)"
Write-Host "  JWT length (decoded): $($JWT.Length)"

Write-Host "`n=== Step 2: Disable and re-enable Kubernetes auth in Vault ===" -ForegroundColor Cyan
kubectl exec vault-0 -- sh -c 'vault auth disable kubernetes 2>/dev/null; vault auth enable kubernetes'

Write-Host "`n=== Step 3: Configure Kubernetes auth with explicit token_reviewer_jwt and CA ===" -ForegroundColor Cyan
# Write the CA cert to a temp file inside the vault pod, then use it
kubectl exec vault-0 -- sh -c "echo '$CA_B64' | base64 -d > /tmp/k8s-ca.crt"

kubectl exec vault-0 -- sh -c "vault write auth/kubernetes/config kubernetes_host='https://kubernetes.default.svc:443' token_reviewer_jwt='$JWT' kubernetes_ca_cert=@/tmp/k8s-ca.crt disable_iss_validation=true"

Write-Host "`n=== Step 4: Re-create the policy ===" -ForegroundColor Cyan
kubectl exec vault-0 -- sh -c 'vault policy write app-policy - <<EOF
path "secret/data/db-credentials" {
  capabilities = ["read"]
}
path "secret/data/redis-credentials" {
  capabilities = ["read"]
}
EOF'

Write-Host "`n=== Step 5: Re-create the role (no audience restriction) ===" -ForegroundColor Cyan
kubectl exec vault-0 -- sh -c 'vault write auth/kubernetes/role/app-role bound_service_account_names=default bound_service_account_namespaces=default policies=app-policy ttl=24h'

Write-Host "`n=== Step 6: Verify secrets exist ===" -ForegroundColor Cyan
kubectl exec vault-0 -- sh -c 'vault kv get secret/db-credentials'
kubectl exec vault-0 -- sh -c 'vault kv get secret/redis-credentials'

Write-Host "`n=== Step 7: Read back auth config to verify ===" -ForegroundColor Cyan
kubectl exec vault-0 -- sh -c 'vault read auth/kubernetes/config'

Write-Host "`n=== Done! Now restart db and redis pods ===" -ForegroundColor Green
