# Stage 1 — Install dependencies
FROM node:20-alpine AS deps
WORKDIR /app
COPY package*.json ./
COPY prisma ./prisma
RUN npm ci
RUN npx prisma generate

# Stage 2 — Build the app
FROM node:20-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

# Stage 3 — Run the app
FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV PORT=10000
ENV HOSTNAME=0.0.0.0

COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/prisma ./prisma
COPY --from=builder /app/node_modules/.prisma ./node_modules/.prisma

EXPOSE 10000
CMD ["node", "server.js"]