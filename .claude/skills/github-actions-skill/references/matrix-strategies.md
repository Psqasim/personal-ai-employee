# Matrix Strategies

## Basic Matrix

### Single Dimension

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12"]

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - run: python --version
      - run: pytest
```

### Multiple Dimensions

```yaml
jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        python-version: ["3.10", "3.11", "3.12"]
        # Creates 3 x 3 = 9 jobs

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - run: pytest
```

### Node.js Matrix

```yaml
jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest]
        node-version: [18, 20, 22]

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node-version }}
      - run: npm ci
      - run: npm test
```

## Include and Exclude

### Include Additional Configurations

```yaml
jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest]
        python-version: ["3.10", "3.11", "3.12"]
        include:
          # Add specific configuration for latest Python on Ubuntu
          - os: ubuntu-latest
            python-version: "3.12"
            experimental: true
            coverage: true

          # Add macOS only for Python 3.12
          - os: macos-latest
            python-version: "3.12"

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Run tests
        run: pytest

      - name: Run with coverage
        if: matrix.coverage
        run: pytest --cov=src --cov-report=xml
```

### Exclude Specific Combinations

```yaml
jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        python-version: ["3.10", "3.11", "3.12"]
        exclude:
          # Skip Windows + Python 3.10 (known issues)
          - os: windows-latest
            python-version: "3.10"

          # Skip macOS for older Python versions
          - os: macos-latest
            python-version: "3.10"
          - os: macos-latest
            python-version: "3.11"
```

## Fail-Fast and Max Parallel

### Fail-Fast (Default: true)

```yaml
jobs:
  test:
    strategy:
      fail-fast: true  # Stop all jobs if one fails (default)
      matrix:
        python-version: ["3.10", "3.11", "3.12"]

    steps:
      - run: pytest
```

### Continue on Failure

```yaml
jobs:
  test:
    strategy:
      fail-fast: false  # Continue other jobs even if one fails
      matrix:
        python-version: ["3.10", "3.11", "3.12"]

    steps:
      - run: pytest
```

### Limit Parallel Jobs

```yaml
jobs:
  test:
    strategy:
      max-parallel: 2  # Only run 2 jobs at a time
      matrix:
        python-version: ["3.10", "3.11", "3.12", "3.13"]
```

## Dynamic Matrix

### Using fromJSON

```yaml
jobs:
  setup:
    runs-on: ubuntu-latest
    outputs:
      matrix: ${{ steps.set-matrix.outputs.matrix }}

    steps:
      - id: set-matrix
        run: |
          echo 'matrix={"python-version":["3.10","3.11","3.12"],"os":["ubuntu-latest","windows-latest"]}' >> $GITHUB_OUTPUT

  test:
    needs: setup
    runs-on: ${{ matrix.os }}
    strategy:
      matrix: ${{ fromJSON(needs.setup.outputs.matrix) }}

    steps:
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - run: python --version
```

### From File

```yaml
jobs:
  setup:
    runs-on: ubuntu-latest
    outputs:
      matrix: ${{ steps.set-matrix.outputs.matrix }}

    steps:
      - uses: actions/checkout@v4
      - id: set-matrix
        run: |
          content=$(cat .github/matrix.json)
          echo "matrix=$content" >> $GITHUB_OUTPUT

  test:
    needs: setup
    strategy:
      matrix: ${{ fromJSON(needs.setup.outputs.matrix) }}
    # ...
```

## Advanced Patterns

### Database Matrix

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        database:
          - name: postgres
            image: postgres:15
            port: 5432
            env:
              POSTGRES_USER: test
              POSTGRES_PASSWORD: test
          - name: mysql
            image: mysql:8
            port: 3306
            env:
              MYSQL_ROOT_PASSWORD: test

    services:
      db:
        image: ${{ matrix.database.image }}
        ports:
          - ${{ matrix.database.port }}:${{ matrix.database.port }}
        env: ${{ matrix.database.env }}

    steps:
      - uses: actions/checkout@v4
      - run: pytest --database=${{ matrix.database.name }}
```

### Framework Matrix

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        include:
          - framework: django
            python-version: "3.12"
            test-command: python manage.py test

          - framework: flask
            python-version: "3.12"
            test-command: pytest

          - framework: fastapi
            python-version: "3.12"
            test-command: pytest

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install ${{ matrix.framework }}
        run: pip install -e ".[dev]"

      - name: Test ${{ matrix.framework }}
        run: ${{ matrix.test-command }}
```

### Conditional Matrix Values

```yaml
jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest]
        python-version: ["3.11", "3.12"]
        include:
          - os: ubuntu-latest
            python-version: "3.12"
            upload-coverage: true

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Run tests
        run: pytest --cov=src

      - name: Upload coverage
        if: matrix.upload-coverage == true
        uses: codecov/codecov-action@v4
```

## Reusable Matrix Workflows

### Reusable Workflow

```yaml
# .github/workflows/test-python.yml
name: Python Test

on:
  workflow_call:
    inputs:
      python-versions:
        required: true
        type: string  # JSON array

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ${{ fromJSON(inputs.python-versions) }}

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - run: pip install -e ".[dev]"
      - run: pytest
```

### Caller Workflow

```yaml
# .github/workflows/ci.yml
name: CI

on: [push, pull_request]

jobs:
  test:
    uses: ./.github/workflows/test-python.yml
    with:
      python-versions: '["3.10", "3.11", "3.12"]'
```

## Best Practices

### 1. Test Minimum and Maximum Versions

```yaml
strategy:
  matrix:
    python-version: ["3.10", "3.12"]  # Oldest and newest supported
```

### 2. Use fail-fast: false for Comprehensive Testing

```yaml
strategy:
  fail-fast: false  # See all failures, not just the first
  matrix:
    python-version: ["3.10", "3.11", "3.12"]
```

### 3. Limit Matrix Size

```yaml
# Instead of 3 OS x 4 Python = 12 jobs
strategy:
  matrix:
    os: [ubuntu-latest]  # Primary
    python-version: ["3.10", "3.11", "3.12"]
    include:
      # Add minimal cross-platform coverage
      - os: windows-latest
        python-version: "3.12"
      - os: macos-latest
        python-version: "3.12"
```

### 4. Name Matrix Jobs Clearly

```yaml
jobs:
  test:
    name: Test Python ${{ matrix.python-version }} on ${{ matrix.os }}
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest]
        python-version: ["3.11", "3.12"]
```
