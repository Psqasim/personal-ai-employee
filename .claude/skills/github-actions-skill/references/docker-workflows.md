# Docker Build and Push Workflows

## Basic Docker Build

### Simple Build and Push

```yaml
name: Docker Build

on:
  push:
    branches: [main]
    tags: ["v*"]

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Login to Docker Hub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: username/app:latest
```

## Multi-Registry Push

### Docker Hub and GHCR

```yaml
name: Docker Multi-Registry

on:
  push:
    branches: [main]
    tags: ["v*"]

env:
  DOCKERHUB_IMAGE: username/myapp
  GHCR_IMAGE: ghcr.io/${{ github.repository }}

jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write

    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Login to Docker Hub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}

      - name: Login to GitHub Container Registry
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: |
            ${{ env.DOCKERHUB_IMAGE }}
            ${{ env.GHCR_IMAGE }}
          tags: |
            type=ref,event=branch
            type=semver,pattern={{version}}
            type=sha

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
```

## Versioned Tags

### Semantic Versioning

```yaml
name: Docker Release

on:
  push:
    tags: ["v*"]

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Docker meta
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: username/myapp
          tags: |
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=semver,pattern={{major}}
            type=sha

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Login to Docker Hub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}

# For tag v1.2.3, creates:
# - username/myapp:1.2.3
# - username/myapp:1.2
# - username/myapp:1
# - username/myapp:sha-abc1234
```

## Multi-Platform Builds

### AMD64 and ARM64

```yaml
name: Multi-Platform Docker

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up QEMU
        uses: docker/setup-qemu-action@v3

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Login to Docker Hub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          platforms: linux/amd64,linux/arm64
          push: true
          tags: username/myapp:latest
```

## Build Caching

### GitHub Actions Cache

```yaml
name: Docker with Cache

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Login to Docker Hub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: username/myapp:latest
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

### Registry Cache

```yaml
- name: Build and push
  uses: docker/build-push-action@v5
  with:
    context: .
    push: true
    tags: username/myapp:latest
    cache-from: type=registry,ref=username/myapp:cache
    cache-to: type=registry,ref=username/myapp:cache,mode=max
```

## Build Arguments and Secrets

### Build Arguments

```yaml
- name: Build and push
  uses: docker/build-push-action@v5
  with:
    context: .
    push: true
    tags: username/myapp:latest
    build-args: |
      NODE_ENV=production
      VERSION=${{ github.sha }}
      BUILD_DATE=${{ github.event.head_commit.timestamp }}
```

### Build Secrets

```yaml
- name: Build and push
  uses: docker/build-push-action@v5
  with:
    context: .
    push: true
    tags: username/myapp:latest
    secrets: |
      "npm_token=${{ secrets.NPM_TOKEN }}"
      "github_token=${{ secrets.GITHUB_TOKEN }}"

# In Dockerfile:
# RUN --mount=type=secret,id=npm_token \
#     NPM_TOKEN=$(cat /run/secrets/npm_token) npm ci
```

## Multi-Stage Workflows

### Build, Test, Push

```yaml
name: Docker CI/CD

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    outputs:
      image: ${{ steps.meta.outputs.tags }}

    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Docker meta
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: username/myapp
          tags: |
            type=sha

      - name: Build
        uses: docker/build-push-action@v5
        with:
          context: .
          load: true  # Load to local Docker
          tags: ${{ steps.meta.outputs.tags }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

      - name: Run tests in container
        run: |
          docker run --rm ${{ steps.meta.outputs.tags }} pytest

      - name: Login and push
        if: github.event_name == 'push'
        run: |
          echo "${{ secrets.DOCKERHUB_TOKEN }}" | docker login -u "${{ secrets.DOCKERHUB_USERNAME }}" --password-stdin
          docker push ${{ steps.meta.outputs.tags }}
```

## Docker Compose

### Build with Compose

```yaml
name: Docker Compose

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Build images
        run: docker compose build

      - name: Run tests
        run: docker compose run --rm app pytest

      - name: Push images
        if: github.ref == 'refs/heads/main'
        run: |
          echo "${{ secrets.DOCKERHUB_TOKEN }}" | docker login -u "${{ secrets.DOCKERHUB_USERNAME }}" --password-stdin
          docker compose push
```

## Dockerfile Examples

### Python Application

```dockerfile
# Dockerfile
FROM python:3.12-slim as builder

WORKDIR /app

# Install build dependencies
RUN pip install --no-cache-dir build

# Copy and build
COPY pyproject.toml .
COPY src/ src/
RUN python -m build --wheel

# Production image
FROM python:3.12-slim

WORKDIR /app

# Copy wheel from builder
COPY --from=builder /app/dist/*.whl .
RUN pip install --no-cache-dir *.whl && rm *.whl

# Run as non-root
RUN useradd -m appuser
USER appuser

CMD ["python", "-m", "myapp"]
```

### Node.js Application

```dockerfile
# Dockerfile
FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# Production image
FROM node:20-alpine

WORKDIR /app

COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
COPY package*.json ./

USER node

EXPOSE 3000
CMD ["node", "dist/index.js"]
```

## Security Scanning

### Trivy Scanner

```yaml
name: Docker Security

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Build image
        run: docker build -t myapp:${{ github.sha }} .

      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: myapp:${{ github.sha }}
          format: "sarif"
          output: "trivy-results.sarif"
          severity: "CRITICAL,HIGH"

      - name: Upload Trivy scan results
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: "trivy-results.sarif"
```

## Best Practices

### 1. Use Specific Base Image Tags

```dockerfile
# GOOD
FROM python:3.12.1-slim

# BAD
FROM python:latest
```

### 2. Multi-Stage Builds

```dockerfile
# Build stage
FROM node:20 AS builder
RUN npm ci && npm run build

# Production stage
FROM node:20-alpine
COPY --from=builder /app/dist ./dist
```

### 3. Cache Dependencies First

```dockerfile
# Copy dependency files first
COPY package*.json ./
RUN npm ci

# Then copy source
COPY . .
RUN npm run build
```

### 4. Use .dockerignore

```
# .dockerignore
node_modules
.git
.env
*.md
tests/
```
