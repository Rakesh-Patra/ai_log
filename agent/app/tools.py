# WHY THIS EXISTS:
# The AI Agent is "blind" without tools. In a real-world incident, an SRE 
# first looks at logs and events. These tools provide the agent with the
# "eyes" and "hands" needed to triage and remediate issues autonomously, 
# reducing Mean Time To Resolution (MTTR) from hours to seconds.

import subprocess
import requests
import json
import os
from datetime import datetime, timedelta
from langchain.tools import tool

# Configuration
LOKI_URL = os.getenv("LOKI_URL", "http://loki.monitoring.svc:3100")
PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://prometheus.monitoring.svc:9090")

@tool
def query_loki_logs(pod_name: str, namespace: str = "default"):
    """
    WHY THIS EXISTS:
    Without log access, the agent cannot see stack traces or application errors.
    Loki provides a centralized way to query logs without SSHing into pods.
    """
    query = f'{{pod="{pod_name}", namespace="{namespace}"}}'
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(minutes=15)
    
    params = {
        'query': query,
        'limit': 50,
        'start': int(start_time.timestamp() * 1e9),
        'end': int(end_time.timestamp() * 1e9),
        'direction': 'backward'
    }
    
    try:
        response = requests.get(f"{LOKI_URL}/loki/api/v1/query_range", params=params, timeout=10)
        response.raise_for_status()
        results = response.json().get('data', {}).get('result', [])
        
        logs = []
        for res in results:
            for val in res.get('values', []):
                logs.append(val[1])
        
        return "\n".join(logs) if logs else "No logs found for the specified pod/namespace."
    except Exception as e:
        return f"Error querying Loki: {str(e)}"

@tool
def get_k8s_events(namespace: str = "default"):
    """
    WHY THIS EXISTS:
    Kubernetes events are the first place to look for OOMKills, Node failures,
    or ImagePullBackOffs. This provides the 'Cluster Context' to the agent.
    """
    try:
        cmd = ["kubectl", "get", "events", "-n", namespace, "--sort-by=.metadata.creationTimestamp", "-o", "json"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        
        if result.returncode != 0:
            return f"Error fetching events: {result.stderr}"
            
        events = json.loads(result.stdout).get('items', [])
        summary = []
        for e in events[-10:]:  # Last 10 events
            summary.append(f"[{e['lastTimestamp']}] {e['reason']}: {e['message']}")
            
        return "\n".join(summary) if summary else "No recent events found."
    except Exception as e:
        return f"Unexpected error: {str(e)}"

@tool
def get_namespace_utilization(namespace: str):
    """
    WHY THIS EXISTS:
    FinOps requires knowing if resources are actually being used. 
    This tool queries Prometheus to find idle workloads that are prime 
    candidates for scaling down to zero during off-hours.
    """
    # Simple CPU usage query: sum of cpu usage per namespace
    query = f'sum(node_namespace_pod_container:container_cpu_usage_seconds_total:sum_irate{{namespace="{namespace}"}})'
    
    try:
        response = requests.get(f"{PROMETHEUS_URL}/api/v1/query", params={'query': query}, timeout=10)
        response.raise_for_status()
        data = response.json().get('data', {}).get('result', [])
        
        if not data:
            return f"No utilization data found for namespace: {namespace}"
            
        usage = data[0]['value'][1]
        return f"Current CPU Utilization for namespace '{namespace}': {usage} cores. (Values near 0 indicate idle environment)"
    except Exception as e:
        return f"Error querying Prometheus: {str(e)}"

@tool
def execute_k8s_action(action: str, resource_type: str, resource_name: str, namespace: str = "default", replicas: int = None):
    """
    WHY THIS EXISTS:
    Autonomous SRE requires the ability to fix things. 
    This tool allows safe actions like scaling and restarting, enabling the 
    agent to execute FinOps scale-downs or SRE remediations.
    
    RESTRICTIONS: 
    - Scale-down to 0 is ONLY allowed for non-critical namespaces.
    - Critical namespaces (kube-system, vault, monitoring) are PROTECTED.
    """
    PROTECTED_NAMESPACES = ["kube-system", "vault", "monitoring"]
    ALLOWED_ACTIONS = ["scale", "rollout restart"]
    
    if namespace in PROTECTED_NAMESPACES:
        return f"CRITICAL SECURITY ALERT: Action '{action}' denied on protected namespace '{namespace}'."
        
    if action not in ALLOWED_ACTIONS:
        return f"Action '{action}' is not permitted. Only 'scale' and 'rollout restart' are allowed."

    try:
        if action == "scale":
            if replicas is None:
                return "Error: replicas must be specified for scale action."
            cmd = ["kubectl", "scale", f"{resource_type}/{resource_name}", "--replicas", str(replicas), "-n", namespace]
        else: # rollout restart
            cmd = ["kubectl", "rollout", "restart", f"{resource_type}/{resource_name}", "-n", namespace]
            
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        
        if result.returncode != 0:
            return f"Failed to execute {action}: {result.stderr}"
            
        return f"Successfully executed {action} on {resource_type}/{resource_name} in {namespace}."
    except Exception as e:
        return f"Unexpected error during k8s action: {str(e)}"

@tool
def get_kubecost_metrics(namespace: str):
    """
    WHY THIS EXISTS:
    This tool allows the agent to see the actual financial cost of a 
    namespace. It bridges the gap between 'CPU metrics' and 'Budget impact'.
    Returns cost in USD per day for the specified namespace.
    """
    KUBECOST_URL = "http://kubecost-cost-analyzer.kubecost.svc:9090"
    endpoint = f"{KUBECOST_URL}/model/allocation"
    params = {
        'window': '1h',
        'aggregate': 'namespace',
        'accumulate': 'true'
    }
    
    try:
        response = requests.get(endpoint, params=params, timeout=10)
        response.raise_for_status()
        data = response.json().get('data', [])
        
        # Parse the JSON for the specific namespace
        namespace_data = next((item for item in data if item.get('name') == namespace), None)
        
        if not namespace_data:
            return f"No cost data found for namespace: {namespace} (Kubecost may still be gathering data)"
            
        cost = namespace_data.get('totalCost', 0)
        return f"The current cost for namespace '{namespace}' is ${round(cost, 4)} per hour. (Annualized: ${round(cost * 24 * 365, 2)}/year)"
    except Exception as e:
        return f"Error querying Kubecost: {str(e)}"

