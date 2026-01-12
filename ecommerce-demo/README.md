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

## Docs

- Architecture diagram: `../ecommerce-architecture-diagram.md`
- End-to-end architecture doc (includes HA/DR/DevOps/CI-CD): `docs/end-to-end-architecture.md`
