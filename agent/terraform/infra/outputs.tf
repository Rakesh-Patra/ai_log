# ════════════════════════════════════════════════════════════
# outputs.tf — K3s Server Details
# ════════════════════════════════════════════════════════════

output "k3s_public_ip" {
  description = "Public IP of the K3s node"
  value       = aws_instance.k3s.public_ip
}

output "k3s_instance_id" {
  description = "Instance ID of the K3s node"
  value       = aws_instance.k3s.id
}

output "kubeconfig_command" {
  description = "Command to download the kubeconfig securely using AWS SSM"
  value       = <<-EOT
    # Wait ~2 minutes after applying for K3s to finish installing, then run:
    # SECURITY: kubeconfig contains credentials. Keep it OUT of git and treat it as a secret.
    mkdir -p kubeconfig_agent
    aws ssm send-command --document-name "AWS-RunShellScript" --targets "Key=instanceids,Values=${aws_instance.k3s.id}" --parameters 'commands=["cat /home/ubuntu/.kubeconfig"]' --comment "Get Kubeconfig" --output text --query "CommandInvocations[0].CommandPlugins[0].Output" > kubeconfig_agent/k3s-kubeconfig.yaml
    
    # Then export it so kubectl uses it:
    $env:KUBECONFIG="$(Get-Location)\kubeconfig_agent\k3s-kubeconfig.yaml"
    kubectl get nodes
  EOT
}
