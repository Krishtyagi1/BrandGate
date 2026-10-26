FROM node:22-bookworm-slim AS web
WORKDIR /app
ENV NEXT_TELEMETRY_DISABLED=1
COPY package.json package-lock.json ./
COPY apps/web/package.json apps/web/package.json
RUN npm ci
COPY apps/web apps/web
COPY packages packages
COPY scripts/editor-assets.mjs scripts/web.mjs scripts/
RUN npm run build

FROM python:3.12-slim-bookworm AS runtime
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    NEXT_TELEMETRY_DISABLED=1 \
    LANGSMITH_TRACING=false \
    LANGCHAIN_TRACING_V2=false \
    PORT=8080
COPY services/api/requirements.txt services/api/requirements.txt
RUN pip install --no-cache-dir -r services/api/requirements.txt
COPY --from=web /usr/local/bin/node /usr/local/bin/node
COPY --from=web /app/node_modules node_modules
COPY --from=web /app/apps/web apps/web
COPY services/api services/api
COPY scripts/hosted.py scripts/hosted.py
COPY samples samples
COPY docs/licenses docs/licenses
COPY LICENSE EXTERNAL_COMPONENTS.md ./
EXPOSE 8080
CMD ["python", "scripts/hosted.py"]
