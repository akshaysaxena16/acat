FROM node:22-alpine AS deps
WORKDIR /app

COPY package.json package-lock.json ./
COPY packages/shared/package.json packages/shared/package.json
COPY packages/services/order/package.json packages/services/order/package.json

RUN npm ci

FROM node:22-alpine AS build
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY tsconfig.base.json package.json package-lock.json ./
COPY packages/shared ./packages/shared
COPY packages/services/order ./packages/services/order

RUN npm -w @ecom/order run build

FROM node:22-alpine AS run
WORKDIR /app
ENV NODE_ENV=production
ENV PORT=4003
# In-cluster catalog service DNS
ENV CATALOG_BASE_URL=http://catalog:4001

COPY --from=deps /app/node_modules ./node_modules
COPY --from=build /app/packages/shared ./packages/shared
COPY --from=build /app/packages/services/order/dist ./dist

EXPOSE 4003
CMD ["node", "dist/server.js"]

