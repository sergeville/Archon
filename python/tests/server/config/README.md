# Configuration Validation Tests

**Purpose**: Automated tests to validate configuration consistency, environment variables, and prevent runtime configuration errors.

**Location**: `python/tests/server/config/test_config_validation.py`

---

## Test Coverage

### 1. OpenAI API Key Validation
Tests: `TestOpenAIKeyValidation`

- ✅ Valid key format (starts with `sk-`)
- ✅ Empty key rejection
- ✅ Invalid prefix rejection

### 2. OpenRouter API Key Validation
Tests: `TestOpenRouterKeyValidation`

- ✅ Valid key format (starts with `sk-or-v1-`)
- ✅ Empty key rejection
- ✅ Invalid prefix rejection
- ✅ OpenAI key format rejection (common mistake)

### 3. Supabase Key Validation
Tests: `TestSupabaseKeyValidation`

- ✅ Service role key acceptance
- ✅ Anon key rejection (critical security check)
- ✅ Unknown role rejection
- ✅ Empty key rejection
- ✅ Non-JWT key handling

### 4. Supabase URL Validation
Tests: `TestSupabaseURLValidation`

- ✅ HTTPS URL validation
- ✅ HTTP localhost allowance
- ✅ HTTP Docker internal allowance
- ✅ HTTP private IP allowance
- ✅ Production HTTP rejection
- ✅ Empty URL rejection
- ✅ Invalid scheme rejection

### 5. Environment Configuration Loading
Tests: `TestEnvironmentConfigLoading`

- ✅ Missing required variables detection
- ✅ Invalid PORT format rejection
- ✅ Anon key startup prevention
- ✅ Valid configuration loading

### 6. Environment File Consistency
Tests: `TestEnvFileConsistency`

- ✅ Critical variables documented in `.env.example`
- ✅ Frontend variables documented
- ✅ Port variables consistency

### 7. Port Configuration
Tests: `TestPortConfiguration`

- ✅ Default port uniqueness (prevents conflicts)

### 8. Boolean Parsing
Tests: `TestBooleanParsing`

- ✅ Various `true` values (`"true"`, `"1"`, `"yes"`, `"on"`)
- ✅ Various `false` values (`"false"`, `"0"`, `"no"`, `"off"`, `""`)
- ✅ Unset variable handling (defaults to `false`)

---

## Running Tests

### Prerequisites

```bash
cd python
uv sync  # or uv sync --group all for full dependencies
```

### Run All Config Tests

```bash
uv run pytest tests/server/config/test_config_validation.py -v
```

### Run Specific Test Class

```bash
# Test only OpenAI validation
uv run pytest tests/server/config/test_config_validation.py::TestOpenAIKeyValidation -v

# Test only Supabase validation
uv run pytest tests/server/config/test_config_validation.py::TestSupabaseKeyValidation -v
```

### Run With Coverage

```bash
uv run pytest tests/server/config/test_config_validation.py --cov=src.server.config --cov-report=term-missing
```

---

## What These Tests Prevent

### 1. Common Mistakes
- ❌ Using Supabase anon key instead of service key
- ❌ Using HTTP for production Supabase URLs
- ❌ Using OpenAI key format for OpenRouter
- ❌ Missing required environment variables
- ❌ Port conflicts between services

### 2. Runtime Failures
- ❌ Database permission errors from wrong key type
- ❌ Configuration load failures at startup
- ❌ Invalid API key formats causing crashes
- ❌ Boolean environment variables parsing incorrectly

### 3. Documentation Drift
- ❌ `.env.example` missing required variables
- ❌ Undocumented configuration options
- ❌ Inconsistent port assignments

---

## Integration with CI/CD

Add to GitHub Actions workflow:

```yaml
- name: Run Configuration Tests
  run: |
    cd python
    uv sync
    uv run pytest tests/server/config/test_config_validation.py -v
```

---

## Maintenance

### Adding New Configuration

When adding new environment variables:

1. Add validation function in `src/server/config/config.py`
2. Add tests in `test_config_validation.py`
3. Update `.env.example` files
4. Add test to verify `.env.example` includes new variable

### Example: Adding New API Key Validation

```python
# In config.py
def validate_myapi_key(api_key: str) -> bool:
    if not api_key:
        raise ConfigurationError("MyAPI key cannot be empty")
    if not api_key.startswith("myapi-"):
        raise ConfigurationError("MyAPI key must start with 'myapi-'")
    return True

# In test_config_validation.py
class TestMyAPIKeyValidation:
    def test_valid_myapi_key(self):
        assert validate_myapi_key("myapi-1234567890")

    def test_invalid_prefix(self):
        with pytest.raises(ConfigurationError, match="must start with 'myapi-'"):
            validate_myapi_key("wrong-prefix-1234")
```

---

## Test Statistics

**Total Test Classes**: 8
**Total Test Methods**: 35+
**Coverage Target**: >90% of `config.py`

---

**Created**: 2026-02-18
**Last Updated**: 2026-02-18
**Maintainer**: Archon Development Team
