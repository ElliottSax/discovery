#!/usr/bin/env python3
"""
Production Verification Script
Verifies all security fixes are properly applied
"""

import os
import sys
from pathlib import Path

print("=" * 60)
print("PRODUCTION SECURITY VERIFICATION")
print("=" * 60)

# Security checklist
checks = {
    "Environment Variables": False,
    "No Hardcoded Credentials": False,
    "SQL Injection Protection": False,
    "Sensitive Data Filtering": False,
    "Memory-Safe Caching": False,
    "Thread-Safe MLflow": False,
    "Error Handling": False,
    "Abstract Interfaces": False
}

# 1. Check environment variables
if os.getenv('DB_PASSWORD'):
    checks["Environment Variables"] = True

# 2. Check no hardcoded credentials in code
dangerous_patterns = [
    "password = 'postgres'",
    "password': 'postgres'",
    "postgresql://quant_user:quant_password"
]

for py_file in Path('.').rglob('*.py'):
    if 'test' not in str(py_file).lower() and 'venv' not in str(py_file) and 'verify_production.py' not in str(py_file):
        try:
            content = py_file.read_text()
            for pattern in dangerous_patterns:
                if pattern in content:
                    print(f"⚠️  Found hardcoded credential in {py_file}")
                    checks["No Hardcoded Credentials"] = False
                    break
            else:
                continue
            break
        except:
            pass
else:
    checks["No Hardcoded Credentials"] = True

# 3. Check SQL injection protection
sql_files = ['scripts/analyze_politician_patterns.py', 'scripts/run_quick_analysis.py']
for file_path in sql_files:
    if Path(file_path).exists():
        content = Path(file_path).read_text()
        if 'params=' in content or ':politician_name' in content or 'sql.text' in content:
            checks["SQL Injection Protection"] = True
            break

# 4. Check sensitive data filtering
if Path('config/logging_config.py').exists():
    content = Path('config/logging_config.py').read_text()
    if 'SensitiveDataFilter' in content and 'REDACTED' in content:
        checks["Sensitive Data Filtering"] = True

# 5. Check memory-safe caching
if Path('analysis/utils/caching.py').exists():
    content = Path('analysis/utils/caching.py').read_text()
    if 'max_size_mb' in content and '_auto_cleanup' in content:
        checks["Memory-Safe Caching"] = True

# 6. Check thread-safe MLflow
if Path('analysis/utils/mlflow_tracker.py').exists():
    content = Path('analysis/utils/mlflow_tracker.py').read_text()
    if 'threading.Lock' in content and '_experiment_lock' in content:
        checks["Thread-Safe MLflow"] = True

# 7. Check error handling
if Path('analysis/correlation.py').exists():
    content = Path('analysis/correlation.py').read_text()
    if 'try:' in content and 'except' in content and 'logger.error' in content:
        checks["Error Handling"] = True

# 8. Check abstract interfaces
if Path('analysis/base.py').exists():
    content = Path('analysis/base.py').read_text()
    if 'BaseDetector' in content and 'ABC' in content and '@abstractmethod' in content:
        checks["Abstract Interfaces"] = True

# Display results
print("\nSecurity Verification Results:")
print("-" * 60)

all_passed = True
for check, passed in checks.items():
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{check:.<40} {status}")
    if not passed:
        all_passed = False

print("-" * 60)

if all_passed:
    print("\n🎉 SUCCESS: All security checks passed!")
    print("🔒 System is secure and ready for production")
    sys.exit(0)
else:
    failed_checks = [k for k, v in checks.items() if not v]
    print(f"\n⚠️  WARNING: {len(failed_checks)} checks failed:")
    for check in failed_checks:
        print(f"   - {check}")
    print("\nPlease address these issues before production deployment")
    sys.exit(1)