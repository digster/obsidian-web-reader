# Multi-stage Dockerfile for Obsidian Web Reader

# ==============================================================================
# Stage 1: Build frontend
# ==============================================================================
FROM node:20-slim AS frontend-build

WORKDIR /app/frontend

# Install pnpm
RUN npm install -g pnpm

# Copy frontend package files
COPY frontend/package.json frontend/pnpm-lock.yaml* ./

# Install dependencies
RUN pnpm install --frozen-lockfile || pnpm install

# Copy frontend source
COPY frontend/ ./

# Build the frontend (increase Node.js memory limit for build)
ENV NODE_OPTIONS=--max-old-space-size=4096
RUN pnpm build

# ==============================================================================
# Stage 2: Backend development
# ==============================================================================
FROM python:3.12-slim AS backend-dev

WORKDIR /app

# Install system dependencies (git is required for GitPython)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Copy backend files
COPY backend/pyproject.toml ./
COPY backend/src ./src

# Install dependencies
RUN uv pip install --system -e ".[dev]"

# Environment
ENV ENV=development
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "obsidian_reader.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ==============================================================================
# Stage 3: Production
# ==============================================================================
FROM python:3.12-slim AS production

WORKDIR /app

# Install system dependencies (git is required for GitPython, gosu for user switching)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    gosu \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Copy backend files
COPY backend/pyproject.toml ./
COPY backend/src ./src

# Install dependencies (production only)
RUN uv pip install --system -e .

# Copy built frontend
COPY --from=frontend-build /app/frontend/build ./static

# Copy entrypoint script
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Create data, config, and vaults directories
RUN mkdir -p /app/data /app/config /app/vaults

# Environment
ENV ENV=production
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1
ENV DATA_DIR=/app/data
ENV VAULTS_DIR=/app/vaults

# Create non-root user for security
# The entrypoint script will run as root to fix permissions, then switch to appuser
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app

EXPOSE 8000

# Use entrypoint to fix permissions and switch to appuser
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["uvicorn", "obsidian_reader.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]

