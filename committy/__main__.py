"""Main entry point for Committy."""

import sys
from committy.cli.main import main


def run_main():
    """Run the main Committy application."""
    print("Committy - AI-powered git commit message generator")
    sys.exit(main())


if __name__ == "__main__":
    run_main()