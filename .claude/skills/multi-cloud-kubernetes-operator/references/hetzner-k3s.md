# Hetzner Cloud K3s Reference

## Overview
Hetzner Cloud offers the best price-to-performance ratio for Kubernetes clusters using lightweight K3s. Ideal for budget-conscious hackathon projects.

**Pricing (as of 2026-02-05):**
- Minimum: ~€4-8/month (~$4.50-9/month) for CX11/CPX11 instances
- Free tier: None
- Best for: Maximum cost efficiency, European regions

## Prerequisites

### Install hetzner-k3s

**macOS (Homebrew):**
```bash
brew install vitobotta/tap/hetzner-k3s
```

**Linux (Direct download):**
```bash
# AMD64
wget https://github.com/vitobotta/hetzner-k3s/releases/download/v2.3.0/hetzner-k3s-linux-amd64
chmod +x hetzner-k3s-linux-amd64
sudo mv hetzner-k3s-linux-amd64 /usr/local/bin/hetzner-k3s

# ARM64
wget https://github.com/vitobotta/hetzner-k3s/releases/download/v2.3.0/hetzner-k3s-linux-arm64
chmod +x hetzner-k3s-linux-arm64
sudo mv hetzner-k3s-linux-arm64 /usr/local/bin/hetzner-k3s
```

**Verify installation:**
```bash
hetzner-k3s version
```

### Generate SSH Keys
```bash
# Generate ED25519 key (recommended)
ssh-keygen -t ed25519 -f ~/.ssh/hetzner-k3s -C "hetzner-k3s-cluster"

# Or use existing key
ls ~/.ssh/id_ed25519.pub ~/.ssh/id_rsa.pub
```

### Get Hetzner API Token
1. Visit https://console.hetzner.cloud/
2. Create project (e.g., "hackathon-cluster")
3. Go to Security → API Tokens
4. Generate Read & Write token
5. Save token securely

**Verify token:**
```bash
export HETZNER_TOKEN=your_api_token_here
curl -H "Authorization: Bearer $HETZNER_TOKEN" 'https://api.hetzner.cloud/v1/server_types'
```

## Quick Start Workflow

### 1. Create Configuration File

**Minimal hackathon config** (`cluster_config.yaml`):
```yaml
hetzner_token: <paste_your_token_here>
cluster_name: hackathon-cluster
kubeconfig_path: "./kubeconfig"
k3s_version: v1.30.3+k3s1

networking:
  ssh:
    port: 22
    use_agent: false
    public_key_path: "~/.ssh/id_ed25519.pub"
    private_key_path: "~/.ssh/id_ed25519"
  allowed_networks:
    ssh:
      - 0.0.0.0/0  # ⚠️ Restrict in production
    api:
      - 0.0.0.0/0  # ⚠️ Restrict in production

masters_pool:
  instance_type: cpx11  # €4.51/month
  instance_count: 1     # Single master for hackathons
  location: fsn1

worker_node_pools:
- name: workers
  instance_type: cpx11  # €4.51/month
  instance_count: 1     # Single worker for cost
  location: fsn1
```

**Budget-friendly options:**
- `cx21`: 2 vCPU, 4GB RAM, €5.83/month (AMD, older gen)
- `cpx11`: 2 vCPU, 2GB RAM, €4.51/month (AMD, current gen)
- `cx31`: 2 vCPU, 8GB RAM, €10.90/month

### 2. Create Cluster
```bash
# Create cluster (takes 3-5 minutes)
hetzner-k3s create --config cluster_config.yaml | tee create.log

# Output:
# - Creates servers in Hetzner Cloud
# - Installs K3s
# - Configures networking
# - Saves kubeconfig to ./kubeconfig
```

### 3. Configure kubectl
```bash
# Use generated kubeconfig
export KUBECONFIG=$(pwd)/kubeconfig

# Or merge into default kubeconfig
cp kubeconfig ~/.kube/hetzner-k3s-config
export KUBECONFIG=~/.kube/config:~/.kube/hetzner-k3s-config
kubectl config view --flatten > ~/.kube/config-merged
mv ~/.kube/config-merged ~/.kube/config
```

### 4. Verify Cluster
```bash
kubectl get nodes
# Should show 2 nodes (1 master, 1 worker) in Ready state

kubectl cluster-info
```

### 5. TEARDOWN (CRITICAL)
```bash
# ⚠️ Set protect_against_deletion to false in config first
# Edit cluster_config.yaml: protect_against_deletion: false

# Delete cluster
hetzner-k3s delete --config cluster_config.yaml

# Confirm by typing cluster name when prompted
# This deletes ALL resources created by hetzner-k3s

# ⚠️ Manually delete orphaned resources:
# - Load balancers created by apps
# - Persistent volumes created by apps
# Check in Hetzner Console: https://console.hetzner.cloud/
```

## Cluster Configuration Options

### Instance Types (Price vs Performance)

**Check available types:**
```bash
curl -H "Authorization: Bearer $HETZNER_TOKEN" 'https://api.hetzner.cloud/v1/server_types' | jq '.server_types[] | {name, description, cores, memory, disk, prices}'
```

**Recommended for hackathons:**
```yaml
# Ultra-minimal (~€9/month total)
masters_pool:
  instance_type: cpx11
  instance_count: 1
worker_node_pools:
- name: workers
  instance_type: cpx11
  instance_count: 1

# Budget HA (~€27/month total)
masters_pool:
  instance_type: cpx21
  instance_count: 3  # HA requires 3+ masters
  locations: [fsn1, hel1, nbg1]  # Different locations for HA
worker_node_pools:
- name: workers
  instance_type: cpx21
  instance_count: 2
```

### Locations
```yaml
# Europe locations (lowest latency from EU/US):
# fsn1 (Falkenstein, Germany)
# nbg1 (Nuremberg, Germany)
# hel1 (Helsinki, Finland)
# ash (Ashburn, VA, USA)
# hil (Hillsboro, OR, USA)

# For HA, use 3 different locations
masters_pool:
  locations:
    - fsn1
    - nbg1
    - hel1
```

### Autoscaling Configuration
```yaml
worker_node_pools:
- name: autoscale-workers
  instance_type: cpx21
  location: fsn1
  autoscaling:
    enabled: true
    min_instances: 1
    max_instances: 5
```

## Advanced Configuration

### High Availability Setup
```yaml
hetzner_token: <token>
cluster_name: ha-cluster
kubeconfig_path: "./kubeconfig"
k3s_version: v1.30.3+k3s1

networking:
  ssh:
    port: 22
    use_agent: false
    public_key_path: "~/.ssh/id_ed25519.pub"
    private_key_path: "~/.ssh/id_ed25519"
  allowed_networks:
    ssh:
      - 0.0.0.0/0
    api:
      - 0.0.0.0/0
  private_network:
    enabled: true
    subnet: 10.0.0.0/16

masters_pool:
  instance_type: cpx21
  instance_count: 3  # HA requires odd number (3, 5, 7)
  locations:
    - fsn1
    - hel1
    - nbg1

worker_node_pools:
- name: workers
  instance_type: cpx21
  instance_count: 3
  location: fsn1

protect_against_deletion: true  # Safety for production
```

### SSH Key with Passphrase
```yaml
networking:
  ssh:
    use_agent: true  # Required for passphrase-protected keys
    public_key_path: "~/.ssh/id_ed25519.pub"
    private_key_path: "~/.ssh/id_ed25519"
```

**Start SSH agent:**
```bash
eval "$(ssh-agent -s)"
ssh-add --apple-use-keychain ~/.ssh/id_ed25519  # macOS
# OR
ssh-add ~/.ssh/id_ed25519  # Linux
```

## Common Issues & Solutions

### Issue: "API token invalid"
**Solution:**
```bash
# Verify token
curl -H "Authorization: Bearer $HETZNER_TOKEN" 'https://api.hetzner.cloud/v1/server_types'

# Regenerate token in Hetzner Console if needed
```

### Issue: "SSH connection failed"
**Solution:**
```bash
# Verify SSH key exists
ls -la ~/.ssh/id_ed25519.pub

# Test SSH to created server
ssh root@<server-ip> -i ~/.ssh/id_ed25519

# Check SSH agent (if using passphrase)
ssh-add -l
```

### Issue: Nodes not joining cluster
**Solution:**
```bash
# SSH into master node
ssh root@<master-ip> -i ~/.ssh/id_ed25519

# Check K3s status
systemctl status k3s

# View logs
journalctl -u k3s -f
```

### Issue: Can't connect with kubectl
**Solution:**
```bash
# Verify kubeconfig path
ls -la ./kubeconfig

# Check kubeconfig content
cat ./kubeconfig

# Test connection
export KUBECONFIG=$(pwd)/kubeconfig
kubectl get nodes -v=6  # Verbose output for debugging
```

### Issue: "Quota exceeded"
**Solution:**
- Hetzner has resource limits per project
- Check console: https://console.hetzner.cloud/
- Contact support to increase limits
- Or create new project

## Cost Management

### Monitor Costs
```bash
# List all servers in project
curl -H "Authorization: Bearer $HETZNER_TOKEN" 'https://api.hetzner.cloud/v1/servers' | jq '.servers[] | {name, server_type, status}'

# Calculate monthly cost:
# cpx11: €4.51/month per server
# cpx21: €9.01/month per server
# cpx31: €17.01/month per server
```

### Cost-Saving Tips
1. **Use single-node clusters** for development/testing
2. **Delete clusters immediately** after use
3. **Use autoscaling** with min_instances=0 for worker pools
4. **Snapshot instead of keeping clusters running**
5. **Use cx-series (AMD)** for best price/performance

### Cleanup Checklist
```bash
# 1. Delete cluster via hetzner-k3s
hetzner-k3s delete --config cluster_config.yaml

# 2. Verify deletion in Hetzner Console
# https://console.hetzner.cloud/projects/<project-id>/servers

# 3. Check for orphaned resources:
# - Load balancers
# - Volumes
# - Floating IPs
# - Networks

# 4. Delete via API if needed
curl -X DELETE -H "Authorization: Bearer $HETZNER_TOKEN" \
  'https://api.hetzner.cloud/v1/servers/<server-id>'
```

## Production Considerations

### Network Security
```yaml
networking:
  allowed_networks:
    ssh:
      - "your.office.ip/32"  # Restrict SSH
    api:
      - "your.office.ip/32"  # Restrict K8s API
  private_network:
    enabled: true  # Internal traffic only
```

### External Database (for large clusters)
```yaml
datastore:
  mode: external
  external_datastore_endpoint: postgres://user:pass@host:5432/k3s
```

### Embedded Registry Mirror
```yaml
embedded_registry_mirror:
  enabled: true  # Faster image pulls via P2P
```

## Additional Resources
- [hetzner-k3s Documentation](https://github.com/vitobotta/hetzner-k3s)
- [Hetzner Cloud API](https://docs.hetzner.cloud/)
- [K3s Documentation](https://docs.k3s.io/)
- [Server Types & Pricing](https://www.hetzner.com/cloud)
