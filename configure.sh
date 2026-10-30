#!/usr/bin/env bash

set -euo pipefail

SERVER_IP="192.168.64.50" # server (admin) ip
SSH_USER="ubuntu"

KDIR="$HOME/.kube/k3s"
TMP="$HOME/.kube/k3s.yaml"

rm -rf KDIR

mkdir -p "$KDIR"

ssh "${SSH_USER}@${SERVER_IP}" 'sudo cat /etc/rancher/k3s/k3s.yaml' > "$TMP"
chmod 600 "$TMP"

extract() {
  grep "$1" "$TMP" | awk '{print $2}' | base64 -d > "$KDIR/$2"
}

extract certificate-authority-data ca.crt
extract client-certificate-data    client.crt
extract client-key-data            client.key
chmod 600 "$KDIR/client.key"

rm -f "$TMP"

kubectl config set-cluster k3s \
  --server="https://${SERVER_IP}:6443" \
  --certificate-authority="$KDIR/ca.crt"

kubectl config set-credentials k3s-admin \
  --client-certificate="$KDIR/client.crt" \
  --client-key="$KDIR/client.key"

kubectl config set-context k3s --cluster=k3s --user=k3s-admin
kubectl config use-context k3s

kubectl get nodes -o wide