"""
Run the DynaPort dashboard.

This script launches the DynaPort web dashboard for monitoring and managing
port allocations and services.
"""

import sys
import argparse
from dynaport.web_dashboard import run_dashboard


def main():
    """Run the DynaPort dashboard."""
    parser = argparse.ArgumentParser(description="Run the DynaPort dashboard")
    parser.add_argument(
        "--port", "-p",
        type=int,
        default=7000,
        help="Port to run the dashboard on (default: 7000)"
    )
    
    args = parser.parse_args()
    
    print(f"Starting DynaPort dashboard on port {args.port}")
    print(f"Visit http://localhost:{args.port} to access the dashboard")
    
    try:
        run_dashboard(port=args.port)
    except KeyboardInterrupt:
        print("\nDashboard stopped")
    except Exception as e:
        print(f"Error running dashboard: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
