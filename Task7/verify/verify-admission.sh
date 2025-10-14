kubectl apply -f ../gatekeeper/01-ct-no-privileged.yaml
kubectl apply -f ../gatekeeper/02-ct-require-runasnonroot.yaml
kubectl apply -f ../gatekeeper/03-ct-readonly-rootfs.yaml
kubectl apply -f ../gatekeeper/04-ct-no-hostpath.yaml