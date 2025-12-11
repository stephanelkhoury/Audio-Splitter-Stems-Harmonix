#!/usr/bin/env python3
"""
Simple launcher for Harmonix Dashboard
Usage: python run_dashboard.py
"""

import sys
import subprocess
from pathlib import Path

def main():
    print("=" * 60)
    print("  🎵 Harmonix Audio Splitter Dashboard")
    print("=" * 60)
    print()
    
    # Check if we're in the right directory
    dashboard_module = Path(__file__).parent / "src" / "harmonix_splitter" / "dashboard.py"
    if not dashboard_module.exists():
        print("❌ Error: Dashboard module not found!")
        print("   Make sure you're running this from the project root directory.")
        sys.exit(1)
    
    print("🚀 Starting dashboard...")
    print()
    print("   Open your browser to: http://localhost:5000")
    print()
    print("   Press Ctrl+C to stop")
    print()
    print("=" * 60)
    print()
    
    try:
        # Run the dashboard
        subprocess.run([
            sys.executable,
            "-m",
            "harmonix_splitter.dashboard"
        ])
    except KeyboardInterrupt:
        print("\n\n👋 Dashboard stopped. Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
