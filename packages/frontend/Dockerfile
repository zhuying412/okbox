FROM node:22-alpine AS build

WORKDIR /app

# 配置国内 npm 源（npmmirror）
RUN npm config set registry https://registry.npmmirror.com

# Enable corepack for pnpm
RUN corepack enable

# Copy package files
COPY package.json ./

# Install dependencies
RUN pnpm install --frozen-lockfile || pnpm install

# Copy source
COPY . .

# Build for production
RUN pnpm run build

# ─── Production stage: serve with lightweight node server ──────
FROM node:22-alpine AS production

WORKDIR /app

# 配置国内 npm 源
RUN npm config set registry https://registry.npmmirror.com && \
    npm install -g serve

COPY --from=build /app/dist ./dist

EXPOSE 3000

CMD ["serve", "-s", "dist", "-l", "3000"]
