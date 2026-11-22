# Build context is the repo root (see docker-compose.yml).
# Unprivileged nginx image: runs as a non-root user and listens on 8080 inside the container.
FROM nginxinc/nginx-unprivileged:1.27-alpine

COPY nginx/nginx.conf /etc/nginx/conf.d/default.conf
COPY frontend/index.html frontend/register.html frontend/dashboard.html /usr/share/nginx/html/
COPY frontend/css /usr/share/nginx/html/css
COPY frontend/js /usr/share/nginx/html/js

EXPOSE 8080
