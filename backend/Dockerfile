FROM node:20-alpine
WORKDIR /app
RUN apk add --no-cache openssl curl
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN mkdir -p uploads logs keys
EXPOSE 10000
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:10000/health || exit 1
CMD ["node", "server.js"]
