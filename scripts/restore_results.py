"""Restore packaged datasets and experiment records after cloning the repository."""
from pathlib import Path
import gzip
import shutil


def main():
    root = Path(__file__).resolve().parents[1]
    restored = 0
    for directory in (root / "data", root / "outputs"):
        for source in sorted(directory.rglob("*.jsonl.gz")):
            target = source.with_suffix("")
            if target.exists():
                continue
            temporary = target.with_suffix(target.suffix + ".tmp")
            try:
                with gzip.open(source, "rb") as src, temporary.open("wb") as dst:
                    shutil.copyfileobj(src, dst, 1024 * 1024)
                temporary.replace(target)
            finally:
                temporary.unlink(missing_ok=True)
            restored += 1
    print(f"Restored {restored} JSONL files. Existing files were preserved.")


if __name__ == "__main__":
    main()
