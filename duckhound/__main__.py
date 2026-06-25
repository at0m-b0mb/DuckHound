"""Allow `python -m duckhound` to launch the GUI."""
import sys

from duckhound.app import main

if __name__ == "__main__":
    sys.exit(main())
