#!/usr/bin/env bash
set -euo pipefail

# Пользователи
USERS=("foo" "bar")

# Директория для артефактов
mkdir -p ./users

for USER in "${USERS[@]}"; do
  echo "[*] Создаём пользователя ${USER}..."
  openssl genrsa -out ./users/${USER}.key 2048
  openssl req -new -key ./users/${USER}.key -subj "/CN=${USER}" -out ./users/${USER}.csr
done

# Загружаем CSR в Kubernetes и подписываем
for USER in "${USERS[@]}"; do
  CSR_NAME=csr-${USER}

  kubectl delete csr ${CSR_NAME} --ignore-not-found
  cat <<EOF | kubectl apply -f -
apiVersion: certificates.k8s.io/v1
kind: CertificateSigningRequest
metadata:
  name: ${CSR_NAME}
spec:
  request: $(base64 < ./users/${USER}.csr | tr -d '\n')
  signerName: kubernetes.io/kube-apiserver-client
  usages: ["client auth"]
EOF

  kubectl certificate approve ${CSR_NAME}

  CERT_B64=$(kubectl get csr ${CSR_NAME} -o jsonpath='{.status.certificate}')
  echo "${CERT_B64}" | base64 -d > ./users/${USER}.crt

  echo "[*] Сертификат для ${USER} создан: ./users/${USER}.crt"
done
