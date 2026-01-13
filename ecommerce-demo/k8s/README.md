# Deploy to EKS (no Helm for your app)

This folder contains **plain Kubernetes YAML** for the eCommerce demo APIs.

## What you need in the cluster

- An EKS cluster in a VPC with public/private subnets
- **AWS Load Balancer Controller** installed (it creates the ALB for `Ingress`)
- Optional: `metrics-server` if you add HPAs later

## Build & push images (ECR)

Build context should be the `ecommerce-demo/` folder so the Dockerfiles can include `packages/shared`.

Example (repeat for each service):

```bash
cd ecommerce-demo

# catalog
docker build -f packages/services/catalog/Dockerfile -t catalog:local .
docker tag catalog:local <ACCOUNT>.dkr.ecr.<REGION>.amazonaws.com/catalog:<TAG>
docker push <ACCOUNT>.dkr.ecr.<REGION>.amazonaws.com/catalog:<TAG>
```

## Configure image URIs

Edit these files and replace `REPLACE_ME_*_IMAGE` with your ECR URIs:

- `catalog-deployment.yaml`
- `cart-deployment.yaml`
- `order-deployment.yaml`

## Apply manifests

```bash
kubectl apply -f namespace.yaml
kubectl apply -f catalog-deployment.yaml -f catalog-service.yaml
kubectl apply -f cart-deployment.yaml -f cart-service.yaml
kubectl apply -f order-deployment.yaml -f order-service.yaml
kubectl apply -f ingress-alb.yaml
```

## Get the ALB URL

```bash
kubectl -n ecommerce get ingress ecommerce-api
```

The `ADDRESS` field will show the ALB DNS name (use it as the API origin in CloudFront under `/api/*`).

