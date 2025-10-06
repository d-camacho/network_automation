#!/bin/bash

# Usage: sudo ./prep-node.sh <new_hostname>

# === Safety Check ===
if [ "$EUID" -ne 0 ]; then
  echo "❌ Please run as root (use sudo)"
  exit 1
fi

NEW_HOSTNAME="$1"

if [ -z "$NEW_HOSTNAME" ]; then
  echo "Usage: sudo $0 <new_hostname>"
  exit 1
fi

echo "🔧 Current hostname: $(hostname)"
echo "🔧 Setting hostname to $NEW_HOSTNAME..."
hostnamectl set-hostname "$NEW_HOSTNAME"

echo "📝 Updating /etc/hosts..."
sed -i "/127.0.0.1/d" /etc/hosts
echo "127.0.0.1 localhost $NEW_HOSTNAME" >> /etc/hosts

echo "🚫 Disabling swap..."
swapoff -a
sed -i '/swap/d' /etc/fstab

echo "🌉 Loading kernel modules and sysctl settings..."
cat <<EOF | tee /etc/modules-load.d/k8s.conf
br_netfilter
EOF

cat <<EOF | tee /etc/sysctl.d/k8s.conf
net.bridge.bridge-nf-call-iptables = 1
net.ipv4.ip_forward = 1
EOF

modprobe br_netfilter
sysctl --system

# === Firewall Setup ===
echo "🔥 Configuring firewall rules for Kubernetes..."

# Open kubelet port for control plane access
firewall-cmd --add-port=10250/tcp --permanent

# Optional: open NodePort range for services
firewall-cmd --add-port=30000-32767/tcp --permanent

# Reload firewall to apply changes
firewall-cmd --reload

echo "✅ Firewall rules applied: 10250/tcp and 30000-32767/tcp"

# === Optional: Disable firewalld entirely ===
# Uncomment below if you prefer no firewall in homelab
# systemctl stop firewalld
# systemctl disable firewalld
# echo "⚠️ firewalld disabled for homelab simplicity"

echo "✅ Node prep complete for $NEW_HOSTNAME"
