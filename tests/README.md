# 🧪 Test Suite

Comprehensive test suite for Personal AI Employee (Bronze, Silver, Gold tiers).

## 📁 Structure

```
tests/
├── unit/                    # Unit tests (pytest)
│   └── test_ai_analyzer.py
├── integration/             # Integration tests
│   └── test_gmail_watcher.py
├── live/                    # Live API tests (REAL APIs)
│   ├── test_mcp_servers.py        # MCP connectivity (5 servers)
│   ├── test_gold_simple.py        # Simplified Gold tests (37/38 PASS)
│   └── test_gold_tier_complete.py # Comprehensive Gold tests
├── manual/                  # Manual setup & testing scripts
│   ├── whatsapp_quick_setup.py    # WhatsApp QR authentication
│   ├── linkedin_permission_test.py
│   └── test_whatsapp*.py
└── fixtures/                # Test data
    ├── mock_claude_responses.json
    └── mock_gmail_data.json
```

## 🚀 Running Tests

### Live MCP Server Tests
```bash
cd /path/to/project
source .venv/bin/activate
python3 tests/live/test_mcp_servers.py
# Expected: 5/5 servers operational
```

### Simplified Gold Tier Tests
```bash
python3 tests/live/test_gold_simple.py
# Expected: 37/38 tests passing (97% - Grade A+)
```

### Comprehensive Gold Tests
```bash
python3 tests/live/test_gold_tier_complete.py
# Tests all automation flows without live API calls
```

### Unit Tests (pytest)
```bash
pytest tests/unit/ -v
```

### Integration Tests
```bash
pytest tests/integration/ -v
```

## 📊 Test Results Summary

| Test Suite | Status | Score | Details |
|------------|--------|-------|---------|
| **MCP Connectivity** | ✅ PASS | 5/5 (100%) | All servers operational |
| **Gold Tier Simple** | ✅ PASS | 37/38 (97%) | Grade A+ |
| **Unit Tests** | ✅ PASS | 88% coverage | Exceeds 80% target |
| **Live Email Test** | ✅ PASS | Working | Confirmed delivery |

## 🔧 Manual Setup Scripts

### WhatsApp QR Authentication
```bash
python3 tests/manual/whatsapp_quick_setup.py
# Scan QR code with phone
# Session persists at ~/.whatsapp_session
```

### LinkedIn Permission Test
```bash
python3 tests/manual/linkedin_permission_test.py
# Test LinkedIn API token permissions
```

## 📝 Test Coverage

- **Overall:** 88% (exceeds 80% target)
- **agent_skills/**: 87-94% per module
- **mcp_servers/**: Tested via live integration tests

## 🎯 CI/CD Integration

Tests are designed to run in CI/CD pipelines:
- Unit tests: Fast (<5s)
- Integration tests: Medium (<30s)
- Live tests: Manual trigger only (avoid API costs)

## 📍 Related Documentation

- Test reports: `docs/reports/`
- Setup guides: `docs/gold/`
- Validation results: `docs/reports/FINAL-GOLD-VALIDATION-REPORT.md`
