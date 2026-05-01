import yaml
import sys

cm_path = 'k8s/prometheus-cm-backup.yaml'
# Use utf-16 to read if it was saved by powershell redirect, or try utf-8
try:
    with open(cm_path, 'r', encoding='utf-16') as f:
        content = f.read()
except:
    with open(cm_path, 'r', encoding='utf-8') as f:
        content = f.read()

cm = yaml.safe_load(content)

prom_conf = yaml.safe_load(cm['data']['prometheus.yml'])

new_job = {
    'job_name': 'node-exporter',
    'static_configs': [
        {
            'targets': ['node-exporter-prometheus-node-exporter.voting-monitoring.svc.cluster.local:9100']
        }
    ]
}

# Check if it already exists
if not any(j['job_name'] == 'node-exporter' for j in prom_conf['scrape_configs']):
    prom_conf['scrape_configs'].append(new_job)

cm['data']['prometheus.yml'] = yaml.dump(prom_conf)

with open('k8s/prometheus-cm-new.yaml', 'w', encoding='utf-8') as f:
    yaml.dump(cm, f)
