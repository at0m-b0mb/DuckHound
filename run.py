#!/usr/bin/env python3
"""DuckHound launcher.

Usage:
    python run.py            # launch the GUI
    python run.py --cli      # headless terminal monitor
    python run.py --demo     # GUI with a simulated attack feed (no permissions needed)
"""
import sys

if __name__ == "__main__":
    if "--cli" in sys.argv:
        from duckhound.cli import main
        sys.exit(main())
    from duckhound.app import main
    sys.exit(main())
