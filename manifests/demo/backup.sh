kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.20.0/cert-manager.yaml
kubectl rollout status deployment -n cert-manager cert-manager-webhook
kubectl apply -f https://github.com/cloudnative-pg/plugin-barman-cloud/releases/download/v0.15.1/manifest.yaml
kubectl rollout status deployment -n cnpg-system barman-cloud
kubectl create secret generic minio-creds --from-literal=ACCESS_KEY_ID=minioadmin --from-literal=ACCESS_SECRET_KEY=minioadmin123
kubectl apply -f minio.yaml
kubectl wait --for=condition=complete job/minio-create-bucket --timeout=180s
kubectl apply -f objectstore.yaml