FROM node:22-alpine AS deps
WORKDIR /app

COPY package.json package-lock.json ./
COPY packages/shared/package.json packages/shared/package.json
COPY packages/services/cart/package.json packages/services/cart/package.json

RUN npm ci

FROM node:22-alpine AS build
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY tsconfig.base.json package.json package-lock.json ./
COPY packages/shared ./packages/shared
COPY packages/services/cart ./packages/services/cart

RUN npm -w @ecom/cart run build

FROM node:22-alpine AS run
WORKDIR /app
ENV NODE_ENV=production
ENV PORT=4002

COPY --from=deps /app/node_modules ./node_modules
COPY --from=build /app/packages/shared ./packages/shared
COPY --from=build /app/packages/services/cart/dist ./dist

EXPOSE 4002
CMD ["node", "dist/server.js"]

