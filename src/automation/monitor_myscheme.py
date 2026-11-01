
"""Command-line entry point for myScheme monitoring."""

import argparse
import os

from src.automation.monitor_api import router as monitor_router,run_monitor    


def main():
    parser = argparse.ArgumentParser(
        description="Monitor registered myScheme pages."
    )

    parser.add_argument(
        "--db",
        default=os.getenv(      
            "SCHEME_DB_PATH",
            "data/government_schemes.db",
        ),
        help="Path to the project's SQLite database",
    )

    parser.add_argument(
        "--scheme-id",
        action="append",
        dest="scheme_ids",
        help="Check a specific ID; this option can be repeated",
    )

    args = parser.parse_args()

    run_monitor(
        db_path=args.db,
        scheme_ids=args.scheme_ids,
    )


if __name__ == "__main__":
    main()
