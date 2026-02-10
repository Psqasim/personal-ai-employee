# Secrets and Environment Variables

## Repository Secrets

### Creating Secrets

1. Go to Repository → Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Enter name and value

### Using Secrets

```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Use secret in env
        env:
          API_KEY: ${{ secrets.API_KEY }}
        run: |
          echo "Using API key"
          curl -H "Authorization: Bearer $API_KEY" https://api.example.com

      - name: Use secret directly
        run: |
          echo "${{ secrets.DEPLOY_KEY }}" > deploy_key
          chmod 600 deploy_key
```

### Secret Masking

```yaml
# Secrets are automatically masked in logs
steps:
  - run: echo "${{ secrets.API_KEY }}"
    # Output: ***

  - run: |
      # Even partial matches are masked
      echo "Key is ${{ secrets.API_KEY }}"
```

## Environment Secrets

### Environment Configuration

1. Go to Repository → Settings → Environments
2. Create environment (e.g., "production", "staging")
3. Add environment-specific secrets
4. Configure protection rules

### Using Environments

```yaml
jobs:
  deploy-staging:
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - name: Deploy
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}  # From staging env
        run: ./deploy.sh

  deploy-production:
    runs-on: ubuntu-latest
    environment: production
    needs: deploy-staging
    steps:
      - name: Deploy
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}  # From production env
        run: ./deploy.sh
```

### Environment Protection Rules

```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    environment:
      name: production
      url: https://myapp.com  # Displayed in PR

    steps:
      - name: Deploy
        run: ./deploy.sh
```

## Organization Secrets

### Sharing Across Repos

1. Go to Organization → Settings → Secrets and variables → Actions
2. Create secret
3. Select which repos can access it

```yaml
# Available to all repos with access
jobs:
  deploy:
    steps:
      - env:
          NPM_TOKEN: ${{ secrets.ORG_NPM_TOKEN }}
        run: npm publish
```

## Environment Variables

### Workflow-Level

```yaml
env:
  NODE_ENV: production
  CI: true

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - run: echo $NODE_ENV  # production
```

### Job-Level

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    env:
      DATABASE_URL: postgres://localhost/test

    steps:
      - run: echo $DATABASE_URL
```

### Step-Level

```yaml
steps:
  - name: Build
    env:
      OPTIMIZE: true
    run: npm run build
```

### Dynamic Environment Variables

```yaml
steps:
  - name: Set version
    run: |
      VERSION=$(cat version.txt)
      echo "VERSION=$VERSION" >> $GITHUB_ENV

  - name: Use version
    run: echo "Building version $VERSION"
```

### Multi-line Environment Variables

```yaml
steps:
  - name: Set multi-line env
    run: |
      echo 'CONFIG<<EOF' >> $GITHUB_ENV
      cat config.json >> $GITHUB_ENV
      echo 'EOF' >> $GITHUB_ENV

  - name: Use config
    run: echo "$CONFIG"
```

## GitHub Token

### Automatic GITHUB_TOKEN

```yaml
jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Create Release
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          gh release create v1.0.0 --generate-notes
```

### Token Permissions

```yaml
# Workflow-level permissions
permissions:
  contents: write
  packages: write
  pull-requests: write

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: gh release create v1.0.0
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### Job-Level Permissions

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      contents: read  # Minimal permissions

    steps:
      - uses: actions/checkout@v4
      - run: npm run build

  deploy:
    runs-on: ubuntu-latest
    permissions:
      contents: write
      deployments: write

    steps:
      - uses: actions/checkout@v4
      - run: ./deploy.sh
```

## Variables (Non-Sensitive)

### Repository Variables

1. Go to Repository → Settings → Secrets and variables → Actions → Variables
2. Create variable

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - run: echo "App name: ${{ vars.APP_NAME }}"
      - run: echo "Region: ${{ vars.DEPLOY_REGION }}"
```

### Environment Variables

```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production
    steps:
      - run: echo "URL: ${{ vars.API_URL }}"  # From production environment
```

## Secure Patterns

### Don't Echo Secrets

```yaml
# BAD - Secret might leak in logs
- run: echo "Key: ${{ secrets.API_KEY }}"

# GOOD - Use environment variable
- env:
    API_KEY: ${{ secrets.API_KEY }}
  run: curl -H "Authorization: Bearer $API_KEY" https://api.example.com
```

### Mask Dynamic Secrets

```yaml
steps:
  - name: Get token
    id: token
    run: |
      TOKEN=$(generate-token)
      echo "::add-mask::$TOKEN"
      echo "token=$TOKEN" >> $GITHUB_OUTPUT

  - name: Use token
    run: curl -H "Auth: ${{ steps.token.outputs.token }}" https://api.example.com
```

### Secure File Handling

```yaml
steps:
  - name: Write key file
    run: |
      echo "${{ secrets.SSH_PRIVATE_KEY }}" > key.pem
      chmod 600 key.pem

  - name: Use key
    run: ssh -i key.pem user@server

  - name: Cleanup
    if: always()
    run: rm -f key.pem
```

### Validate Required Secrets

```yaml
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - name: Check required secrets
        run: |
          if [ -z "${{ secrets.API_KEY }}" ]; then
            echo "::error::API_KEY secret is required"
            exit 1
          fi
          if [ -z "${{ secrets.DATABASE_URL }}" ]; then
            echo "::error::DATABASE_URL secret is required"
            exit 1
          fi
```

## Common Secret Patterns

### Docker Registry

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Login to Docker Hub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          push: true
          tags: user/app:latest
```

### Cloud Provider

```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1

      - name: Deploy to AWS
        run: aws s3 sync ./dist s3://my-bucket
```

### SSH Deployment

```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Setup SSH
        run: |
          mkdir -p ~/.ssh
          echo "${{ secrets.SSH_PRIVATE_KEY }}" > ~/.ssh/deploy_key
          chmod 600 ~/.ssh/deploy_key
          echo "${{ secrets.SSH_KNOWN_HOSTS }}" > ~/.ssh/known_hosts

      - name: Deploy
        run: |
          rsync -avz -e "ssh -i ~/.ssh/deploy_key" ./dist/ user@server:/app/

      - name: Cleanup
        if: always()
        run: rm -rf ~/.ssh/deploy_key
```

### NPM Publishing

```yaml
jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
          registry-url: "https://registry.npmjs.org"

      - run: npm ci
      - run: npm publish
        env:
          NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}
```
