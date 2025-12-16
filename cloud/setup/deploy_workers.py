#!/usr/bin/env python3
"""
Unified Worker Deployment CLI
Deploy workers to HuggingFace, Railway, Render, etc.
"""
import os
import sys
import argparse
from pathlib import Path

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


def show_menu():
    """Show deployment menu"""
    print_header("🚀 Free Compute Worker Deployment")

    print("Available platforms:")
    print()
    print(f"  {GREEN}1.{NC} HuggingFace Spaces  (⭐ Recommended)")
    print("     • 2 cores, 16GB RAM per worker")
    print("     • Unlimited workers")
    print("     • 24/7 uptime")
    print("     • Automated deployment ✅")
    print()
    print(f"  {BLUE}2.{NC} Google Colab (GPU)")
    print("     • T4 GPU, 2 cores, 13GB RAM")
    print("     • Manual setup (15 min)")
    print("     • 12h sessions")
    print()
    print(f"  {BLUE}3.{NC} Railway")
    print("     • 0.5 vCPU, 512MB RAM")
    print("     • $5/month credit")
    print("     • Good for Redis/queues")
    print()
    print(f"  {BLUE}4.{NC} Render")
    print("     • Shared CPU, 512MB RAM")
    print("     • Good for APIs")
    print()
    print(f"  {YELLOW}5.{NC} Oracle Cloud")
    print("     • 4 cores, 24GB RAM (free tier)")
    print("     • Auto-provisioning active ✅")
    print("     • Check status: tail -f ~/.oracle_auto_provision/provision.log")
    print()
    print(f"  {BOLD}0.{NC} Exit")
    print()


def deploy_huggingface():
    """Deploy to HuggingFace"""
    script = Path(__file__).parent / 'deploy_huggingface.py'
    os.system(f'python3 {script}')


def deploy_colab():
    """Instructions for Colab"""
    print_header("Google Colab Deployment")

    notebook = Path(__file__).parent.parent / 'colab' / 'discovery_worker.ipynb'

    print("Google Colab requires manual setup (GPU workers):")
    print()
    print("Steps:")
    print("  1. Upload this file to Google Drive:")
    print(f"     {notebook}")
    print()
    print("  2. Open in Colab, enable GPU:")
    print("     Runtime > Change runtime type > GPU (T4)")
    print()
    print("  3. Get ngrok token:")
    print("     https://dashboard.ngrok.com/signup")
    print()
    print("  4. Run all cells, paste token when prompted")
    print()
    print("  5. Copy the public URL and add to .env:")
    print("     COLAB_GPU_WORKER=https://xxxx.ngrok.io")
    print()
    print("Full guide: cloud/colab/README.md")
    print()
    input("Press Enter to continue...")


def deploy_railway():
    """Instructions for Railway"""
    print_header("Railway Deployment")

    print("Railway deployment steps:")
    print()
    print("1. Sign up: https://railway.app")
    print()
    print("2. New Project > Deploy from GitHub")
    print()
    print("3. Connect this repository")
    print()
    print("4. Add environment variables from .env")
    print()
    print("5. Deploy!")
    print()
    print("Note: Railway gives $5/month credit free")
    print()
    input("Press Enter to continue...")


def deploy_render():
    """Instructions for Render"""
    print_header("Render Deployment")

    print("Render deployment steps:")
    print()
    print("1. Sign up: https://render.com")
    print()
    print("2. New Web Service > Connect GitHub")
    print()
    print("3. Configure:")
    print("   Build: pip install -r requirements.txt")
    print("   Start: uvicorn cloud.worker.worker_api:app --host 0.0.0.0 --port $PORT")
    print()
    print("4. Deploy")
    print()
    print("Note: Free tier spins down after 15 min idle")
    print()
    input("Press Enter to continue...")


def check_oracle_status():
    """Check Oracle auto-provisioning status"""
    print_header("Oracle Cloud Auto-Provisioning Status")

    log_file = Path.home() / '.oracle_auto_provision' / 'provision.log'

    if not log_file.exists():
        print(f"{RED}❌ Auto-provisioning not running{NC}")
        print()
        print("Start it with:")
        print("  cd cloud/setup && ./auto_provision.sh --background")
        print()
    else:
        os.system(f'tail -30 {log_file}')
        print()
        print("Live monitoring:")
        print(f"  tail -f {log_file}")
        print()

    input("Press Enter to continue...")


def main():
    """Main CLI"""
    parser = argparse.ArgumentParser(description='Deploy free compute workers')
    parser.add_argument('--platform', choices=['hf', 'colab', 'railway', 'render', 'oracle'],
                       help='Platform to deploy to')
    parser.add_argument('--auto', action='store_true',
                       help='Auto-deploy to HuggingFace without menu')

    args = parser.parse_args()

    # Direct deployment
    if args.auto or args.platform == 'hf':
        deploy_huggingface()
        return

    if args.platform == 'colab':
        deploy_colab()
        return

    if args.platform == 'railway':
        deploy_railway()
        return

    if args.platform == 'render':
        deploy_render()
        return

    if args.platform == 'oracle':
        check_oracle_status()
        return

    # Interactive menu
    while True:
        os.system('clear' if os.name == 'posix' else 'cls')
        show_menu()

        choice = input("Select platform [1-5, 0 to exit]: ").strip()

        if choice == '0':
            print("Goodbye!")
            break
        elif choice == '1':
            deploy_huggingface()
        elif choice == '2':
            deploy_colab()
        elif choice == '3':
            deploy_railway()
        elif choice == '4':
            deploy_render()
        elif choice == '5':
            check_oracle_status()
        else:
            print(f"{RED}Invalid choice{NC}")
            input("Press Enter to continue...")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print()
        print(f"{YELLOW}Cancelled{NC}")
        sys.exit(0)
