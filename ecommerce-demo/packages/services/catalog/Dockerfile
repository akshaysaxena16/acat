FROM node:22-alpine AS deps
WORKDIR /app

# Copy dependency manifests first (better layer caching)
COPY package.json package-lock.json ./
COPY packages/shared/package.json packages/shared/package.json
COPY packages/frontend/package.json packages/frontend/package.json
COPY packages/services/cart/package.json packages/services/cart/package.json
COPY packages/services/catalog/package.json packages/services/catalog/package.json
COPY packages/services/order/package.json packages/services/order/package.json

RUN npm ci

FROM node:22-alpine AS build
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY --from=deps /app/packages ./packages
COPY tsconfig.base.json package.json package-lock.json ./
COPY packages/shared ./packages/shared
COPY packages/services/catalog ./packages/services/catalog

RUN npm -w @ecom/catalog run build

FROM node:22-alpine AS run
WORKDIR /app/packages/services/catalog
ENV NODE_ENV=production
ENV PORT=4001

# Only what we need at runtime
COPY --from=deps /app/node_modules /app/node_modules
COPY --from=deps /app/packages /app/packages
COPY --from=build /app/packages/services/catalog/dist /app/packages/services/catalog/dist

EXPOSE 4001
CMD ["node", "dist/server.js"]

