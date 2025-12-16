#!/usr/bin/env python3
"""
Automated HuggingFace Space Deployment
Automatically creates and deploys worker spaces
"""
import os
import sys
import time
import requests
from pathlib import Path
import subprocess
import json

# Colors
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
RED = '\033[0;31m'
BLUE = '\033[0;34m'
BOLD = '\033[1m'
NC = '\033[0m'


def print_header(text):
    print(f"\n{BLUE}{'='*70}{NC}")
    print(f"{BLUE}{BOLD}{text}{NC}")
    print(f"{BLUE}{'='*70}{NC}\n")


def print_success(text):
    print(f"{GREEN}✅ {text}{NC}")


def print_error(text):
    print(f"{RED}❌ {text}{NC}")


def print_info(text):
    print(f"{BLUE}ℹ️  {text}{NC}")


def print_warning(text):
    print(f"{YELLOW}⚠️  {text}{NC}")


def check_huggingface_cli():
    """Check if huggingface-cli is installed"""
    try:
        result = subprocess.run(
            ['huggingface-cli', '--version'],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def install_huggingface_cli():
    """Install huggingface_hub package"""
    print_info("Installing huggingface_hub...")
    try:
        subprocess.run(
            [sys.executable, '-m', 'pip', 'install', '-q', 'huggingface_hub'],
            check=True
        )
        print_success("huggingface_hub installed")
        return True
    except subprocess.CalledProcessError:
        print_error("Failed to install huggingface_hub")
        return False


def get_hf_token():
    """Get HuggingFace token from user"""
    print_header("HuggingFace Authentication")

    print("To deploy workers, you need a HuggingFace token.")
    print("\nSteps:")
    print("1. Go to: https://huggingface.co/settings/tokens")
    print("2. Create a new token with 'write' permissions")
    print("3. Copy and paste it below")
    print()

    token = input("Enter your HuggingFace token: ").strip()

    if not token:
        print_error("No token provided")
        return None

    # Verify token works
    print_info("Verifying token...")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get("https://huggingface.co/api/whoami", headers=headers)

    if response.status_code == 200:
        username = response.json().get('name')
        print_success(f"Authenticated as: {username}")
        return token, username
    else:
        print_error("Invalid token")
        return None


def create_space(token, username, space_name, num):
    """Create a HuggingFace Space"""
    print_info(f"Creating space: {space_name}...")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # Create space using API
    data = {
        "name": space_name,
        "sdk": "gradio",
        "private": False,
        "hardware": "cpu-basic"
    }

    response = requests.post(
        "https://huggingface.co/api/spaces",
        headers=headers,
        json=data
    )

    if response.status_code in [200, 201]:
        print_success(f"Space created: {username}/{space_name}")
        return f"{username}/{space_name}"
    elif response.status_code == 409:
        print_warning(f"Space already exists: {username}/{space_name}")
        return f"{username}/{space_name}"
    else:
        print_error(f"Failed to create space: {response.status_code}")
        print_error(response.text)
        return None


def upload_files_to_space(token, repo_id, source_dir):
    """Upload worker files to the space using git"""
    print_info(f"Uploading files to {repo_id}...")

    from huggingface_hub import HfApi

    api = HfApi(token=token)

    # Files to upload
    files = ['app.py', 'requirements.txt', 'README.md']

    for filename in files:
        filepath = os.path.join(source_dir, filename)
        if os.path.exists(filepath):
            try:
                api.upload_file(
                    path_or_fileobj=filepath,
                    path_in_repo=filename,
                    repo_id=repo_id,
                    repo_type="space",
                )
                print_success(f"Uploaded: {filename}")
            except Exception as e:
                print_error(f"Failed to upload {filename}: {e}")
                return False
        else:
            print_warning(f"File not found: {filepath}")

    return True


def wait_for_space_ready(username, space_name, timeout=300):
    """Wait for space to be built and ready"""
    print_info(f"Waiting for space to build (max {timeout}s)...")

    url = f"https://{username}-{space_name}.hf.space/health"
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print_success("Space is live!")
                return True
        except requests.RequestException:
            pass

        elapsed = int(time.time() - start_time)
        print(f"\r  Building... {elapsed}s / {timeout}s", end='', flush=True)
        time.sleep(10)

    print()
    print_warning("Space not ready yet (may take longer)")
    return False


def add_to_env_file(space_url, worker_num):
    """Add worker URL to .env file"""
    env_file = Path(__file__).parent.parent.parent / '.env'

    line = f"HUGGINGFACE_WORKER_{worker_num}={space_url}\n"

    # Check if already exists
    if env_file.exists():
        with open(env_file, 'r') as f:
            if line.strip() in f.read():
                print_info(".env already contains this worker")
                return

    # Append to .env
    with open(env_file, 'a') as f:
        f.write(line)

    print_success(f"Added to .env: HUGGINGFACE_WORKER_{worker_num}")


def deploy_worker(token, username, worker_num=1):
    """Deploy a single worker"""
    print_header(f"Deploying Worker #{worker_num}")

    space_name = f"discovery-worker-{worker_num}"
    source_dir = Path(__file__).parent.parent / 'huggingface'

    # Create space
    repo_id = create_space(token, username, space_name, worker_num)
    if not repo_id:
        return False

    # Upload files
    if not upload_files_to_space(token, repo_id, source_dir):
        return False

    # Generate URL
    space_url = f"https://{username}-{space_name}.hf.space"
    print_success(f"Worker URL: {space_url}")

    # Wait for it to be ready
    wait_for_space_ready(username, space_name)

    # Add to .env
    add_to_env_file(space_url, worker_num)

    print_success(f"Worker #{worker_num} deployed successfully!")
    print()
    print(f"Test with: curl {space_url}/health")
    print()

    return True


def main():
    """Main deployment function"""
    print_header("🚀 Automated HuggingFace Worker Deployment")

    # Check if huggingface_hub is installed
    try:
        import huggingface_hub
    except ImportError:
        print_warning("huggingface_hub not installed")
        if not install_huggingface_cli():
            print_error("Installation failed. Install manually:")
            print("  pip install huggingface_hub")
            return 1

    # Get authentication
    auth = get_hf_token()
    if not auth:
        return 1

    token, username = auth

    # Ask how many workers to deploy
    print()
    print("How many workers do you want to deploy?")
    print("  • Each worker: 2 cores, 16GB RAM")
    print("  • You can deploy unlimited workers")
    print("  • Recommended: Start with 2-3")
    print()

    try:
        num_workers = int(input("Number of workers [1-10]: ").strip() or "2")
        if num_workers < 1 or num_workers > 10:
            print_error("Please enter a number between 1 and 10")
            return 1
    except ValueError:
        print_error("Invalid number")
        return 1

    # Deploy workers
    print()
    print(f"Deploying {num_workers} worker(s)...")
    print()

    successful = 0
    for i in range(1, num_workers + 1):
        if deploy_worker(token, username, i):
            successful += 1
        time.sleep(2)  # Small delay between deployments

    # Summary
    print_header("Deployment Complete")
    print(f"Successfully deployed: {successful}/{num_workers} workers")
    print()

    if successful > 0:
        print("Your workers are now available!")
        print()
        print("Next steps:")
        print("  1. Test workers: python3 cloud/monitor/check_all_workers.py")
        print("  2. View .env file to see worker URLs")
        print()
        print(f"Total compute added: {successful * 2} cores, {successful * 16} GB RAM")
        print()

    return 0 if successful > 0 else 1


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print()
        print_warning("Deployment cancelled")
        sys.exit(1)
