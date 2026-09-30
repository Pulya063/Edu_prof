FROM node:20-alpine AS base

# 1. Залежності
FROM base AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app
# Копіюємо package файли
COPY package.json package-lock.json ./
# Ставимо залежності
RUN npm ci

# 2. Збірка
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Вимикаємо телеметрію Next.js (опціонально, але добре для CI)
ENV NEXT_TELEMETRY_DISABLED 1

# Запускаємо збірку. Вона створить папку .next/standalone
RUN npm run build

# 3. Production образ
FROM base AS runner
WORKDIR /app

ENV NODE_ENV production
ENV NEXT_TELEMETRY_DISABLED 1
# Порт за замовчуванням
ENV PORT 3221
ENV HOSTNAME "0.0.0.0"

# Створюємо непривілейованого користувача з міркувань безпеки
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Копіюємо публічні файли
COPY --from=builder /app/public ./public

# Копіюємо згенерований standalone-сервер та статику
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3221

# server.js автоматично генерується Next.js при output: "standalone"
CMD ["node", "server.js"]
