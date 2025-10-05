# Start fresh WITH the mount and your extra-config
```
minikube stop
minikube delete

mkdir -p ~/.minikube/files/etc/ssl/certs
cat <<EOF > ~/.minikube/files/etc/ssl/certs/audit-policy.yaml
apiVersion: audit.k8s.io/v1
kind: Policy
rules:
  - level: RequestResponse
    verbs: ["create", "delete", "update", "patch", "get", "list"]
    resources:
      - group: ""
        resources: ["pods", "secrets", "configmaps", "serviceaccounts", "roles", "rolebindings"]

  # Catch-all for ALL core API resources (group = "")
  - level: Metadata
    resources:
      - resources: ["*"]   # group omitted == same as group: ""
EOF
minikube start \
  --extra-config=apiserver.audit-policy-file=/etc/ssl/certs/audit-policy.yaml \
  --extra-config=apiserver.audit-log-path=/var/log/audit.log

minikube cp kube-apiserver.yaml  /etc/kubernetes/manifests/kube-apiserver.yaml

minikube stop
minikube start
```

# Copy log file form minikube
```
minikube cp minikube:/var/log/audit.log ./audit.log
```

# Stop & remove the existing node
```
minikube stop
minikube delete
minikube -p minikube delete --all --purge
docker system prune -f
```

# Create the dir & copy your policy into the node
```
minikube ssh -- 'sudo mkdir -p /etc/kubernetes/config'
minikube  cp "/Users/alex/Documents/projects/architecture-pro-propdevelopment/Task6/kube-apiserver.yaml" /etc/kubernetes/config/audit-policy.yaml
```

# Bounce the API server pod (kubelet will recreate it)
`minikube -p minikube ssh -- "sudo crictl pods | grep kube-apiserver -q && sudo crictl ps -a | awk '/kube-apiserver/{print \$1}' | xargs -r sudo crictl rm -f"`
# or simply restart the node:
```
minikube -p minikube stop && minikube -p minikube start

minikube -p minikube ssh
sudo crictl ps -a | grep kube-apiserver
sudo crictl logs 47200d9ecd242 | less
```



