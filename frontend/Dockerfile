# ==============================================================================
# Multi-stage Dockerfile for React + Vite Frontend
# Rule 10: Mandatory healthcheck and optimized unprivileged production runtime
# ==============================================================================

# --- Stage 1: Build Static Assets ---
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package dependencies definitions
COPY package*.json ./

# Install all dependencies (including devDependencies required for vite build)
RUN npm ci

# Copy frontend source code and configuration files
COPY . .

# Compile TypeScript and bundle production assets into dist/
RUN npm run build


# --- Stage 2: Production Nginx Runtime ---
FROM nginx:1.27-alpine AS runner

WORKDIR /usr/share/nginx/html

# Remove default Nginx welcome assets
RUN rm -rf ./*

# Copy compiled SPA bundle from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy custom Nginx configuration with SPA fallback, security headers and proxy
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

# Docker Healthcheck instruction (Hard Rule #10)
HEALTHCHECK --interval=15s --timeout=5s --start-period=5s --retries=3 \
    CMD wget -q --spider http://localhost:80/healthz || exit 1

CMD ["nginx", "-g", "daemon off;"]
