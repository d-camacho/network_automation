#!/bin/bash

# Define VM hostnames and IPs
declare -A vms=(
  ["kube_controller"]="192.168.122.10"
  ["kube_worker1"]="192.168.122.11"
  ["kube_worker2"]="192.168.122.12"
)

# Loop through each VM and rename
for vm_name in "${!vms[@]}"; do
  ip="${vms[$vm_name]}"
  echo "Renaming $ip to $vm_name..."

  ssh clab_admin@"$ip" <<EOF
    sudo hostnamectl set-hostname $vm_name
    sudo sed -i "s/^127.0.0.1.*/127.0.0.1 localhost $vm_name/" /etc/hosts
    echo "Hostname set to \$(hostname)"
EOF

  echo "Done with $vm_name"
  echo "----------------------"
done
