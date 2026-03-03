FROM node:20-alpine AS builder

WORKDIR /app

# Railway uses repo root as build context
COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ .
RUN npm run build

FROM nginx:1.27-alpine

# Remove default nginx config
RUN rm -f /etc/nginx/conf.d/default.conf

# Copy built Vite output
COPY --from=builder /app/dist /usr/share/nginx/html

# Use nginx template system so Railway can inject $PORT
COPY frontend/nginx.conf /etc/nginx/templates/default.conf.template

EXPOSE 8080
