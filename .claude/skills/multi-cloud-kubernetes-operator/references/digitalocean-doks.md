# DigitalOcean Kubernetes (DOKS) Reference

## Overview
DigitalOcean Kubernetes Service provides managed Kubernetes clusters with the easiest setup among budget providers. Best for hackathon projects that prioritize speed over cost.

**Pricing (as of 2026-02-05):**
- Minimum: ~$12/month for smallest node pool (1 node, s-1vcpu-2gb)
- Free tier: $200 credit for new accounts (60 days)
- Best for: Fastest setup, managed experience

## Prerequisites

### Install doctl
```bash
# macOS
brew install doctl

# Linux (snap)
sudo snap install doctl

# Linux (direct download)
cd ~
wget https://github.com/digitalocean/doctl/releases/download/v1.104.0/doctl-1.104.0-linux-amd64.tar.gz
tar xf doctl-1.104.0-linux-amd64.tar.gz
sudo mv doctl /usr/local/bin
```

### Authentication
```bash
# Interactive authentication (creates ~/.config/doctl/config.yaml)
doctl auth init
# When prompted, paste your DigitalOcean API token
# Get token from: https://cloud.digitalocean.com/account/api/tokens

# Verify authentication
doctl account get

# For CI/CD or scripts
export DIGITALOCEAN_ACCESS_TOKEN=dop_v1_your_api_token_here
doctl account get
```

## Quick Start Workflow

### 1. Create Cluster (Minimal Cost)
```bash
# Smallest cluster for hackathons ($12/month)
doctl kubernetes cluster create hackathon-cluster \
  --region nyc1 \
  --version 1.28.2-do.0 \
  --node-pool "name=worker-pool;size=s-1vcpu-2gb;count=1" \
  --wait

# Output shows cluster ID, name, region, status
# Credentials automatically added to ~/.kube/config
```

### 2. Get Kubeconfig
```bash
# Save cluster credentials (already done if using --wait above)
doctl kubernetes cluster kubeconfig save hackathon-cluster

# Show kubeconfig YAML
doctl kubernetes cluster kubeconfig show hackathon-cluster
```

### 3. Verify Cluster
```bash
kubectl get nodes
# Should show 1 node in Ready state

kubectl cluster-info
```

### 4. Deploy Application
```bash
# Example: Deploy nginx
kubectl create deployment nginx --image=nginx:latest
kubectl expose deployment nginx --port=80 --type=LoadBalancer

# Get external IP (may take 1-2 minutes)
kubectl get svc nginx --watch
```

### 5. TEARDOWN (IMPORTANT)
```bash
# ⚠️ Delete cluster to stop charges
doctl kubernetes cluster delete hackathon-cluster --force

# Verify deletion
doctl kubernetes cluster list

# Remove from kubeconfig
doctl kubernetes cluster kubeconfig remove hackathon-cluster
```

## Cluster Configuration Options

### Recommended Hackathon Sizes
```bash
# Ultra-minimal ($12/month) - Single small node
--node-pool "name=workers;size=s-1vcpu-2gb;count=1"

# Budget ($24/month) - Two small nodes for HA
--node-pool "name=workers;size=s-1vcpu-2gb;count=2"

# Moderate ($48/month) - Two medium nodes
--node-pool "name=workers;size=s-2vcpu-4gb;count=2"
```

### Available Regions
```bash
# List regions
doctl kubernetes options regions

# Common regions:
# nyc1, nyc3 (New York)
# sfo3 (San Francisco)
# ams3 (Amsterdam)
# sgp1 (Singapore)
# lon1 (London)
```

### Available Versions
```bash
# List available Kubernetes versions
doctl kubernetes options versions
```

### Node Pool Management
```bash
# Add node pool
doctl kubernetes cluster node-pool create hackathon-cluster \
  --name gpu-pool \
  --size s-2vcpu-4gb \
  --count 1

# Update node pool size
doctl kubernetes cluster node-pool update hackathon-cluster worker-pool --count 2

# Delete node pool
doctl kubernetes cluster node-pool delete hackathon-cluster gpu-pool --force
```

## Common Issues & Solutions

### Issue: Cluster stuck in "provisioning"
**Solution:**
```bash
# Check cluster status
doctl kubernetes cluster get hackathon-cluster

# If stuck >10 minutes, delete and recreate
doctl kubernetes cluster delete hackathon-cluster --force
```

### Issue: "Error: invalid token"
**Solution:**
```bash
# Re-authenticate
doctl auth init

# Or regenerate token at:
# https://cloud.digitalocean.com/account/api/tokens
```

### Issue: LoadBalancer stuck in "pending"
**Solution:**
```bash
# Check events
kubectl describe svc <service-name>

# DigitalOcean LB takes 1-3 minutes to provision
# If >5 minutes, check account limits:
doctl balance get
```

### Issue: kubectl can't connect
**Solution:**
```bash
# Refresh kubeconfig
doctl kubernetes cluster kubeconfig save hackathon-cluster --overwrite

# Check context
kubectl config current-context

# Switch context if needed
kubectl config use-context do-nyc1-hackathon-cluster
```

## Cost Management

### Monitor Costs
```bash
# Check account balance
doctl balance get

# List all clusters (check for forgotten clusters)
doctl kubernetes cluster list
```

### Cost-Saving Tips
1. **Use smallest node size** for development: `s-1vcpu-2gb`
2. **Delete clusters immediately** after hackathon ends
3. **Avoid LoadBalancer services** if testing locally (use NodePort or port-forward)
4. **Use single node** for non-production testing
5. **Set calendar reminder** to delete cluster

### Resource Cleanup Checklist
```bash
# 1. List all resources
doctl kubernetes cluster list
doctl compute droplet list
doctl compute load-balancer list
doctl compute volume list

# 2. Delete cluster (deletes nodes)
doctl kubernetes cluster delete <cluster-name> --force

# 3. Delete orphaned load balancers
doctl compute load-balancer delete <lb-id> --force

# 4. Delete orphaned volumes
doctl compute volume delete <volume-id> --force
```

## Production Considerations

### High Availability Setup
```bash
doctl kubernetes cluster create production-cluster \
  --region nyc1 \
  --version 1.28.2-do.0 \
  --node-pool "name=workers;size=s-2vcpu-4gb;count=3;auto-scale=true;min-nodes=3;max-nodes=5" \
  --ha \
  --auto-upgrade \
  --maintenance-window saturday=02:00 \
  --wait
```

### Autoscaling Configuration
```bash
# Create cluster with autoscaling
doctl kubernetes cluster node-pool create production-cluster \
  --name autoscale-pool \
  --size s-2vcpu-4gb \
  --count 2 \
  --auto-scale \
  --min-nodes 2 \
  --max-nodes 5
```

## Additional Resources
- [DOKS Documentation](https://docs.digitalocean.com/products/kubernetes/)
- [doctl Reference](https://docs.digitalocean.com/reference/doctl/)
- [API Rate Limits](https://docs.digitalocean.com/reference/api/api-reference/#section/Introduction/Rate-Limit)
