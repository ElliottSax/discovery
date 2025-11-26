#!/usr/bin/env python3
"""
Simple launcher for politician trading analysis
Just run: python3 analyze.py
"""

import os
import sys

def main():
    print("🚀 POLITICIAN TRADING ANALYSIS")
    print("=" * 60)
    print()
    print("Choose analysis mode:")
    print("  1. Quick Analysis (standalone, no dependencies)")
    print("  2. Full Production Analysis (with monitoring)")
    print("  3. Production Testing")
    print("  4. System Status Check")
    print()
    
    try:
        choice = input("Enter choice (1-4): ").strip()
        
        if choice == "1":
            print("\n🤖 Running Standalone Analysis...")
            os.system("python3 standalone_analyzer.py")
            
        elif choice == "2":
            print("\n⚙️ Running Production Analysis...")
            # Check if environment variables are set
            if not os.getenv('DB_PASSWORD'):
                os.environ['DB_PASSWORD'] = 'demo_password'
                print("   Using demo credentials (set DB_PASSWORD for production)")
                
            os.system("python3 run_production.py")
            
        elif choice == "3":
            print("\n🧪 Running Production Tests...")
            os.system("python3 production_test_basic.py")
            
        elif choice == "4":
            print("\n📊 Checking System Status...")
            if not os.getenv('DB_PASSWORD'):
                os.environ['DB_PASSWORD'] = 'demo'
            os.system("python3 production_dashboard.py")
            
        else:
            print("Invalid choice. Please enter 1-4.")
            return
            
    except KeyboardInterrupt:
        print("\n\nAnalysis cancelled.")
    except Exception as e:
        print(f"\nError: {e}")
        
    print("\n" + "=" * 60)
    print("Analysis complete! Check the generated report files.")

if __name__ == "__main__":
    main()