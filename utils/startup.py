"""
Environment validation and startup checks.
"""
import os
import sys
from typing import List, Tuple

from utils.logger import app_logger


class StartupValidator:
    """Validates environment and dependencies on startup."""

    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate_all(self) -> bool:
        """Run all validations."""
        self._validate_python_version()
        self._validate_required_env_vars()
        self._validate_optional_env_vars()
        self._validate_directories()
        self._validate_dependencies()
        self._validate_gpu()

        return len(self.errors) == 0

    def _validate_python_version(self):
        """Check Python version."""
        required = (3, 9)
        current = sys.version_info[:2]

        if current < required:
            self.errors.append(
                f"Python {required[0]}.{required[1]}+ required, found {current[0]}.{current[1]}"
            )

    def _validate_required_env_vars(self):
        """Check required environment variables."""
        # No strictly required vars - all have defaults or are optional
        pass

    def _validate_optional_env_vars(self):
        """Check optional but recommended environment variables."""
        optional_vars = [
            ("DATABASE_URL", "PostgreSQL connection", "Using SQLite fallback"),
            ("JWT_SECRET_KEY", "JWT signing key", "⚠️ Using default - insecure!"),
            ("REDIS_URL", "Redis connection", "Caching disabled"),
            ("S3_ENDPOINT_URL", "S3 storage", "Using local storage"),
            ("SMTP_HOST", "Email notifications", "Email disabled"),
            ("SLACK_WEBHOOK_URL", "Slack notifications", "Slack disabled"),
        ]

        for var_name, description, warning_msg in optional_vars:
            if not os.getenv(var_name):
                self.warnings.append(f"{var_name} not set - {warning_msg}")

    def _validate_directories(self):
        """Ensure required directories exist."""
        dirs = [
            ("logs", "Log files"),
            ("uploads", "Uploaded documents"),
            ("cache", "Model cache"),
        ]

        for dir_name, description in dirs:
            if not os.path.exists(dir_name):
                try:
                    os.makedirs(dir_name)
                    app_logger.info(f"Created directory: {dir_name}")
                except Exception as e:
                    self.warnings.append(f"Could not create {dir_name}: {e}")

    def _validate_dependencies(self):
        """Check critical dependencies."""
        dependencies = [
            ("torch", "PyTorch"),
            ("transformers", "HuggingFace Transformers"),
            ("fastapi", "FastAPI"),
            ("gradio", "Gradio"),
            ("PIL", "Pillow"),
            ("sqlalchemy", "SQLAlchemy"),
        ]

        for module_name, display_name in dependencies:
            try:
                __import__(module_name)
            except ImportError:
                self.errors.append(f"Missing dependency: {display_name} ({module_name})")

    def _validate_gpu(self):
        """Check GPU availability."""
        try:
            import torch
            if torch.cuda.is_available():
                gpu_name = torch.cuda.get_device_name(0)
                memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)
                app_logger.info(f"GPU detected: {gpu_name} ({memory:.1f}GB)")
            else:
                self.warnings.append("No GPU detected - running on CPU (slower)")
        except Exception as e:
            self.warnings.append(f"Could not check GPU: {e}")

    def print_report(self):
        """Print validation report."""
        print("\n" + "=" * 60)
        print("STARTUP VALIDATION REPORT")
        print("=" * 60)

        if self.errors:
            print("\n❌ ERRORS (must fix):")
            for error in self.errors:
                print(f"  • {error}")

        if self.warnings:
            print("\n⚠️  WARNINGS (optional):")
            for warning in self.warnings:
                print(f"  • {warning}")

        if not self.errors and not self.warnings:
            print("\n✅ All checks passed!")

        print("\n" + "=" * 60)

        if self.errors:
            print("❌ Startup blocked due to errors above")
            print("=" * 60 + "\n")
            return False
        else:
            print("✅ Startup checks passed")
            print("=" * 60 + "\n")
            return True


def validate_startup() -> bool:
    """
    Run startup validation.

    Returns:
        True if all checks pass, False otherwise
    """
    validator = StartupValidator()
    is_valid = validator.validate_all()
    validator.print_report()
    return is_valid


def require_valid_startup():
    """
    Validate startup and exit if checks fail.
    """
    if not validate_startup():
        sys.exit(1)


if __name__ == "__main__":
    validate_startup()
