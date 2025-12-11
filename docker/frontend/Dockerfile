# Frontend Dockerfile - Multi-stage build

# Stage 1: Build
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY frontend/package.json frontend/package-lock.json* ./

# Install dependencies
RUN npm ci

# Copy source
COPY frontend/ .

# Build
RUN npm run build

# Stage 2: Production
FROM nginx:alpine

# Copy nginx config
COPY docker/nginx/nginx.conf /etc/nginx/nginx.conf

# Copy built assets
COPY --from=builder /app/dist /usr/share/nginx/html

# Expose port
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
