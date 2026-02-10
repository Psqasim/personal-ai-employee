#!/usr/bin/env python3
"""
GitHub Actions Workflow Generator - Creates workflow YAML files

Usage:
    generate_workflow.py ci --path .github/workflows/
    generate_workflow.py deploy --path .github/workflows/ --env staging
    generate_workflow.py docker --path .github/workflows/

Workflow Types:
    ci       - Continuous Integration (lint, test, coverage)
    deploy   - Deployment workflow with environment gates
    docker   - Docker build and push workflow
    release  - Release publishing workflow

Examples:
    python scripts/generate_workflow.py ci --path .github/workflows/
    python scripts/generate_workflow.py deploy --path .github/workflows/ --env production
"""

import sys
import argparse
from pathlib import Path


CI_WORKFLOW = '''name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  lint:
    name: Lint & Type Check
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install UV
        uses: astral-sh/setup-uv@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "{python_version}"

      - name: Install dependencies
        run: uv pip install -e ".[dev]" --system

      - name: Lint with ruff
        run: ruff check .

      - name: Type check with mypy
        run: mypy src/

  test:
    name: Test Python ${{{{ matrix.python-version }}}}
    runs-on: ubuntu-latest
    needs: lint
    strategy:
      fail-fast: false
      matrix:
        python-version: ["{python_version}", "3.13"]

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python ${{{{ matrix.python-version }}}}
        uses: actions/setup-python@v5
        with:
          python-version: ${{{{ matrix.python-version }}}}

      - name: Install UV
        uses: astral-sh/setup-uv@v4

      - name: Install dependencies
        run: uv pip install -e ".[dev]" --system

      - name: Run tests with coverage
        run: pytest --cov=src --cov-report=xml --cov-report=term-missing

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v4
        with:
          files: ./coverage.xml
          fail_ci_if_error: false
'''


DEPLOY_WORKFLOW = '''name: Deploy

on:
  push:
    branches: [main]
  workflow_dispatch:
    inputs:
      environment:
        description: 'Environment to deploy to'
        required: true
        default: '{environment}'
        type: choice
        options:
          - staging
          - production

jobs:
  build:
    name: Build
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "{python_version}"

      - name: Install UV
        uses: astral-sh/setup-uv@v4

      - name: Install dependencies
        run: uv pip install -e ".[dev]" --system

      - name: Run tests
        run: pytest

      - name: Build package
        run: python -m build

      - name: Upload build artifacts
        uses: actions/upload-artifact@v4
        with:
          name: dist
          path: dist/

  deploy-staging:
    name: Deploy to Staging
    needs: build
    runs-on: ubuntu-latest
    environment: staging
    if: github.ref == 'refs/heads/main' || github.event.inputs.environment == 'staging'
    steps:
      - uses: actions/checkout@v4

      - name: Download artifacts
        uses: actions/download-artifact@v4
        with:
          name: dist
          path: dist/

      - name: Deploy to staging
        run: |
          echo "Deploying to staging environment..."
          # TODO: Add your deployment commands here
        env:
          DEPLOY_TOKEN: ${{{{ secrets.STAGING_DEPLOY_TOKEN }}}}

  deploy-production:
    name: Deploy to Production
    needs: deploy-staging
    runs-on: ubuntu-latest
    environment: production
    if: github.event.inputs.environment == 'production'
    steps:
      - uses: actions/checkout@v4

      - name: Download artifacts
        uses: actions/download-artifact@v4
        with:
          name: dist
          path: dist/

      - name: Deploy to production
        run: |
          echo "Deploying to production environment..."
          # TODO: Add your deployment commands here
        env:
          DEPLOY_TOKEN: ${{{{ secrets.PRODUCTION_DEPLOY_TOKEN }}}}
'''


DOCKER_WORKFLOW = '''name: Docker Build

on:
  push:
    branches: [main]
    tags: ['v*']
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{{{ github.repository }}}}

jobs:
  build:
    name: Build and Push
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write

    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to Container Registry
        if: github.event_name != 'pull_request'
        uses: docker/login-action@v3
        with:
          registry: ${{{{ env.REGISTRY }}}}
          username: ${{{{ github.actor }}}}
          password: ${{{{ secrets.GITHUB_TOKEN }}}}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{{{ env.REGISTRY }}}}/${{{{ env.IMAGE_NAME }}}}
          tags: |
            type=ref,event=branch
            type=ref,event=pr
            type=semver,pattern={{{{version}}}}
            type=semver,pattern={{{{major}}}}.{{{{minor}}}}
            type=sha

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          push: ${{{{ github.event_name != 'pull_request' }}}}
          tags: ${{{{ steps.meta.outputs.tags }}}}
          labels: ${{{{ steps.meta.outputs.labels }}}}
          cache-from: type=gha
          cache-to: type=gha,mode=max
'''


RELEASE_WORKFLOW = '''name: Release

on:
  release:
    types: [published]

jobs:
  publish:
    name: Publish to PyPI
    runs-on: ubuntu-latest
    permissions:
      id-token: write  # For trusted publishing

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "{python_version}"

      - name: Install build tools
        run: pip install build

      - name: Build package
        run: python -m build

      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
        # Uses trusted publishing - no API token needed
        # Configure at: https://pypi.org/manage/project/YOUR-PROJECT/settings/publishing/
'''


WORKFLOWS = {
    "ci": ("ci.yml", CI_WORKFLOW),
    "deploy": ("deploy.yml", DEPLOY_WORKFLOW),
    "docker": ("docker.yml", DOCKER_WORKFLOW),
    "release": ("release.yml", RELEASE_WORKFLOW),
}


def main():
    parser = argparse.ArgumentParser(
        description="Generate GitHub Actions workflow files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument("workflow_type",
                        choices=WORKFLOWS.keys(),
                        help="Type of workflow to generate")
    parser.add_argument("--path", "-p", type=str, default=".github/workflows",
                        help="Output path for workflow file")
    parser.add_argument("--python-version", type=str, default="3.12",
                        help="Python version to use (default: 3.12)")
    parser.add_argument("--env", type=str, default="staging",
                        help="Default environment for deploy workflow")

    args = parser.parse_args()

    output_path = Path(args.path)
    output_path.mkdir(parents=True, exist_ok=True)

    filename, template = WORKFLOWS[args.workflow_type]

    # Format template with options
    content = template.format(
        python_version=args.python_version,
        environment=args.env
    )

    workflow_file = output_path / filename
    workflow_file.write_text(content)

    print(f"Created workflow: {workflow_file}")
    print(f"\nWorkflow type: {args.workflow_type}")

    if args.workflow_type == "ci":
        print("\nThis workflow will:")
        print("  - Run linting with ruff")
        print("  - Run type checking with mypy")
        print("  - Run tests with pytest and coverage")
        print("  - Upload coverage to Codecov")

    elif args.workflow_type == "deploy":
        print("\nThis workflow will:")
        print("  - Build the package")
        print("  - Deploy to staging (automatic on main)")
        print("  - Deploy to production (manual approval)")
        print("\nRequired secrets: STAGING_DEPLOY_TOKEN, PRODUCTION_DEPLOY_TOKEN")

    elif args.workflow_type == "docker":
        print("\nThis workflow will:")
        print("  - Build Docker image on push/PR")
        print("  - Push to GitHub Container Registry on main/tags")
        print("  - Use GitHub Actions cache for faster builds")

    elif args.workflow_type == "release":
        print("\nThis workflow will:")
        print("  - Build package on release")
        print("  - Publish to PyPI using trusted publishing")
        print("\nSetup: Configure trusted publishing at PyPI project settings")


if __name__ == "__main__":
    main()
