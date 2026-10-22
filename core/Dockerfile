# Stage 1: Build the Vue application
FROM node:20-alpine as build-stage

WORKDIR /app
COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

# Stage 2: Serve the application with Nginx
FROM nginx:alpine as production-stage

# Remove default nginx static assets
RUN rm -rf /usr/share/nginx/html/*

# Copy built assets from build-stage
COPY --from=build-stage /app/dist /usr/share/nginx/html

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
