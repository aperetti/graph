# Multi-stage Dockerfile for Docusaurus
FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

# Serve stage using a simple node server or static file server
# Using busybox httpd for a very lightweight static server
FROM busybox:1.36

WORKDIR /public
COPY --from=builder /app/build ./docs

# Run httpd on port 3000
EXPOSE 3000
CMD ["httpd", "-f", "-p", "3000", "-h", "/public"]
