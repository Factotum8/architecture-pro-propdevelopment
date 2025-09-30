kubectl run front-end-app      --image=nginx --labels role=front-end --expose --port 80
kubectl run back-end-api       --image=nginx --labels role=front-end --expose --port 80
kubectl run admin-front-end    --image=nginx --labels role=front-end --expose --port 80
kubectl run admin-back-end-api --image=nginx --labels role=front-end --expose --port 80