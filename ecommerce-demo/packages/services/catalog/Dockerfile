FROM node:22-alpine AS deps
WORKDIR /app

# Copy dependency manifests first (better layer caching)
COPY package.json package-lock.json ./
COPY packages/shared/package.json packages/shared/package.json
COPY packages/services/catalog/package.json packages/services/catalog/package.json

RUN npm ci

FROM node:22-alpine AS build
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY tsconfig.base.json package.json package-lock.json ./
COPY packages/shared ./packages/shared
COPY packages/services/catalog ./packages/services/catalog

RUN npm -w @ecom/catalog run build

FROM node:22-alpine AS run
WORKDIR /app
ENV NODE_ENV=production
ENV PORT=4001

# Only what we need at runtime
COPY --from=deps /app/node_modules ./node_modules
COPY --from=build /app/packages/shared ./packages/shared
COPY --from=build /app/packages/services/catalog/dist ./dist

EXPOSE 4001
CMD ["node", "dist/server.js"]

