#!/usr/bin/env bash
set -euo pipefail

USERS=("foo" "bar")

CLUSTER_NAME=$(kubectl config view -o jsonpath='{.contexts[?(@.name=="minikube")].context.cluster}')
CLUSTER_SERVER=$(kubectl config view -o jsonpath="{.clusters[?(@.name=='${CLUSTER_NAME}')].cluster.server}")
CA=$(kubectl config view --raw -o jsonpath="{.clusters[?(@.name=='${CLUSTER_NAME}')].cluster.certificate-authority-data}")

for USER in "${USERS[@]}"; do
  KCFG=./users/${USER}.kubeconfig

  kubectl config --kubeconfig=${KCFG} set-cluster ${CLUSTER_NAME} \
    --server=${CLUSTER_SERVER} \
    --certificate-authority <(echo $CA | base64 -d) \
    --embed-certs=true

  kubectl config --kubeconfig=${KCFG} set-credentials ${USER} \
    --client-certificate=./users/${USER}.crt \
    --client-key=./users/${USER}.key \
    --embed-certs=true

  kubectl config --kubeconfig=${KCFG} set-context ${USER}@${CLUSTER_NAME} \
    --cluster=${CLUSTER_NAME} \
    --user=${USER}

  kubectl config --kubeconfig=${KCFG} use-context ${USER}@${CLUSTER_NAME}

  echo "[*] kubeconfig для ${USER} готов: ${KCFG}"
done
