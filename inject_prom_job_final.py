import yaml
import sys

cm_path = 'k8s/prometheus-cm-backup.yaml'
try:
    with open(cm_path, 'r', encoding='utf-16') as f:
        content = f.read()
except:
    with open(cm_path, 'r', encoding='utf-8') as f:
        content = f.read()

cm = yaml.safe_load(content)
prom_conf = yaml.safe_load(cm['data']['prometheus.yml'])

# Find the kubernetes-pods job
for job in prom_conf['scrape_configs']:
    if job['job_name'] == 'kubernetes-pods':
        # Add a relabel rule to set job="node-exporter" for node-exporter pods
        relabel_rule = {
            'action': 'replace',
            'regex': 'prometheus-node-exporter',
            'source_labels': ['__meta_kubernetes_pod_label_app_kubernetes_io_name'],
            'target_label': 'job',
            'replacement': 'node-exporter'
        }
        # Insert at the beginning of relabel_configs
        if 'relabel_configs' not in job:
            job['relabel_configs'] = []
        
        # Check if already exists
        if not any(r.get('replacement') == 'node-exporter' for r in job['relabel_configs']):
            job['relabel_configs'].insert(0, relabel_rule)

cm['data']['prometheus.yml'] = yaml.dump(prom_conf)

with open('k8s/prometheus-cm-final.yaml', 'w', encoding='utf-8') as f:
    yaml.dump(cm, f)
