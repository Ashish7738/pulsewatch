FROM nginxinc/nginx-unprivileged:1.27-alpine

COPY nginx/nginx.conf /etc/nginx/templates/default.conf.template
COPY frontend/index.html frontend/register.html frontend/dashboard.html /usr/share/nginx/html/
COPY frontend/css /usr/share/nginx/html/css
COPY frontend/js /usr/share/nginx/html/js

EXPOSE 8080