"""Restore packaged datasets and experiment records after cloning the repository."""
from pathlib import Path
import gzip
import shutil


def main():
    root = Path(__file__).resolve().parents[1]
    restored = 0
    for directory in (root / "data", root / "outputs"):
        for first in sorted(directory.rglob("*.jsonl.gz.part0000")):
            target = first.with_name(first.name.removesuffix(".part0000"))
            if target.exists():
                continue
            parts = sorted(first.parent.glob(target.name + ".part*"))
            expected = [target.name + f".part{i:04d}" for i in range(len(parts))]
            if [part.name for part in parts] != expected:
                raise ValueError(f"Missing archive part: {target}")
            temporary = target.with_suffix(target.suffix + ".tmp")
            try:
                with temporary.open("wb") as dst:
                    for part in parts:
                        with part.open("rb") as src:
                            shutil.copyfileobj(src, dst, 1024 * 1024)
                temporary.replace(target)
            finally:
                temporary.unlink(missing_ok=True)
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
