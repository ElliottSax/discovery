#!/usr/bin/env python3
"""
Setup verification script
Checks that all system components are properly configured
"""

import sys
import os
from pathlib import Path
import subprocess
import importlib.util
from typing import List, Tuple
import logging

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)


class SetupVerifier:
    """Verify system setup and configuration"""

    def __init__(self):
        self.issues = []
        self.warnings = []

    def check_python_version(self) -> bool:
        """Check Python version"""
        logger.info("Checking Python version...")
        version = sys.version_info
        if version.major >= 3 and version.minor >= 9:
            logger.info(f"  ✓ Python {version.major}.{version.minor}.{version.micro}")
            return True
        else:
            self.issues.append(f"Python 3.9+ required, found {version.major}.{version.minor}")
            logger.error(f"  ✗ Python version too old: {version.major}.{version.minor}")
            return False

    def check_required_packages(self) -> bool:
        """Check required Python packages"""
        logger.info("Checking required packages...")

        required = [
            "fastapi",
            "uvicorn",
            "sqlalchemy",
            "psycopg2",
            "pandas",
            "numpy",
            "scipy",
            "sklearn",
            "mlflow",
            "pydantic",
            "redis",
        ]

        missing = []
        for package in required:
            # Handle package name variations
            import_name = package
            if package == "sklearn":
                import_name = "sklearn"
            elif package == "psycopg2":
                import_name = "psycopg2"

            if importlib.util.find_spec(import_name) is None:
                missing.append(package)
                logger.error(f"  ✗ {package}")
            else:
                logger.info(f"  ✓ {package}")

        if missing:
            self.issues.append(f"Missing packages: {', '.join(missing)}")
            logger.info(f"\nInstall missing packages with:")
            logger.info(f"  pip install {' '.join(missing)}")
            return False

        return True

    def check_environment_variables(self) -> bool:
        """Check required environment variables"""
        logger.info("Checking environment variables...")

        required = {
            "DB_HOST": "Database host",
            "DB_NAME": "Database name",
            "DB_USER": "Database user",
            "DB_PASSWORD": "Database password",
        }

        optional = {
            "MLFLOW_TRACKING_URI": "MLFlow server URI",
            "REDIS_HOST": "Redis cache host",
            "SECRET_KEY": "Application secret key",
            "JWT_SECRET_KEY": "JWT signing key",
        }

        all_ok = True

        for var, description in required.items():
            value = os.getenv(var)
            if not value:
                self.issues.append(f"Missing required env var: {var} ({description})")
                logger.error(f"  ✗ {var}: {description}")
                all_ok = False
            else:
                # Mask password
                display = "***" if "PASSWORD" in var or "SECRET" in var else value
                logger.info(f"  ✓ {var}: {display}")

        for var, description in optional.items():
            value = os.getenv(var)
            if not value:
                self.warnings.append(f"Optional env var not set: {var} ({description})")
                logger.warning(f"  ⚠ {var}: {description} (optional)")
            else:
                display = "***" if "PASSWORD" in var or "SECRET" in var else value
                logger.info(f"  ✓ {var}: {display}")

        return all_ok

    def check_database_connection(self) -> bool:
        """Check database connectivity"""
        logger.info("Checking database connection...")

        try:
            from api.database import check_connection
            if check_connection():
                logger.info("  ✓ Database connection successful")
                return True
            else:
                self.issues.append("Cannot connect to database")
                logger.error("  ✗ Database connection failed")
                return False
        except Exception as e:
            self.issues.append(f"Database connection error: {e}")
            logger.error(f"  ✗ Error: {e}")
            return False

    def check_directory_structure(self) -> bool:
        """Check required directories exist"""
        logger.info("Checking directory structure...")

        required_dirs = [
            "analysis",
            "api",
            "scripts",
            "data_pipeline",
        ]

        optional_dirs = [
            "frontend",
            "data",
            "cache",
            "logs",
        ]

        all_ok = True

        for dir_name in required_dirs:
            dir_path = project_root / dir_name
            if dir_path.exists() and dir_path.is_dir():
                logger.info(f"  ✓ {dir_name}/")
            else:
                self.issues.append(f"Missing required directory: {dir_name}/")
                logger.error(f"  ✗ {dir_name}/")
                all_ok = False

        for dir_name in optional_dirs:
            dir_path = project_root / dir_name
            if dir_path.exists() and dir_path.is_dir():
                logger.info(f"  ✓ {dir_name}/")
            else:
                logger.warning(f"  ⚠ {dir_name}/ (will be created as needed)")

        return all_ok

    def check_api_files(self) -> bool:
        """Check API files exist"""
        logger.info("Checking API files...")

        required_files = [
            "api/main.py",
            "api/models.py",
            "api/database.py",
            "api/db_models.py",
            "api/auth.py",
        ]

        all_ok = True

        for file_path in required_files:
            full_path = project_root / file_path
            if full_path.exists():
                logger.info(f"  ✓ {file_path}")
            else:
                self.issues.append(f"Missing required file: {file_path}")
                logger.error(f"  ✗ {file_path}")
                all_ok = False

        return all_ok

    def check_analysis_modules(self) -> bool:
        """Check analysis modules"""
        logger.info("Checking analysis modules...")

        modules = [
            "analysis.cyclical.fourier",
            "analysis.cyclical.hmm",
            "analysis.cyclical.dtw",
            "analysis.ensemble",
            "analysis.correlation",
        ]

        all_ok = True

        for module_name in modules:
            if importlib.util.find_spec(module_name):
                logger.info(f"  ✓ {module_name}")
            else:
                self.warnings.append(f"Analysis module not found: {module_name}")
                logger.warning(f"  ⚠ {module_name} (optional)")

        return all_ok

    def check_frontend(self) -> bool:
        """Check frontend setup"""
        logger.info("Checking frontend setup...")

        frontend_dir = project_root / "frontend"

        if not frontend_dir.exists():
            self.warnings.append("Frontend directory not found")
            logger.warning("  ⚠ Frontend not set up (optional)")
            return True

        # Check for package.json
        package_json = frontend_dir / "package.json"
        if package_json.exists():
            logger.info("  ✓ package.json")
        else:
            self.warnings.append("Frontend package.json not found")
            logger.warning("  ⚠ package.json not found")

        # Check for node_modules
        node_modules = frontend_dir / "node_modules"
        if node_modules.exists():
            logger.info("  ✓ node_modules")
        else:
            self.warnings.append("Frontend dependencies not installed")
            logger.warning("  ⚠ node_modules not found")
            logger.info("    Run: cd frontend && npm install")

        return True

    def run_all_checks(self) -> bool:
        """Run all verification checks"""
        logger.info("=" * 60)
        logger.info("System Setup Verification")
        logger.info("=" * 60)
        logger.info("")

        checks = [
            self.check_python_version,
            self.check_required_packages,
            self.check_directory_structure,
            self.check_api_files,
            self.check_environment_variables,
            self.check_database_connection,
            self.check_analysis_modules,
            self.check_frontend,
        ]

        results = []
        for check in checks:
            try:
                result = check()
                results.append(result)
                logger.info("")
            except Exception as e:
                logger.error(f"  ✗ Check failed with error: {e}")
                logger.info("")
                results.append(False)

        # Summary
        logger.info("=" * 60)
        logger.info("Summary")
        logger.info("=" * 60)

        if self.issues:
            logger.error("\n⚠ Issues found:")
            for issue in self.issues:
                logger.error(f"  • {issue}")

        if self.warnings:
            logger.warning("\n⚠ Warnings:")
            for warning in self.warnings:
                logger.warning(f"  • {warning}")

        if all(results) and not self.issues:
            logger.info("\n✓ All required checks passed!")
            logger.info("✓ System is ready to use")
            return True
        else:
            logger.error("\n✗ Some checks failed")
            logger.error("✗ Please fix the issues above before continuing")
            return False


def main():
    verifier = SetupVerifier()
    success = verifier.run_all_checks()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
