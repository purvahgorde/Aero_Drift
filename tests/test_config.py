"""Tests for the configuration loading module (app.config).

All tests use temporary YAML files so they are fully self-contained.
"""

import os
import tempfile
import unittest

from app.config import load_config, AeroConfig, ConfigError


class TestLoadValidConfig(unittest.TestCase):
    """Test that a well-formed config file loads successfully."""

    def test_load_valid_config(self):
        content = (
            "app:\n"
            "  name: TestApp\n"
            "  description: A test application\n"
            "  version: '1.0.0'\n"
            "aws:\n"
            "  region: eu-west-1\n"
        )
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        ) as fh:
            fh.write(content)
            path = fh.name
        try:
            config = load_config(path)
            self.assertIsInstance(config, AeroConfig)
        finally:
            os.unlink(path)


class TestConfigValueAccess(unittest.TestCase):
    """Test that configuration values can be accessed correctly."""

    def setUp(self):
        content = (
            "app:\n"
            "  name: AeroDrift\n"
            "  description: Cloud Platform\n"
            "  version: '0.1.0'\n"
            "aws:\n"
            "  region: us-east-1\n"
            "  mock_data_path: data/mock_aws_state.json\n"
            "logging:\n"
            "  level: DEBUG\n"
            "  verbose: true\n"
        )
        self._tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        )
        self._tmp.write(content)
        self._tmp.close()
        self.config = load_config(self._tmp.name)

    def tearDown(self):
        os.unlink(self._tmp.name)

    def test_attribute_access(self):
        self.assertEqual(self.config.app.name, "AeroDrift")
        self.assertEqual(self.config.aws.region, "us-east-1")

    def test_dict_style_access(self):
        self.assertEqual(self.config["app"]["name"], "AeroDrift")

    def test_get_with_default(self):
        self.assertIsNone(self.config.get("nonexistent"))
        self.assertEqual(self.config.get("nonexistent", "fallback"), "fallback")

    def test_contains(self):
        self.assertIn("app", self.config)
        self.assertNotIn("nonexistent", self.config)

    def test_keys(self):
        keys = self.config.keys()
        self.assertIn("app", keys)
        self.assertIn("aws", keys)
        self.assertIn("logging", keys)

    def test_to_dict(self):
        d = self.config.to_dict()
        self.assertIsInstance(d, dict)
        self.assertIn("app", d)


class TestMissingConfigFile(unittest.TestCase):
    """Test that a missing config file raises ConfigError."""

    def test_missing_file_raises_config_error(self):
        with self.assertRaises(ConfigError) as ctx:
            load_config("/nonexistent/path/config.yaml")
        self.assertIn("not found", str(ctx.exception))

    def test_missing_file_error_message_includes_path(self):
        path = "/tmp/does_not_exist_config.yaml"
        with self.assertRaises(ConfigError) as ctx:
            load_config(path)
        self.assertIn(path, str(ctx.exception))


class TestInvalidYAML(unittest.TestCase):
    """Test that malformed YAML raises ConfigError."""

    def test_invalid_yaml_raises_config_error(self):
        content = "app:\n  name: [invalid yaml\n  broken: {{\n"
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        ) as fh:
            fh.write(content)
            path = fh.name
        try:
            with self.assertRaises(ConfigError) as ctx:
                load_config(path)
            self.assertIn("Invalid YAML", str(ctx.exception))
        finally:
            os.unlink(path)


class TestMissingRequiredKeys(unittest.TestCase):
    """Test that missing required keys are detected."""

    def test_missing_app_section(self):
        content = "aws:\n  region: us-east-1\n"
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        ) as fh:
            fh.write(content)
            path = fh.name
        try:
            with self.assertRaises(ConfigError) as ctx:
                load_config(path)
            self.assertIn("app", str(ctx.exception))
        finally:
            os.unlink(path)

    def test_missing_app_name(self):
        content = "app:\n  description: No name here\n"
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        ) as fh:
            fh.write(content)
            path = fh.name
        try:
            with self.assertRaises(ConfigError) as ctx:
                load_config(path)
            self.assertIn("app.name", str(ctx.exception))
        finally:
            os.unlink(path)


class TestNestedConfigValues(unittest.TestCase):
    """Test that nested YAML sections work correctly."""

    def test_nested_access(self):
        content = (
            "app:\n"
            "  name: AeroDrift\n"
            "  metadata:\n"
            "    author: Team4\n"
            "    tags:\n"
            "      - cloud\n"
            "      - topology\n"
        )
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        ) as fh:
            fh.write(content)
            path = fh.name
        try:
            config = load_config(path)
            self.assertEqual(config.app.metadata.author, "Team4")
            self.assertIsInstance(config.app.metadata.tags, list)
            self.assertIn("cloud", config.app.metadata.tags)
        finally:
            os.unlink(path)


class TestDefaultValues(unittest.TestCase):
    """Test that missing optional keys are filled with defaults."""

    def test_defaults_for_missing_sections(self):
        # Provide only the required keys — optional sections should get defaults
        content = "app:\n  name: Minimal\n"
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        ) as fh:
            fh.write(content)
            path = fh.name
        try:
            config = load_config(path)
            # aws and logging sections should have defaults
            self.assertEqual(config.aws.region, "us-east-1")
            self.assertEqual(config.logging.level, "INFO")
            self.assertFalse(config.logging.verbose)
        finally:
            os.unlink(path)

    def test_partial_section_gets_defaults(self):
        # Provide aws.region but not aws.mock_data_path
        content = (
            "app:\n"
            "  name: Partial\n"
            "aws:\n"
            "  region: ap-south-1\n"
        )
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        ) as fh:
            fh.write(content)
            path = fh.name
        try:
            config = load_config(path)
            self.assertEqual(config.aws.region, "ap-south-1")
            self.assertEqual(config.aws.mock_data_path, "data/mock_aws_state.json")
        finally:
            os.unlink(path)


class TestTypeHandling(unittest.TestCase):
    """Test that YAML types are preserved correctly."""

    def test_types_preserved(self):
        content = (
            "app:\n"
            "  name: TypeTest\n"
            "  count: 42\n"
            "  enabled: true\n"
            "  tags:\n"
            "    - alpha\n"
            "    - beta\n"
            "  metadata:\n"
            "    key1: value1\n"
            "    key2: value2\n"
        )
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        ) as fh:
            fh.write(content)
            path = fh.name
        try:
            config = load_config(path)
            self.assertIsInstance(config.app.name, str)
            self.assertIsInstance(config.app.count, int)
            self.assertIsInstance(config.app.enabled, bool)
            self.assertIsInstance(config.app.tags, list)
            self.assertEqual(config.app.count, 42)
            self.assertTrue(config.app.enabled)
            self.assertEqual(config.app.tags, ["alpha", "beta"])
            self.assertEqual(config.app.metadata.key1, "value1")
        finally:
            os.unlink(path)


class TestEmptyConfigFile(unittest.TestCase):
    """Test that an empty YAML file raises ConfigError."""

    def test_empty_file(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        ) as fh:
            fh.write("")
            path = fh.name
        try:
            with self.assertRaises(ConfigError) as ctx:
                load_config(path)
            self.assertIn("empty", str(ctx.exception).lower())
        finally:
            os.unlink(path)

    def test_comments_only_file(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        ) as fh:
            fh.write("# just a comment\n# nothing here\n")
            path = fh.name
        try:
            with self.assertRaises(ConfigError) as ctx:
                load_config(path)
            self.assertIn("empty", str(ctx.exception).lower())
        finally:
            os.unlink(path)


class TestExtraUserKeys(unittest.TestCase):
    """Test that user-defined sections beyond defaults are preserved."""

    def test_extra_top_level_key(self):
        content = (
            "app:\n"
            "  name: AeroDrift\n"
            "custom:\n"
            "  feature_flag: true\n"
        )
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        ) as fh:
            fh.write(content)
            path = fh.name
        try:
            config = load_config(path)
            self.assertTrue(config.custom.feature_flag)
        finally:
            os.unlink(path)


class TestDefaultPathResolution(unittest.TestCase):
    """Test that load_config() finds config.yaml at the project root."""

    def test_default_path_loads_project_config(self):
        # This test relies on the actual config.yaml existing at project root
        config = load_config()
        self.assertEqual(config.app.name, "AeroDrift")


if __name__ == "__main__":
    unittest.main()
