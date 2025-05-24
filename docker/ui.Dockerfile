FROM node:16-alpine AS builder

WORKDIR /app

# Copy UI directory contents
COPY ui/package*.json ./

# Install dependencies
RUN npm install

# Copy UI source code
COPY ui/public ./public
COPY ui/src ./src

# Build the app
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built files
COPY --from=builder /app/build /usr/share/nginx/html

# Copy nginx configuration from root
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
