# Playwright-enabled image for Joiner on Railway
FROM mcr.microsoft.com/playwright:v1.58.2-noble

WORKDIR /app

COPY package*.json ./
RUN npm ci --omit=dev
RUN npx playwright install chromium

COPY . .
EXPOSE 3100

ENV PORT=3100
CMD ["node", "server.js"]
