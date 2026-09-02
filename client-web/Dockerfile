FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
COPY svelte.config.js vite.config.ts tsconfig.json ./
COPY postcss.config.cjs tailwind.config.ts ./
RUN npm ci

COPY . .

EXPOSE 5174

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5174"]
