"""CLI for deterministic AnnabanAI claim boundary linting."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .lint import lint_claim_text


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--text", help="Claim text to inspect")
    source.add_argument("--file", type=Path, help="UTF-8 text file to inspect")
    args = parser.parse_args()
    text = args.text if args.text is not None else args.file.read_text(encoding="utf-8")
    result = lint_claim_text(text)
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    return 1 if result.validation_status == "FAILED" else 0


if __name__ == "__main__":
    raise SystemExit(main())
