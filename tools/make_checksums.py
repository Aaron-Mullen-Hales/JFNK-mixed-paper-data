#!/usr/bin/env python3
"""Record sizes and md5 sums of the package files.

  tools/make_checksums.py             write INPUT_CHECKSUMS.tsv (the plotting inputs: case, role, path, bytes, md5)

Run this only when a file is replaced ON PURPOSE; ./Allrun --check then verifies the inputs against these records.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.dont_write_bytecode = True
from package_info import REQUIRED_INPUTS, ROOT, md5  # noqa: E402



def main() -> None:
    missing = [p for _, _, p in REQUIRED_INPUTS if not (ROOT / p).is_file()]
    if missing:
        raise SystemExit("ERROR: required inputs missing:\n  " + "\n  ".join(missing))
    with (ROOT / "INPUT_CHECKSUMS.tsv").open("w") as out:
        out.write("# Required inputs of the plotting commands in Allrun (case, role, path, bytes, md5).\n")
        out.write("# Verified by ./Allrun --check and before/after every ./Allrun.  Regenerate with tools/make_checksums.py.\n")
        out.write("case\trole\tpath\tbytes\tmd5\n")
        for case, role, path in REQUIRED_INPUTS:
            file = ROOT / path
            out.write(f"{case}\t{role}\t{path}\t{file.stat().st_size}\t{md5(file)}\n")
    print(f"wrote INPUT_CHECKSUMS.tsv ({len(REQUIRED_INPUTS)} inputs)")


if __name__ == "__main__":
    main()
