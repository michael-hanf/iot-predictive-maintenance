# Multi-stage build: Node build, then tiny Nginx server
FROM node:22-alpine AS builder

WORKDIR /app
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/public ./public
COPY frontend/src ./src
COPY frontend/tailwind.config.js frontend/postcss.config.js ./

# Build React app
RUN npm run build

# Final stage: serve with Nginx
FROM nginx:alpine

# Copy nginx config
RUN echo 'server { \
    listen 3000; \
    location / { \
        root /usr/share/nginx/html; \
        try_files $uri $uri/ /index.html; \
    } \
    location /api { \
        proxy_pass http://backend:8080; \
    } \
}' > /etc/nginx/conf.d/default.conf && \
sed -i 's/listen 80;/listen 3000;/' /etc/nginx/conf.d/default.conf

# Copy built app from builder
COPY --from=builder /app/build /usr/share/nginx/html

EXPOSE 3000
CMD ["nginx", "-g", "daemon off;"]
