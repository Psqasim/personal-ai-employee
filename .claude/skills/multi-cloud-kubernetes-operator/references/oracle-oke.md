# Oracle Cloud Infrastructure OKE Reference

## Overview
Oracle Cloud Infrastructure (OCI) offers truly free Kubernetes clusters via Always Free tier. Best for learning and long-term hackathon projects where cost is the primary concern.

**Pricing (as of 2026-02-05):**
- Minimum: $0 with Always Free tier
- Free tier: 2 AMD-based Compute VMs (VM.Standard.E2.1.Micro) + 4 ARM-based Ampere A1 cores + 24GB RAM total
- Best for: Zero-cost learning, long-running dev environments

⚠️ **IMPORTANT:** Setup complexity is HIGH. OKE requires VCN, subnets, security lists, compartments, and IAM policies. Not recommended for time-sensitive hackathons.

## Prerequisites

### Install OCI CLI

**macOS:**
```bash
brew install oci-cli
```

**Linux/macOS (official installer):**
```bash
bash -c "$(curl -L https://raw.githubusercontent.com/oracle/oci-cli/master/scripts/install/install.sh)"
# Follow prompts, default installation to ~/bin/oci
```

**Verify installation:**
```bash
oci --version
```

### Configure OCI CLI

**Interactive setup:**
```bash
oci setup config

# You'll be prompted for:
# - Config file location (default: ~/.oci/config)
# - User OCID
# - Tenancy OCID
# - Region
# - Generate new API key (Y/n)
```

**Get required OCIDs:**
1. Log in to https://cloud.oracle.com/
2. Profile icon → Tenancy → Copy Tenancy OCID
3. Profile icon → User Settings → Copy User OCID
4. Region: Select from console (e.g., us-ashburn-1, us-phoenix-1)

**Verify authentication:**
```bash
oci iam region list
oci iam availability-domain list --compartment-id <your-tenancy-ocid>
```

## Network Prerequisites (CRITICAL)

OKE requires pre-existing networking. You must create:

### 1. Create Compartment
```bash
# Compartments organize resources
oci iam compartment create \
  --compartment-id <tenancy-ocid> \
  --name "hackathon-k8s" \
  --description "Kubernetes hackathon resources"

# Get compartment OCID from output
export COMPARTMENT_ID=ocid1.compartment.oc1..aaaaaaaexample
```

### 2. Create VCN (Virtual Cloud Network)
```bash
# Create VCN
oci network vcn create \
  --compartment-id $COMPARTMENT_ID \
  --cidr-block "10.0.0.0/16" \
  --display-name "k8s-vcn" \
  --dns-label "k8svcn"

# Get VCN OCID from output
export VCN_ID=ocid1.vcn.oc1.iad.aaaaaaaexample
```

### 3. Create Internet Gateway
```bash
oci network internet-gateway create \
  --compartment-id $COMPARTMENT_ID \
  --is-enabled true \
  --vcn-id $VCN_ID \
  --display-name "k8s-igw"

# Get IGW OCID
export IGW_ID=ocid1.internetgateway.oc1.iad.aaaaaaaexample
```

### 4. Create Route Table
```bash
# Get default route table ID
oci network route-table list \
  --compartment-id $COMPARTMENT_ID \
  --vcn-id $VCN_ID

export RT_ID=ocid1.routetable.oc1.iad.aaaaaaaexample

# Update route table to use IGW
oci network route-table update \
  --rt-id $RT_ID \
  --route-rules '[{"destination":"0.0.0.0/0","networkEntityId":"'$IGW_ID'"}]' \
  --force
```

### 5. Create Subnets
```bash
# Kubernetes API subnet
oci network subnet create \
  --compartment-id $COMPARTMENT_ID \
  --vcn-id $VCN_ID \
  --cidr-block "10.0.0.0/24" \
  --display-name "k8s-api-subnet" \
  --dns-label "k8sapi" \
  --route-table-id $RT_ID \
  --prohibit-public-ip-on-vnic false

export API_SUBNET_ID=ocid1.subnet.oc1.iad.aaaaaaaexample

# Node pool subnet
oci network subnet create \
  --compartment-id $COMPARTMENT_ID \
  --vcn-id $VCN_ID \
  --cidr-block "10.0.1.0/24" \
  --display-name "k8s-nodes-subnet" \
  --dns-label "k8snodes" \
  --route-table-id $RT_ID \
  --prohibit-public-ip-on-vnic false

export NODES_SUBNET_ID=ocid1.subnet.oc1.iad.aaaaaaaexample

# Load balancer subnet
oci network subnet create \
  --compartment-id $COMPARTMENT_ID \
  --vcn-id $VCN_ID \
  --cidr-block "10.0.2.0/24" \
  --display-name "k8s-lb-subnet" \
  --dns-label "k8slb" \
  --route-table-id $RT_ID \
  --prohibit-public-ip-on-vnic false

export LB_SUBNET_ID=ocid1.subnet.oc1.iad.aaaaaaaexample
```

### 6. Configure Security Lists
```bash
# This is complex - recommend using OCI Console Web UI:
# Networking → Virtual Cloud Networks → <your-vcn> → Security Lists
# Add rules for:
# - Kubernetes API (6443)
# - Node communication (all internal)
# - Load balancer traffic (80, 443)
```

## Quick Start Workflow (After Network Setup)

### 1. Create OKE Cluster (Always Free Eligible)
```bash
# ⚠️ UNVERIFIED - Context7 does not have complete OKE cluster create docs
# Verify this command in official docs: https://docs.oracle.com/en-us/iaas/Content/ContEng/home.htm

# Basic cluster creation (check official OCI docs for exact flags)
oci ce cluster create \
  --compartment-id $COMPARTMENT_ID \
  --name "hackathon-cluster" \
  --vcn-id $VCN_ID \
  --kubernetes-version "v1.28.2" \
  --endpoint-config '{"subnetId":"'$API_SUBNET_ID'","isPublicIpEnabled":true}' \
  --options '{"serviceLbSubnetIds":["'$LB_SUBNET_ID'"]}'

# Get cluster OCID from output
export CLUSTER_ID=ocid1.cluster.oc1.iad.aaaaaaaexample

# Wait for cluster to be active (10-15 minutes)
oci ce cluster get --cluster-id $CLUSTER_ID --query 'data."lifecycle-state"'
```

### 2. Create Node Pool (Always Free Shapes)
```bash
# ⚠️ UNVERIFIED - Verify exact shape names and flags in official OCI docs
# Always Free shapes:
# - VM.Standard.E2.1.Micro (x86, 1 OCPU, 1GB RAM) - 2 free
# - VM.Standard.A1.Flex (ARM, configurable) - 4 OCPUs + 24GB total free

# Get availability domain
oci iam availability-domain list --compartment-id $COMPARTMENT_ID

export AD_NAME="ABC:US-ASHBURN-AD-1"

# Create ARM node pool (Always Free)
oci ce node-pool create \
  --cluster-id $CLUSTER_ID \
  --compartment-id $COMPARTMENT_ID \
  --name "free-arm-pool" \
  --node-shape "VM.Standard.A1.Flex" \
  --node-shape-config '{"ocpus": 1, "memoryInGBs": 6}' \
  --placement-configs '[{"availabilityDomain":"'$AD_NAME'","subnetId":"'$NODES_SUBNET_ID'"}]' \
  --size 2 \
  --kubernetes-version "v1.28.2"

# Or create x86 node pool (Always Free)
oci ce node-pool create \
  --cluster-id $CLUSTER_ID \
  --compartment-id $COMPARTMENT_ID \
  --name "free-x86-pool" \
  --node-shape "VM.Standard.E2.1.Micro" \
  --placement-configs '[{"availabilityDomain":"'$AD_NAME'","subnetId":"'$NODES_SUBNET_ID'"}]' \
  --size 2 \
  --kubernetes-version "v1.28.2"
```

### 3. Get Kubeconfig
```bash
# Generate kubeconfig
oci ce cluster create-kubeconfig \
  --cluster-id $CLUSTER_ID \
  --file ~/.kube/oke-config \
  --token-version 2.0.0

# Use kubeconfig
export KUBECONFIG=~/.kube/oke-config
```

### 4. Verify Cluster
```bash
kubectl get nodes
# May take 5-10 minutes for nodes to be Ready

kubectl cluster-info
```

### 5. TEARDOWN (IMPORTANT)
```bash
# ⚠️ Delete node pools first
oci ce node-pool list --cluster-id $CLUSTER_ID
oci ce node-pool delete --node-pool-id <node-pool-ocid> --force

# Delete cluster
oci ce cluster delete --cluster-id $CLUSTER_ID --force

# Verify deletion
oci ce cluster get --cluster-id $CLUSTER_ID

# Clean up network resources (reverse order)
oci network subnet delete --subnet-id $LB_SUBNET_ID --force
oci network subnet delete --subnet-id $NODES_SUBNET_ID --force
oci network subnet delete --subnet-id $API_SUBNET_ID --force
oci network internet-gateway delete --ig-id $IGW_ID --force
oci network vcn delete --vcn-id $VCN_ID --force
oci iam compartment delete --compartment-id $COMPARTMENT_ID --force
```

## Always Free Tier Limits

**Compute:**
- 2x VM.Standard.E2.1.Micro (x86, 1 OCPU, 1GB RAM each)
- 4x ARM OCPU (configurable across VMs, max 24GB RAM total)
- Example: 2x VM.Standard.A1.Flex (2 OCPU, 12GB RAM each)

**Storage:**
- 200GB block volume storage
- 10GB object storage

**Networking:**
- 1 public IP per instance
- 10TB outbound data transfer/month

**Load Balancer:**
- 1x 10Mbps flexible load balancer

## Common Issues & Solutions

### Issue: "Service limit exceeded"
**Solution:**
- Always Free resources are limited
- Check limits: https://cloud.oracle.com/limits
- Request limit increase (may require payment method)
- Use different region (free tier per region)

### Issue: "Subnet not found" or "VCN errors"
**Solution:**
```bash
# Verify networking setup
oci network vcn list --compartment-id $COMPARTMENT_ID
oci network subnet list --compartment-id $COMPARTMENT_ID --vcn-id $VCN_ID

# Recreate if missing
```

### Issue: "Cannot reach Kubernetes API"
**Solution:**
- Check security list allows port 6443
- Verify API endpoint subnet has public IP enabled
- Check internet gateway and route table configuration
- Try regenerating kubeconfig

### Issue: Nodes stuck "provisioning"
**Solution:**
```bash
# Check node pool status
oci ce node-pool get --node-pool-id <node-pool-id>

# Check instance status
oci compute instance list --compartment-id $COMPARTMENT_ID

# Common causes:
# - Insufficient Always Free quota
# - Incorrect subnet configuration
# - Security list blocking traffic
```

### Issue: "Out of host capacity"
**Solution:**
- ARM instances (A1.Flex) have limited capacity
- Try different availability domain
- Try different region
- Use x86 instances (E2.1.Micro) instead

## Cost Management

### Always Free Monitoring
```bash
# List compute instances
oci compute instance list --compartment-id $COMPARTMENT_ID

# Check if instances are Always Free eligible
# Look for "isFreeEligible": true in output

# Monitor usage
# OCI Console → Governance → Cost Analysis
```

### Cost-Saving Tips
1. **Stick to Always Free shapes only**
2. **Use ARM instances** (4 OCPUs free vs 2 x86 VMs)
3. **One cluster per region** (Always Free is per-region)
4. **Minimize load balancers** (1 free, additional cost $)
5. **Clean up regularly** to avoid accidental paid resources

## Limitations for Hackathons

**Pros:**
- Truly free (no credit card charges)
- Long-running clusters for multi-week hackathons
- Real managed Kubernetes experience

**Cons:**
- HIGH setup complexity (30-60 minutes initial setup)
- Limited compute power (1GB RAM VMs)
- Capacity issues (ARM instances often unavailable)
- Slow provisioning (10-20 minutes)
- Complex networking requirements

**Verdict:** Only use OCI OKE if:
- You have 2+ hours for initial setup
- Cost is more important than time
- You need long-running dev environment
- You're willing to troubleshoot networking

For hackathons <48 hours, use DigitalOcean or Hetzner instead.

## Alternative: OCI + K3s

**Simpler approach:** Skip OKE entirely, use compute instances + K3s:

```bash
# Create Always Free instance
oci compute instance launch \
  --availability-domain $AD_NAME \
  --compartment-id $COMPARTMENT_ID \
  --shape VM.Standard.A1.Flex \
  --shape-config '{"ocpus": 2, "memoryInGBs": 12}' \
  --image-id <ubuntu-image-id> \
  --subnet-id $NODES_SUBNET_ID

# SSH into instance
ssh ubuntu@<instance-public-ip>

# Install K3s
curl -sfL https://get.k3s.io | sh -

# Copy kubeconfig
scp ubuntu@<instance-public-ip>:/etc/rancher/k3s/k3s.yaml ~/.kube/oci-k3s-config
# Edit server address in kubeconfig to use public IP
```

This avoids OKE complexity while staying in Always Free tier.

## Additional Resources
- [OKE Documentation](https://docs.oracle.com/en-us/iaas/Content/ContEng/home.htm)
- [OCI CLI Reference](https://docs.oracle.com/en-us/iaas/tools/oci-cli/latest/)
- [Always Free Resources](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm)
- [OCI Free Tier FAQ](https://www.oracle.com/cloud/free/faq.html)
