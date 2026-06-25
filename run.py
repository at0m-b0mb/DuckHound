#!/usr/bin/env python3
"""DuckHound launcher.

Usage:
    python run.py            # launch the GUI
    python run.py --cli      # headless terminal monitor
    python run.py --demo     # GUI with a simulated attack feed (no permissions needed)
    python run.py --grant    # trigger the macOS permission prompts + open Settings
    python run.py --doctor   # run the self-test (alias for scripts/diagnose.py)
"""
import sys


def _grant() -> int:
    from duckhound.core import permissions
    print("DuckHound — requesting keyboard-monitoring access…\n")
    granted_before, detail = permissions.keystroke_access()
    permissions.request_keystroke_access()  # prompts + opens Settings panes
    print(f"Current: {detail}")
    print("\nIn System Settings → Privacy & Security, switch ON BOTH:")
    print("  • Input Monitoring   • Accessibility")
    print(f"for {permissions.host_app_hint() or 'your terminal'}.")
    print("\nThen FULLY QUIT that app (Cmd-Q) and relaunch it.\n")
    return 0


if __name__ == "__main__":
    if "--grant" in sys.argv:
        sys.exit(_grant())
    if "--doctor" in sys.argv:
        import runpy
        runpy.run_path("scripts/diagnose.py", run_name="__main__")
        sys.exit(0)
    if "--cli" in sys.argv:
        from duckhound.cli import main
        sys.exit(main())
    from duckhound.app import main
    sys.exit(main())
