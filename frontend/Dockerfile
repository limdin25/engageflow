FROM node:20-alpine AS builder

WORKDIR /app

# Railway uses repo root as build context when Dockerfile path is frontend/Dockerfile
COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ .
RUN npm run build

FROM nginx:1.27-alpine

# Serve built static files (Vite outputs to dist/)
COPY --from=builder /app/dist /usr/share/nginx/html
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
