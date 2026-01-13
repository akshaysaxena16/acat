# eCommerce demo (working locally) + AWS setup docs

This folder contains a **working demo eCommerce website**:

- **Frontend**: Vite + React (TypeScript)
- **Backend**: 3 microservices (Catalog, Cart, Order) on Node.js + Express (TypeScript)
- **Database**: SQLite (via Prisma) for a no-docker local demo (swap to Aurora/Postgres in AWS)

## Run locally (no Docker required)

From the repo root:

```bash
cd ecommerce-demo
npm install
npm run dev
```

Services:

- Frontend: `http://localhost:5173`
- Catalog API: `http://localhost:4001`
- Cart API: `http://localhost:4002`
- Order API: `http://localhost:4003`

## Use AWS EKS backend from local frontend

If your backend is deployed behind an ALB Ingress, set `VITE_API_BASE_URL` to your ALB URL.

Example:

```bash
cd ecommerce-demo/packages/frontend
cp .env.example .env
# edit .env and set:
# VITE_API_BASE_URL=http://<your-alb-dns-name>
```

## Docs

- Architecture diagram: `../ecommerce-architecture-diagram.md`
- End-to-end architecture doc (includes HA/DR/DevOps/CI-CD + AWS setup): `docs/end-to-end-architecture.md`

## Docker Hub CI pipeline (build + push)

This repo includes a GitHub Actions workflow that builds and pushes service images to Docker Hub:

- `tedakshay/ecomerce-catalog`
- `tedakshay/ecomerce-cart`
- `tedakshay/ecomerce-order`

To enable it, add these GitHub repo secrets:

- `DOCKERHUB_USERNAME`: your Docker Hub username (e.g. `tedakshay`)
- `DOCKERHUB_TOKEN`: a Docker Hub access token with push permissions
