"""Download/cache all source data used by the project."""

from __future__ import annotations

import argparse
import json

from term_premium.data import download_all


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download the project's FRED and New York Fed source data."
    )
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Redownload sources even when a local raw snapshot exists.",
    )
    args = parser.parse_args()

    manifest = download_all(refresh=args.refresh)
    print(json.dumps(manifest, indent=2))
    print("\nRaw data acquisition completed.")


if __name__ == "__main__":
    main()
