# WHY THIS EXISTS:
# Image pull failures are often silent until a pod restart causes an outage.
# This runbook explains how to quickly resolve ECR credential expiration.

## Symptom
STATUS = ImagePullBackOff or ErrImagePull

## Why this happens
1. ECR token expired (tokens last 12h — pull secret must be refreshed)
2. Image digest changed but deployment not updated
3. Wrong registry URL (typo in image: field)

## Fix
# Refresh ECR pull secret (most common fix):
aws ecr get-login-password --region ap-south-1 \
  | kubectl create secret docker-registry ecr-secret \
    --docker-server=<account>.dkr.ecr.ap-south-1.amazonaws.com \
    --docker-username=AWS --docker-password=stdin \
    --dry-run=client -o yaml | kubectl apply -f -

## Prevention
Add a CronJob that refreshes the ECR pull secret every 6 hours.
See `k8s/utils/ecr-token-refresh-cronjob.yaml`
