#!/usr/bin/env python3
"""
Oracle Cloud Setup Verification Script
Checks prerequisites and validates configuration
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from typing import Dict, List, Tuple

# Color codes
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
RED = '\033[0;31m'
BLUE = '\033[0;34m'
NC = '\033[0m'  # No Color

class OracleSetupVerifier:
    """Verifies Oracle Cloud setup requirements and configuration"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.issues = []
        self.warnings = []
        self.successes = []

    def print_header(self):
        """Print script header"""
        print("=" * 70)
        print("Oracle Cloud Setup Verification")
        print("=" * 70)
        print()

    def check_python(self) -> bool:
        """Check Python version"""
        print(f"{BLUE}Checking Python...{NC}")
        try:
            version_info = sys.version_info
            if version_info.major >= 3 and version_info.minor >= 9:
                self.successes.append(f"Python {version_info.major}.{version_info.minor}.{version_info.micro} installed")
                return True
            else:
                self.issues.append(f"Python 3.9+ required (found {version_info.major}.{version_info.minor})")
                return False
        except Exception as e:
            self.issues.append(f"Could not check Python version: {e}")
            return False

    def check_ssh_keys(self) -> bool:
        """Check SSH key pair exists"""
        print(f"{BLUE}Checking SSH keys...{NC}")
        ssh_dir = Path.home() / '.ssh'
        private_key = ssh_dir / 'id_rsa'
        public_key = ssh_dir / 'id_rsa.pub'

        if private_key.exists() and public_key.exists():
            self.successes.append(f"SSH key pair found at {ssh_dir}")
            return True
        else:
            self.warnings.append("SSH key pair not found (will be generated)")
            return False

    def check_oci_keys(self) -> bool:
        """Check Oracle Cloud API keys"""
        print(f"{BLUE}Checking OCI API keys...{NC}")
        oci_dir = Path.home() / '.oci'
        private_key = oci_dir / 'oci_api_key.pem'
        public_key = oci_dir / 'oci_api_key_public.pem'

        if private_key.exists() and public_key.exists():
            self.successes.append(f"OCI API keys found at {oci_dir}")
            # Check permissions
            try:
                stat_info = private_key.stat()
                mode = oct(stat_info.st_mode)[-3:]
                if mode == '600':
                    self.successes.append("OCI private key has correct permissions (600)")
                else:
                    self.warnings.append(f"OCI private key permissions should be 600 (found {mode})")
            except:
                pass
            return True
        else:
            self.warnings.append("OCI API keys not found (run generate_oci_keys.sh)")
            return False

    def check_oci_cli(self) -> Tuple[bool, str]:
        """Check OCI CLI installation"""
        print(f"{BLUE}Checking OCI CLI...{NC}")
        try:
            result = subprocess.run(['oci', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                version = result.stdout.strip()
                self.successes.append(f"OCI CLI installed: {version}")
                return True, version
            else:
                self.warnings.append("OCI CLI not installed")
                return False, ""
        except FileNotFoundError:
            self.warnings.append("OCI CLI not found (install with: pip3 install oci-cli)")
            return False, ""

    def check_oci_config(self) -> bool:
        """Check OCI CLI configuration"""
        print(f"{BLUE}Checking OCI CLI configuration...{NC}")
        config_file = Path.home() / '.oci' / 'config'

        if config_file.exists():
            self.successes.append(f"OCI config found at {config_file}")
            # Try to parse config
            try:
                with open(config_file) as f:
                    content = f.read()
                    if 'user=' in content and 'tenancy=' in content:
                        self.successes.append("OCI config appears valid")
                        return True
                    else:
                        self.warnings.append("OCI config may be incomplete")
                        return False
            except:
                self.warnings.append("Could not read OCI config")
                return False
        else:
            self.warnings.append("OCI config not found (run: oci setup config)")
            return False

    def check_env_file(self) -> Dict[str, str]:
        """Check .env file configuration"""
        print(f"{BLUE}Checking .env configuration...{NC}")
        env_file = self.project_root / '.env'
        env_vars = {}

        if env_file.exists():
            self.successes.append(f"Found .env file at {env_file}")
            with open(env_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if '=' in line:
                            key, value = line.split('=', 1)
                            env_vars[key] = value

            # Check Oracle-specific variables
            required_vars = [
                'ORACLE_USER_OCID',
                'ORACLE_TENANCY_OCID',
                'ORACLE_REGION',
                'ORACLE_FINGERPRINT',
                'ORACLE_PRIVATE_KEY_PATH'
            ]

            for var in required_vars:
                if var in env_vars and env_vars[var]:
                    if var == 'ORACLE_FINGERPRINT':
                        if ':' in env_vars[var]:
                            self.successes.append(f"{var} configured")
                        else:
                            self.warnings.append(f"{var} not set (add after uploading API key)")
                    else:
                        self.successes.append(f"{var} configured")
                else:
                    if var == 'ORACLE_FINGERPRINT':
                        self.warnings.append(f"{var} not set (add after uploading API key)")
                    else:
                        self.issues.append(f"{var} missing from .env")

            # Check for worker URLs
            if 'ORACLE_WORKERS' in env_vars and env_vars['ORACLE_WORKERS']:
                workers = env_vars['ORACLE_WORKERS'].split(',')
                self.successes.append(f"Found {len(workers)} worker URLs in .env")
            else:
                self.warnings.append("ORACLE_WORKERS not configured (will be set after VM provisioning)")

        else:
            self.issues.append(".env file not found")

        return env_vars

    def check_workers_file(self) -> List[str]:
        """Check workers.txt configuration"""
        print(f"{BLUE}Checking workers configuration...{NC}")
        workers_file = self.project_root / 'cloud' / 'deploy' / 'workers.txt'
        workers = []

        if workers_file.exists():
            self.successes.append(f"Found workers.txt at {workers_file}")
            with open(workers_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        workers.append(line)

            if workers:
                self.successes.append(f"Found {len(workers)} worker IPs configured")
                return workers
            else:
                self.warnings.append("workers.txt exists but is empty")
        else:
            self.warnings.append("workers.txt not found (will be created after VM provisioning)")

        return workers

    def check_deployment_scripts(self) -> bool:
        """Check deployment scripts exist and are executable"""
        print(f"{BLUE}Checking deployment scripts...{NC}")
        deploy_dir = self.project_root / 'cloud' / 'deploy'
        scripts = [
            'deploy_workers.sh',
            'start_all_workers.sh',
            'stop_all_workers.sh',
            'check_workers.sh'
        ]

        all_found = True
        for script in scripts:
            script_path = deploy_dir / script
            if script_path.exists():
                if os.access(script_path, os.X_OK):
                    self.successes.append(f"✓ {script} (executable)")
                else:
                    self.warnings.append(f"{script} not executable (run: chmod +x {script})")
            else:
                self.issues.append(f"{script} not found")
                all_found = False

        return all_found

    def test_worker_connectivity(self, workers: List[str]) -> bool:
        """Test connectivity to worker nodes"""
        if not workers:
            return False

        print(f"{BLUE}Testing worker connectivity...{NC}")
        import requests
        from concurrent.futures import ThreadPoolExecutor, as_completed

        def check_worker(worker_ip):
            url = f"http://{worker_ip}:8000/health"
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    return worker_ip, True, "Online"
                else:
                    return worker_ip, False, f"HTTP {response.status_code}"
            except requests.exceptions.ConnectionError:
                return worker_ip, False, "Connection refused (worker not running?)"
            except requests.exceptions.Timeout:
                return worker_ip, False, "Timeout"
            except Exception as e:
                return worker_ip, False, str(e)

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {executor.submit(check_worker, worker): worker for worker in workers}

            online_count = 0
            for future in as_completed(futures):
                worker_ip, is_online, status = future.result()
                if is_online:
                    self.successes.append(f"Worker {worker_ip}: {status}")
                    online_count += 1
                else:
                    self.warnings.append(f"Worker {worker_ip}: {status}")

            return online_count > 0

    def check_python_packages(self) -> bool:
        """Check required Python packages"""
        print(f"{BLUE}Checking Python packages...{NC}")
        required_packages = [
            'oci',
            'requests',
            'aiohttp',
            'fastapi',
            'uvicorn'
        ]

        missing_packages = []
        for package in required_packages:
            try:
                __import__(package)
                self.successes.append(f"Package '{package}' installed")
            except ImportError:
                missing_packages.append(package)
                self.warnings.append(f"Package '{package}' not installed")

        if missing_packages:
            self.warnings.append(f"Install missing packages: pip3 install {' '.join(missing_packages)}")

        return len(missing_packages) == 0

    def print_summary(self):
        """Print verification summary"""
        print()
        print("=" * 70)
        print("VERIFICATION SUMMARY")
        print("=" * 70)
        print()

        if self.successes:
            print(f"{GREEN}✅ Successes ({len(self.successes)}):{NC}")
            for success in self.successes:
                print(f"  • {success}")
            print()

        if self.warnings:
            print(f"{YELLOW}⚠️  Warnings ({len(self.warnings)}):{NC}")
            for warning in self.warnings:
                print(f"  • {warning}")
            print()

        if self.issues:
            print(f"{RED}❌ Issues ({len(self.issues)}):{NC}")
            for issue in self.issues:
                print(f"  • {issue}")
            print()

        # Overall status
        if not self.issues:
            if not self.warnings:
                print(f"{GREEN}🎉 All checks passed! System is ready.{NC}")
                return True
            else:
                print(f"{YELLOW}⚠️  Setup incomplete but can proceed with manual steps.{NC}")
                return True
        else:
            print(f"{RED}❌ Critical issues found. Please resolve before continuing.{NC}")
            return False

    def print_next_steps(self, workers: List[str]):
        """Print next steps based on current status"""
        print()
        print("=" * 70)
        print("NEXT STEPS")
        print("=" * 70)
        print()

        if not (Path.home() / '.oci' / 'oci_api_key.pem').exists():
            print("1. Generate OCI API keys:")
            print("   ./generate_oci_keys.sh")
            print()

        if not (Path.home() / '.oci' / 'config').exists():
            print("2. Configure OCI CLI:")
            print("   oci setup config")
            print()

        if not workers:
            print("3. Provision Oracle Cloud VMs:")
            print("   python3 provision_oracle_vms.py")
            print()
            print("   Or create manually in Oracle Console and add IPs to:")
            print("   cloud/deploy/workers.txt")
            print()
        else:
            print("4. Deploy/update workers:")
            print("   cd cloud/deploy")
            print("   ./deploy_workers.sh")
            print("   ./start_all_workers.sh")
            print()

        print("Or run the complete setup wizard:")
        print("   ./setup_oracle_cloud.sh")
        print()

    def run(self):
        """Run all verification checks"""
        self.print_header()

        # Run checks
        self.check_python()
        self.check_ssh_keys()
        self.check_oci_keys()
        oci_installed, _ = self.check_oci_cli()
        if oci_installed:
            self.check_oci_config()
        env_vars = self.check_env_file()
        workers = self.check_workers_file()
        self.check_deployment_scripts()
        self.check_python_packages()

        # Test connectivity if workers are configured
        if workers:
            self.test_worker_connectivity(workers)

        # Print summary
        success = self.print_summary()
        self.print_next_steps(workers)

        return success


def main():
    """Main entry point"""
    verifier = OracleSetupVerifier()
    success = verifier.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()