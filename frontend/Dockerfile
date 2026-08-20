FROM node:18-alpine AS build

ARG VITE_API_URL=http://localhost:8000
ENV VITE_API_URL=$VITE_API_URL

WORKDIR /workspace

COPY package.json ./
RUN npm install

COPY . .
RUN npm run build

FROM nginx:alpine

COPY --from=build /workspace/dist /usr/share/nginx/html

# Custom minimal config for Nginx SPA support
RUN echo 'server { \
    listen 80; \
    location / { \
        root /usr/share/nginx/html; \
        index index.html index.htm; \
        try_files $uri $uri/ /index.html; \
    } \
}' > /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
