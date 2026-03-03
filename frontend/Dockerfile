FROM node:20-alpine AS builder

WORKDIR /app

# Railway uses repo root as build context
COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ .
RUN npm run build

FROM nginx:1.27-alpine

# Remove default nginx config (prevents default "Hello world" page)
RUN rm -f /etc/nginx/conf.d/default.conf

# Copy built Vite output
COPY --from=builder /app/dist /usr/share/nginx/html

# Use our nginx config
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
