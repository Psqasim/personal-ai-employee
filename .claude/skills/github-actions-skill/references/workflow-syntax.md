# Workflow Syntax

## File Structure

```yaml
# .github/workflows/workflow-name.yml
name: Workflow Display Name

on: [push, pull_request]  # Triggers

env:                       # Global environment variables
  NODE_ENV: production

jobs:
  job-name:                # Job definition
    runs-on: ubuntu-latest
    steps:
      - name: Step name
        run: echo "Hello"
```

## Triggers (on)

### Push and Pull Request

```yaml
on:
  push:
    branches:
      - main
      - "release/**"       # Glob pattern
    branches-ignore:
      - "feature/**"
    paths:
      - "src/**"           # Only run if src/ changed
      - "!src/**/*.md"     # Exclude markdown
    tags:
      - "v*"               # Tags starting with v

  pull_request:
    branches: [main]
    types: [opened, synchronize, reopened]
```

### Schedule (Cron)

```yaml
on:
  schedule:
    - cron: "0 0 * * *"    # Daily at midnight UTC
    - cron: "0 */6 * * *"  # Every 6 hours
    - cron: "0 9 * * 1"    # Mondays at 9 AM UTC

# Cron syntax: minute hour day-of-month month day-of-week
# Examples:
# "0 0 * * *"   = Daily at midnight
# "0 0 * * 0"   = Weekly on Sunday
# "0 0 1 * *"   = Monthly on the 1st
```

### Manual Trigger

```yaml
on:
  workflow_dispatch:
    inputs:
      environment:
        description: "Deployment environment"
        required: true
        default: "staging"
        type: choice
        options:
          - staging
          - production
      debug:
        description: "Enable debug mode"
        required: false
        type: boolean
        default: false

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to ${{ inputs.environment }}
        run: ./deploy.sh ${{ inputs.environment }}
        env:
          DEBUG: ${{ inputs.debug }}
```

### Release Events

```yaml
on:
  release:
    types: [published, created, released]

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - name: Get release info
        run: |
          echo "Tag: ${{ github.event.release.tag_name }}"
          echo "Name: ${{ github.event.release.name }}"
```

### Workflow Call (Reusable)

```yaml
# Caller workflow
on:
  push:
    branches: [main]

jobs:
  call-reusable:
    uses: ./.github/workflows/reusable.yml
    with:
      environment: production
    secrets:
      API_KEY: ${{ secrets.API_KEY }}

# Reusable workflow (.github/workflows/reusable.yml)
on:
  workflow_call:
    inputs:
      environment:
        required: true
        type: string
    secrets:
      API_KEY:
        required: true

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - run: echo "Deploying to ${{ inputs.environment }}"
```

## Jobs

### Basic Job

```yaml
jobs:
  build:
    name: Build Application
    runs-on: ubuntu-latest
    timeout-minutes: 30

    steps:
      - uses: actions/checkout@v4
      - run: npm ci
      - run: npm run build
```

### Job Dependencies

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - run: npm test

  build:
    needs: test  # Wait for test to complete
    runs-on: ubuntu-latest
    steps:
      - run: npm run build

  deploy:
    needs: [test, build]  # Wait for multiple jobs
    runs-on: ubuntu-latest
    steps:
      - run: ./deploy.sh
```

### Conditional Jobs

```yaml
jobs:
  deploy-staging:
    if: github.ref == 'refs/heads/develop'
    runs-on: ubuntu-latest
    steps:
      - run: ./deploy.sh staging

  deploy-production:
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - run: ./deploy.sh production

  # Only on PR
  lint:
    if: github.event_name == 'pull_request'
    runs-on: ubuntu-latest
    steps:
      - run: npm run lint
```

### Job Outputs

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    outputs:
      version: ${{ steps.version.outputs.version }}
      artifact-path: ${{ steps.build.outputs.path }}

    steps:
      - id: version
        run: echo "version=$(cat version.txt)" >> $GITHUB_OUTPUT

      - id: build
        run: |
          npm run build
          echo "path=dist/" >> $GITHUB_OUTPUT

  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - name: Use outputs
        run: |
          echo "Deploying version ${{ needs.build.outputs.version }}"
          echo "From path ${{ needs.build.outputs.artifact-path }}"
```

## Steps

### Run Commands

```yaml
steps:
  - name: Single command
    run: echo "Hello World"

  - name: Multiple commands
    run: |
      echo "First command"
      echo "Second command"
      npm install
      npm test

  - name: With shell
    run: |
      Get-ChildItem
    shell: pwsh  # PowerShell

  - name: With working directory
    run: npm test
    working-directory: ./frontend
```

### Using Actions

```yaml
steps:
  # GitHub official action
  - uses: actions/checkout@v4

  # With inputs
  - uses: actions/setup-node@v4
    with:
      node-version: "20"
      cache: "npm"

  # Specific version
  - uses: actions/upload-artifact@v4
    with:
      name: my-artifact
      path: dist/

  # From another repository
  - uses: owner/repo@v1
    with:
      input1: value1
```

### Conditional Steps

```yaml
steps:
  - name: Always run
    run: echo "Always"

  - name: Only on main
    if: github.ref == 'refs/heads/main'
    run: echo "On main branch"

  - name: Only on PR
    if: github.event_name == 'pull_request'
    run: echo "On pull request"

  - name: Only on success
    if: success()
    run: echo "Previous steps succeeded"

  - name: Only on failure
    if: failure()
    run: echo "Previous steps failed"

  - name: Always run (even on failure)
    if: always()
    run: echo "Cleanup"

  - name: Skip on fork PRs
    if: github.event.pull_request.head.repo.full_name == github.repository
    run: echo "Not a fork"
```

## Expressions

### Context Variables

```yaml
steps:
  - name: GitHub context
    run: |
      echo "Repository: ${{ github.repository }}"
      echo "Branch: ${{ github.ref_name }}"
      echo "SHA: ${{ github.sha }}"
      echo "Actor: ${{ github.actor }}"
      echo "Event: ${{ github.event_name }}"
      echo "Run ID: ${{ github.run_id }}"
      echo "Run Number: ${{ github.run_number }}"

  - name: Env context
    run: echo "CI: ${{ env.CI }}"

  - name: Secrets context
    run: echo "Has secret: ${{ secrets.MY_SECRET != '' }}"

  - name: Job context
    run: echo "Status: ${{ job.status }}"
```

### Operators and Functions

```yaml
steps:
  # String comparison
  - if: github.ref == 'refs/heads/main'
    run: echo "Main branch"

  # Contains
  - if: contains(github.event.head_commit.message, '[skip ci]')
    run: echo "Skipping CI"

  # StartsWith / EndsWith
  - if: startsWith(github.ref, 'refs/tags/')
    run: echo "Is a tag"

  # Boolean operators
  - if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    run: echo "Push to main"

  # Format string
  - name: Format example
    run: echo "${{ format('Hello {0} {1}', 'World', '!') }}"

  # JSON functions
  - name: To JSON
    run: echo '${{ toJSON(github.event) }}'
```

## Environment Variables

### Setting Environment Variables

```yaml
env:
  GLOBAL_VAR: "available everywhere"

jobs:
  example:
    env:
      JOB_VAR: "available in this job"

    steps:
      - name: Step with env
        env:
          STEP_VAR: "available in this step"
        run: |
          echo "$GLOBAL_VAR"
          echo "$JOB_VAR"
          echo "$STEP_VAR"

      - name: Set env for subsequent steps
        run: echo "DYNAMIC_VAR=value" >> $GITHUB_ENV

      - name: Use dynamic env
        run: echo "$DYNAMIC_VAR"
```

### Default Environment Variables

```yaml
steps:
  - name: Default vars
    run: |
      echo "CI: $CI"
      echo "GITHUB_REPOSITORY: $GITHUB_REPOSITORY"
      echo "GITHUB_REF: $GITHUB_REF"
      echo "GITHUB_SHA: $GITHUB_SHA"
      echo "GITHUB_ACTOR: $GITHUB_ACTOR"
      echo "GITHUB_WORKSPACE: $GITHUB_WORKSPACE"
      echo "RUNNER_OS: $RUNNER_OS"
```

## Runners

### GitHub-Hosted

```yaml
jobs:
  linux:
    runs-on: ubuntu-latest    # Also: ubuntu-22.04, ubuntu-20.04

  windows:
    runs-on: windows-latest   # Also: windows-2022, windows-2019

  macos:
    runs-on: macos-latest     # Also: macos-14, macos-13

  # Larger runners (GitHub Team/Enterprise)
  large:
    runs-on: ubuntu-latest-16-cores
```

### Self-Hosted

```yaml
jobs:
  build:
    runs-on: self-hosted

  # With labels
  deploy:
    runs-on: [self-hosted, linux, gpu]
```

## Services (Containers)

```yaml
jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: testdb
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

      redis:
        image: redis:7
        ports:
          - 6379:6379

    steps:
      - uses: actions/checkout@v4
      - name: Run tests
        env:
          DATABASE_URL: postgresql://test:test@localhost:5432/testdb
          REDIS_URL: redis://localhost:6379
        run: pytest
```
