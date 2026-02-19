"""
Automated Configuration Validation Tests

Tests configuration consistency, environment variables, and validation logic
to prevent runtime configuration errors and deployment issues.
"""

import os
import pytest
from pathlib import Path

from src.server.config.config import (
    ConfigurationError,
    validate_openai_api_key,
    validate_openrouter_api_key,
    validate_supabase_key,
    validate_supabase_url,
    load_environment_config,
)


class TestOpenAIKeyValidation:
    """Test OpenAI API key validation"""

    def test_valid_openai_key(self):
        """Valid OpenAI key should pass"""
        assert validate_openai_api_key("sk-1234567890abcdef")

    def test_empty_openai_key(self):
        """Empty key should raise error"""
        with pytest.raises(ConfigurationError, match="cannot be empty"):
            validate_openai_api_key("")

    def test_invalid_prefix(self):
        """Key without sk- prefix should raise error"""
        with pytest.raises(ConfigurationError, match="must start with 'sk-'"):
            validate_openai_api_key("invalid-key-format")


class TestOpenRouterKeyValidation:
    """Test OpenRouter API key validation"""

    def test_valid_openrouter_key(self):
        """Valid OpenRouter key should pass"""
        assert validate_openrouter_api_key("sk-or-v1-1234567890abcdef")

    def test_empty_openrouter_key(self):
        """Empty key should raise error"""
        with pytest.raises(ConfigurationError, match="cannot be empty"):
            validate_openrouter_api_key("")

    def test_invalid_prefix(self):
        """Key without sk-or-v1- prefix should raise error"""
        with pytest.raises(ConfigurationError, match="must start with 'sk-or-v1-'"):
            validate_openrouter_api_key("sk-invalid-format")

    def test_openai_key_as_openrouter(self):
        """OpenAI key format should not be valid for OpenRouter"""
        with pytest.raises(ConfigurationError, match="must start with 'sk-or-v1-'"):
            validate_openrouter_api_key("sk-1234567890abcdef")


class TestSupabaseKeyValidation:
    """Test Supabase key validation"""

    def test_empty_key(self):
        """Empty key should return invalid"""
        is_valid, message = validate_supabase_key("")
        assert not is_valid
        assert message == "EMPTY_KEY"

    def test_service_role_key(self):
        """Service role JWT should be valid"""
        # Real-ish service role JWT (role claim = service_role)
        service_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoic2VydmljZV9yb2xlIiwiaXNzIjoic3VwYWJhc2UiLCJpYXQiOjE2NDcyNzA0MDAsImV4cCI6MTk2MjY3NjgwMH0.fake_signature"
        is_valid, message = validate_supabase_key(service_key)
        assert is_valid
        assert message == "VALID_SERVICE_KEY"

    def test_anon_key_rejected(self):
        """Anon key JWT should be rejected"""
        # Real-ish anon JWT (role claim = anon)
        anon_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoiYW5vbiIsImlzcyI6InN1cGFiYXNlIiwiaWF0IjoxNjQ3MjcwNDAwLCJleHAiOjE5NjI2NzY4MDB9.fake_signature"
        is_valid, message = validate_supabase_key(anon_key)
        assert not is_valid
        assert message == "ANON_KEY_DETECTED"

    def test_unknown_role(self):
        """Unknown role in JWT should be rejected"""
        # JWT with unknown role
        unknown_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoidW5rbm93biIsImlzcyI6InN1cGFiYXNlIiwiaWF0IjoxNjQ3MjcwNDAwLCJleHAiOjE5NjI2NzY4MDB9.fake_signature"
        is_valid, message = validate_supabase_key(unknown_key)
        assert not is_valid
        assert message.startswith("UNKNOWN_KEY_TYPE:")

    def test_non_jwt_key(self):
        """Non-JWT key should return unable to validate (allowing new formats)"""
        is_valid, message = validate_supabase_key("not-a-jwt-token")
        assert is_valid  # Allows unknown formats to proceed
        assert message == "UNABLE_TO_VALIDATE"


class TestSupabaseURLValidation:
    """Test Supabase URL validation"""

    def test_valid_https_url(self):
        """HTTPS URL should be valid"""
        assert validate_supabase_url("https://abc123.supabase.co")

    def test_localhost_http_allowed(self):
        """HTTP localhost should be allowed"""
        assert validate_supabase_url("http://localhost:8000")
        assert validate_supabase_url("http://127.0.0.1:8000")

    def test_docker_internal_http_allowed(self):
        """HTTP host.docker.internal should be allowed"""
        assert validate_supabase_url("http://host.docker.internal:8000")

    def test_private_ip_http_allowed(self):
        """HTTP private IP addresses should be allowed"""
        assert validate_supabase_url("http://192.168.1.100:8000")  # Class C
        assert validate_supabase_url("http://10.0.0.1:8000")  # Class A
        assert validate_supabase_url("http://172.16.0.1:8000")  # Class B

    def test_production_http_rejected(self):
        """HTTP production URL should be rejected"""
        with pytest.raises(ConfigurationError, match="must use HTTPS for non-local"):
            validate_supabase_url("http://example.com")

    def test_empty_url(self):
        """Empty URL should raise error"""
        with pytest.raises(ConfigurationError, match="cannot be empty"):
            validate_supabase_url("")

    def test_invalid_scheme(self):
        """Invalid scheme should raise error"""
        with pytest.raises(ConfigurationError, match="must use HTTP or HTTPS"):
            validate_supabase_url("ftp://example.com")

    def test_missing_netloc(self):
        """URL without netloc should raise error"""
        with pytest.raises(ConfigurationError, match="Invalid Supabase URL"):
            validate_supabase_url("https://")


class TestEnvironmentConfigLoading:
    """Test environment configuration loading"""

    def test_missing_supabase_url(self, monkeypatch):
        """Missing SUPABASE_URL should raise error"""
        monkeypatch.delenv("SUPABASE_URL", raising=False)
        monkeypatch.setenv("SUPABASE_SERVICE_KEY", "test")
        monkeypatch.setenv("PORT", "8051")

        with pytest.raises(ConfigurationError, match="SUPABASE_URL.*required"):
            load_environment_config()

    def test_missing_supabase_key(self, monkeypatch):
        """Missing SUPABASE_SERVICE_KEY should raise error"""
        monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
        monkeypatch.delenv("SUPABASE_SERVICE_KEY", raising=False)
        monkeypatch.setenv("PORT", "8051")

        with pytest.raises(ConfigurationError, match="SUPABASE_SERVICE_KEY.*required"):
            load_environment_config()

    def test_missing_port(self, monkeypatch):
        """Missing PORT should raise error"""
        service_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoic2VydmljZV9yb2xlIiwiaXNzIjoic3VwYWJhc2UifQ.fake"
        monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
        monkeypatch.setenv("SUPABASE_SERVICE_KEY", service_key)
        monkeypatch.delenv("PORT", raising=False)
        monkeypatch.delenv("ARCHON_MCP_PORT", raising=False)

        with pytest.raises(ConfigurationError, match="PORT.*ARCHON_MCP_PORT.*required"):
            load_environment_config()

    def test_invalid_port_format(self, monkeypatch):
        """Invalid PORT format should raise error"""
        service_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoic2VydmljZV9yb2xlIiwiaXNzIjoic3VwYWJhc2UifQ.fake"
        monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
        monkeypatch.setenv("SUPABASE_SERVICE_KEY", service_key)
        monkeypatch.setenv("PORT", "not-a-number")

        with pytest.raises(ConfigurationError, match="PORT must be a valid integer"):
            load_environment_config()

    def test_anon_key_prevents_startup(self, monkeypatch):
        """Using anon key should prevent startup with clear error"""
        anon_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoiYW5vbiIsImlzcyI6InN1cGFiYXNlIn0.fake"
        monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
        monkeypatch.setenv("SUPABASE_SERVICE_KEY", anon_key)
        monkeypatch.setenv("PORT", "8051")

        with pytest.raises(ConfigurationError, match="ANON key instead of a SERVICE key"):
            load_environment_config()

    def test_valid_config_loads(self, monkeypatch):
        """Valid configuration should load successfully"""
        service_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoic2VydmljZV9yb2xlIiwiaXNzIjoic3VwYWJhc2UifQ.fake"
        monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
        monkeypatch.setenv("SUPABASE_SERVICE_KEY", service_key)
        monkeypatch.setenv("PORT", "8051")

        config = load_environment_config()

        assert config.supabase_url == "https://test.supabase.co"
        assert config.supabase_service_key == service_key
        assert config.port == 8051
        assert config.host == "0.0.0.0"  # default
        assert config.transport == "sse"  # default


class TestEnvFileConsistency:
    """Test consistency between .env.example files"""

    @pytest.fixture
    def root_env_example(self):
        """Load root .env.example file"""
        path = Path(__file__).parents[3] / ".env.example"
        return self._parse_env_file(path)

    @pytest.fixture
    def frontend_env_example(self):
        """Load frontend .env.example file"""
        path = Path(__file__).parents[3] / "archon-ui-main" / ".env.example"
        return self._parse_env_file(path)

    @staticmethod
    def _parse_env_file(path: Path) -> dict:
        """Parse .env file and extract variable names"""
        variables = {}
        if not path.exists():
            return variables

        with open(path, 'r') as f:
            for line in f:
                line = line.strip()
                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue
                # Extract variable name
                if '=' in line:
                    var_name = line.split('=')[0].strip()
                    variables[var_name] = True

        return variables

    def test_critical_vars_documented(self, root_env_example):
        """Critical environment variables should be documented"""
        critical_vars = [
            "SUPABASE_URL",
            "SUPABASE_SERVICE_KEY",
            "ARCHON_SERVER_PORT",
            "ARCHON_MCP_PORT",
        ]

        for var in critical_vars:
            assert var in root_env_example, f"Critical variable {var} not documented in .env.example"

    def test_frontend_vars_documented(self, frontend_env_example):
        """Frontend variables should be documented"""
        frontend_vars = [
            "VITE_SHOW_DEVTOOLS",
        ]

        for var in frontend_vars:
            assert var in frontend_env_example, f"Frontend variable {var} not documented in archon-ui-main/.env.example"

    def test_port_variables_consistent(self, root_env_example):
        """All port variables should be documented"""
        port_vars = [
            "ARCHON_SERVER_PORT",
            "ARCHON_MCP_PORT",
            "ARCHON_AGENTS_PORT",
            "AGENT_WORK_ORDERS_PORT",
            "ARCHON_UI_PORT",
            "LLM_STREAMER_PORT",
        ]

        for var in port_vars:
            assert var in root_env_example, f"Port variable {var} not documented"


class TestPortConfiguration:
    """Test port configuration to prevent conflicts"""

    def test_default_ports_unique(self):
        """Default port values should not conflict"""
        default_ports = {
            "ARCHON_SERVER_PORT": 8181,
            "ARCHON_MCP_PORT": 8051,
            "ARCHON_AGENTS_PORT": 8052,
            "AGENT_WORK_ORDERS_PORT": 8053,
            "ARCHON_UI_PORT": 3737,
            "LLM_STREAMER_PORT": 8000,
        }

        port_values = list(default_ports.values())
        unique_ports = set(port_values)

        assert len(port_values) == len(unique_ports), f"Port conflict detected: {default_ports}"


class TestBooleanParsing:
    """Test boolean environment variable parsing"""

    def test_str_to_bool_true_values(self):
        """Test that various 'true' string values parse correctly"""
        from src.server.config.config import get_rag_strategy_config

        true_values = ["true", "True", "TRUE", "1", "yes", "Yes", "YES", "on", "On", "ON"]

        for val in true_values:
            os.environ["USE_HYBRID_SEARCH"] = val
            config = get_rag_strategy_config()
            assert config.use_hybrid_search is True, f"'{val}' should parse as True"
            del os.environ["USE_HYBRID_SEARCH"]

    def test_str_to_bool_false_values(self):
        """Test that various 'false' string values parse correctly"""
        from src.server.config.config import get_rag_strategy_config

        false_values = ["false", "False", "FALSE", "0", "no", "No", "NO", "off", "Off", "OFF", ""]

        for val in false_values:
            os.environ["USE_HYBRID_SEARCH"] = val
            config = get_rag_strategy_config()
            assert config.use_hybrid_search is False, f"'{val}' should parse as False"
            del os.environ["USE_HYBRID_SEARCH"]

    def test_str_to_bool_none_value(self):
        """Test that None/unset parses as False"""
        from src.server.config.config import get_rag_strategy_config

        # Ensure variable is not set
        if "USE_HYBRID_SEARCH" in os.environ:
            del os.environ["USE_HYBRID_SEARCH"]

        config = get_rag_strategy_config()
        assert config.use_hybrid_search is False, "Unset variable should default to False"
