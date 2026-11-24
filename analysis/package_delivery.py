#!/usr/bin/env python3
"""Package the formal manuscript, figures, and small-input reconstruction code.

Run from the repository root:
  python analysis/package_delivery.py --dry-run
  python analysis/package_delivery.py --output-dir analysis/delivery --verify-reproduction

The packager uses only the Python standard library. Optional reconstruction
verification needs the NumPy/Matplotlib dependencies of the plotting script.
It does not compile TeX, rerun models, upload files, or change source results.
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path, PurePosixPath
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile


ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper"
FORMAL_FIGURES = (
    "story_overview",
    "figure2_diagnosis",
    "figure3_method",
    "data_fig3_diagnosis",
    "data_fig4_causal",
    "data_fig5_content",
    "data_app_localization",
    "data_app_necessity",
    "data_app_ablation",
    "data_app_capabilities",
)
NUMERICAL_FIGURES = FORMAL_FIGURES[3:]
VECTOR_OVERVIEWS = ("story_overview",)
STYLE_FILES = ("icml2027.sty", "icml2027.bst", "algorithm.sty", "algorithmic.sty", "fancyhdr.sty")
ARTIFACT_NAMES = (
    "coretrace_overleaf.zip",
    "coretrace_figures.zip",
    "coretrace_plotting_code.zip",
    "coretrace_paper.pdf",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def source_path(relative: str) -> Path:
    """Accept existing regular files strictly inside the project."""
    posix = PurePosixPath(relative)
    if posix.is_absolute() or ".." in posix.parts or not posix.parts:
        raise ValueError(f"Unsafe project-relative input path: {relative}")
    path = (ROOT / Path(*posix.parts)).resolve()
    if not path.is_relative_to(ROOT) or not path.is_file():
        raise FileNotFoundError(f"Required project input is missing or outside the project: {relative}")
    return path


def read_json(relative: str):
    return json.loads(source_path(relative).read_text(encoding="utf-8"))


def git_output(*args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(ROOT), *args], capture_output=True, text=True, check=True, timeout=10
        )
        return result.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None


def dependency_versions() -> dict[str, str | None]:
    result = {}
    for name in ("numpy", "matplotlib"):
        try:
            result[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            result[name] = None
    return result


def requirements_text(versions: dict[str, str | None]) -> str:
    compatible = {"numpy": "numpy>=1.24,<3", "matplotlib": "matplotlib>=3.7,<4"}
    lines = ["# Python >=3.10. Exact tested versions and Python version are recorded in SOURCE.json."]
    for name, version in versions.items():
        if version:
            lines.append(f"# Tested: {name}=={version}")
        lines.append(compatible[name])
    return "\n".join(lines) + "\n"


def load_reconstruction_inputs() -> tuple[set[str], list[dict]]:
    plot_manifest = source_path("analysis/figure_data/input_manifest.csv")
    with plot_manifest.open(newline="", encoding="utf-8") as handle:
        records = list(csv.DictReader(handle))
    if not records or not {"path", "sha256"}.issubset(records[0]):
        raise ValueError("Invalid or empty figure input manifest; rerun python analysis/plot_results.py")
    inputs = set()
    for record in records:
        path = source_path(record["path"])
        if path.suffix.lower() not in {".json", ".csv"}:
            raise ValueError(f"Unexpected non-summary figure input: {record['path']}")
        if sha256(path) != record["sha256"]:
            raise ValueError(
                f"Stale figure input manifest for {record['path']}. "
                "Rerun python analysis/plot_results.py before packaging."
            )
        inputs.add(record["path"])
    table_inputs = read_json("analysis/figure_data/table_inputs.json")
    if not isinstance(table_inputs, list) or not table_inputs:
        raise ValueError("Invalid table input list; rerun python analysis/build_tables.py")
    for relative in table_inputs:
        path = source_path(relative)
        if path.suffix.lower() not in {".json", ".csv"}:
            raise ValueError(f"Unexpected non-summary table input: {relative}")
        inputs.add(relative)
    metadata = [{"path": relative, "bytes": source_path(relative).stat().st_size,
                 "sha256": sha256(source_path(relative))} for relative in sorted(inputs)]
    return inputs, metadata


def overleaf_files() -> dict[str, Path]:
    files = {}
    required = ["main.tex", "related_work.tex", "references.bib", "README.md", "Makefile", *STYLE_FILES]
    for relative in required:
        files[relative] = source_path(f"paper/{relative}")
    for folder in ("sections", "tables"):
        found = sorted((PAPER / folder).rglob("*.tex"))
        if not found:
            raise FileNotFoundError(f"No manuscript files found under paper/{folder}")
        for path in found:
            relative = path.relative_to(PAPER).as_posix()
            files[relative] = source_path(f"paper/{relative}")
    for stem in FORMAL_FIGURES:
        relative = f"figures/{stem}.pdf"
        files[relative] = source_path(f"paper/{relative}")
    if (PAPER / "main.bbl").is_file():
        files["main.bbl"] = source_path("paper/main.bbl")
    return files


def check_tex_dependencies(files: dict[str, Path]) -> list[str]:
    issues = []
    graphics = set()
    for relative, path in files.items():
        if path.suffix != ".tex":
            continue
        # Remove ordinary comments, preserving escaped percentage signs.
        text = re.sub(r"(?<!\\)%[^\n]*", "", path.read_text(encoding="utf-8"))
        for target in re.findall(r"\\(?:input|include)\{([^}]+)\}", text):
            if "\\" in target:
                issues.append(f"Cannot resolve macro-based local input in {relative}: {target}")
                continue
            resolved = target if Path(target).suffix else target + ".tex"
            if resolved not in files:
                issues.append(f"Unpackaged local input in {relative}: {resolved}")
        for target in re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", text):
            resolved = target if Path(target).suffix else target + ".pdf"
            graphics.add(resolved)
            if resolved not in files:
                issues.append(f"Unpackaged figure in {relative}: {resolved}; use the formal PDF asset")
        for target in re.findall(r"\\bibliography\{([^}]+)\}", text):
            for bib in target.split(","):
                resolved = bib.strip() + ".bib"
                if resolved not in files:
                    issues.append(f"Unpackaged bibliography in {relative}: {resolved}")
    unused = {f"figures/{stem}.pdf" for stem in FORMAL_FIGURES} - graphics
    if unused:
        issues.append("Formal figures are not referenced by the manuscript: " + ", ".join(sorted(unused)))
    return issues


def compiled_pdf_issues(files: dict[str, Path]) -> list[str]:
    pdf = PAPER / "main.pdf"
    if not pdf.is_file():
        return ["Missing paper/main.pdf. Compile and visually check the complete paper with analysis/compile_paper.sh, then copy the verified PDF to paper/main.pdf."]
    with pdf.open("rb") as handle:
        if not handle.read(8).startswith(b"%PDF-"):
            return ["paper/main.pdf does not have a PDF header."]
    dependencies = [path for path in files.values()
                    if path.suffix in {".tex", ".bib", ".sty", ".bst", ".pdf"}]
    newer = [path.relative_to(ROOT).as_posix() for path in dependencies
             if path.stat().st_mtime > pdf.stat().st_mtime + 1.0]
    if newer:
        return ["paper/main.pdf predates manuscript inputs. Recompile before packaging: " + ", ".join(newer)]
    return []


def source_metadata(inputs: list[dict], versions: dict[str, str | None]) -> dict:
    snapshot = read_json("analysis/internal/source_snapshot.json")
    status = git_output("status", "--porcelain")
    return {
        "repository": "https://github.com/litxiaoyao/coretrace",
        "scientific_source_commit": snapshot.get("source_commit"),
        "audited_source_commit": snapshot.get("audit_source_commit"),
        "source_commit_roles": snapshot.get("commit_roles"),
        "packaged_git_head": git_output("rev-parse", "HEAD"),
        "uncommitted_worktree_changes": None if status is None else bool(status),
        "template": {
            "year": snapshot.get("template_year"),
            "author_instructions": snapshot.get("verified_official_instructions"),
            "style_archive": snapshot.get("source_url"),
        },
        "python_version": platform.python_version(),
        "numerical_dependencies": versions,
        "reconstruction_scope": "Seven numerical figures, one vector story overview, and all LaTeX tables from supplied small inputs",
        "reconstruction_inputs": "Completed experiment summaries and derived measurements supplied with the package",
        "input_files": inputs,
    }


def archive_write(path: Path, files: dict[str, Path], virtual: dict[str, str] | None = None) -> dict:
    virtual = virtual or {}
    collision = set(files) & set(virtual)
    if collision:
        raise ValueError(f"Archive entry collision: {sorted(collision)}")
    size = 0
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name in sorted(set(files) | set(virtual)):
            safe = PurePosixPath(name)
            if safe.is_absolute() or ".." in safe.parts:
                raise ValueError(f"Unsafe archive entry: {name}")
            payload = files[name].read_bytes() if name in files else virtual[name].encode("utf-8")
            item = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            item.compress_type = zipfile.ZIP_DEFLATED
            item.external_attr = 0o100644 << 16
            archive.writestr(item, payload, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
            size += len(payload)
    with zipfile.ZipFile(path) as archive:
        bad = archive.testzip()
        if bad is not None:
            raise RuntimeError(f"Archive CRC validation failed: {path.name}/{bad}")
    return {"entries": len(files) + len(virtual), "uncompressed_bytes": size}


def verify_reconstruction(archive_path: Path, workspace: Path) -> dict:
    tree = workspace / "isolated_reconstruction"
    tree.mkdir()
    with zipfile.ZipFile(archive_path) as archive:
        for entry in archive.namelist():
            name = PurePosixPath(entry)
            if name.is_absolute() or ".." in name.parts:
                raise ValueError(f"Unsafe extraction path: {entry}")
        archive.extractall(tree)
    # Ensure validation observes regenerated data rather than the supplied CSV copies.
    for csv_path in (tree / "analysis" / "figure_data").glob("data_*.csv"):
        csv_path.unlink()
    environment = os.environ.copy()
    environment["PYTHONPATH"] = ""
    environment["MPLCONFIGDIR"] = str(workspace / "isolated_mpl_config")
    commands = ([sys.executable, "analysis/plot_results.py"],
                [sys.executable, "analysis/build_tables.py"],
                [sys.executable, "analysis/draw_story_overview.py"])
    for command in commands:
        run = subprocess.run(command, cwd=tree, env=environment, capture_output=True,
                             text=True, timeout=180)
        if run.returncode:
            raise RuntimeError(
                "Standalone reconstruction failed for " + " ".join(command[1:]) + "\n"
                + run.stdout[-3000:] + "\n" + run.stderr[-5000:]
            )
    missing = [f"paper/figures/{stem}.{extension}" for stem in (*NUMERICAL_FIGURES, *VECTOR_OVERVIEWS)
               for extension in ("pdf", "png")
               if not (tree / "paper" / "figures" / f"{stem}.{extension}").is_file()]
    if missing:
        raise RuntimeError("Standalone reconstruction omitted figures: " + ", ".join(missing))
    overview_assets = 0
    for stem in VECTOR_OVERVIEWS:
        for extension in ("pdf", "png"):
            original = source_path(f"paper/figures/{stem}.{extension}")
            reproduced = tree / "paper" / "figures" / original.name
            if reproduced.read_bytes() != original.read_bytes():
                raise RuntimeError(
                    f"Reconstructed story asset differs: {original.name}. "
                    "Regenerate it with the current script and dependencies before packaging."
                )
            overview_assets += 1
    table_count = 0
    for original in sorted((PAPER / "tables").glob("*.tex")):
        reproduced = tree / "paper" / "tables" / original.name
        if not reproduced.is_file() or reproduced.read_bytes() != original.read_bytes():
            raise RuntimeError(f"Reconstructed table differs: {original.name}. Rerun the table builder before packaging.")
        table_count += 1
    csv_count = 0
    for original in sorted((ROOT / "analysis" / "figure_data").glob("data_*.csv")):
        reproduced = tree / "analysis" / "figure_data" / original.name
        if not reproduced.is_file() or reproduced.read_bytes() != original.read_bytes():
            raise RuntimeError(f"Reconstructed figure data differ: {original.name}. Rerun the complete plotting script.")
        csv_count += 1
    return {"performed": True, "passed": True, "numerical_figures": len(NUMERICAL_FIGURES),
            "vector_overviews": len(VECTOR_OVERVIEWS), "overview_assets_compared": overview_assets,
            "table_files_compared": table_count, "csv_files_compared": csv_count,
            "commands": ["python analysis/plot_results.py", "python analysis/build_tables.py",
                         "python analysis/draw_story_overview.py"],
            "scope": "Fresh extraction, cleared PYTHONPATH, supplied small inputs only; no model execution"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "analysis" / "delivery",
                        help="Delivery directory (default: analysis/delivery; other repository directories are refused)")
    parser.add_argument("--dry-run", action="store_true", help="Inspect the complete plan without writing packages")
    parser.add_argument("--verify-reproduction", action="store_true",
                        help="Regenerate numerical figures, all tables, and the vector story overview from the isolated code archive")
    parser.add_argument("--include-audit-code", action="store_true",
                        help="Include optional verification scripts, which need the full repository/data to run")
    args = parser.parse_args()
    output = args.output_dir.expanduser().resolve()
    if output.is_relative_to(ROOT) and not output.is_relative_to(ROOT / "analysis" / "delivery"):
        raise ValueError("Repository output paths must be analysis/delivery or its descendants; external delivery directories are also supported.")

    inputs, input_records = load_reconstruction_inputs()
    manuscript = overleaf_files()
    issues = check_tex_dependencies(manuscript) + compiled_pdf_issues(manuscript)
    figures = {f"{stem}.{extension}": source_path(f"paper/figures/{stem}.{extension}")
               for stem in FORMAL_FIGURES for extension in ("pdf", "png")}
    figures["captions.json"] = source_path("paper/figures/captions.json")
    code_paths = set(inputs) | {
        "analysis/plot_results.py", "analysis/build_tables.py", "analysis/package_delivery.py",
        "analysis/draw_story_overview.py", "analysis/REPRODUCIBILITY.md",
        "analysis/wrap_conceptual_figures.py", "analysis/README.md", "analysis/image_prompts.json",
        "analysis/internal/source_snapshot.json", "analysis/internal/legacy_figure_metadata.json",
        "paper/figures/captions.json", "paper/figures/figure_sources.json",
    }
    code_paths.update(path.relative_to(ROOT).as_posix()
                      for path in (ROOT / "analysis" / "figure_data").iterdir()
                      if path.is_file() and path.suffix in {".csv", ".json", ".md"})
    if args.include_audit_code:
        code_paths.update(path.relative_to(ROOT).as_posix()
                          for path in (ROOT / "analysis").glob("audit_*.py"))
    code = {relative: source_path(relative) for relative in sorted(code_paths)}
    versions = dependency_versions()
    metadata = source_metadata(input_records, versions)
    plan = {
        "output_directory": str(output),
        "formal_figures": list(FORMAL_FIGURES),
        "overleaf_file_count": len(manuscript),
        "figure_asset_count": 2 * len(FORMAL_FIGURES),
        "figure_metadata_files": ["captions.json"],
        "reconstruction_input_count": len(inputs),
        "reconstruction_input_bytes": sum(row["bytes"] for row in input_records),
        "code_file_count_before_generated_metadata": len(code),
        "compiled_pdf_exists": (PAPER / "main.pdf").is_file(),
        "issues_requiring_resolution_before_packaging": issues,
        "optional_verification_scripts": bool(args.include_audit_code),
        "verification_requested": bool(args.verify_reproduction),
    }
    if args.dry_run:
        print(json.dumps(plan, indent=2))
        return
    if issues:
        raise ValueError("Packaging requires a current, complete manuscript:\n- " + "\n- ".join(issues))
    output.mkdir(parents=True, exist_ok=True)
    watched = set(manuscript.values()) | set(figures.values()) | set(code.values()) | {PAPER / "main.pdf"}
    initial_state = {path: (path.stat().st_size, path.stat().st_mtime_ns) for path in watched}

    code_readme = """# CoReTrace figure and table reconstruction

This archive preserves the required project-relative input layout. From its root:

    python -m pip install -r analysis/requirements.txt
    python analysis/plot_results.py
    python analysis/build_tables.py
    python analysis/draw_story_overview.py

See analysis/README.md for the scientific organization, exact scope, and population
and uncertainty conventions. SOURCE.json records the scientific baseline commit,
packaging revision, dependency versions, and hashes of all small input files.
The seven numerical figures, all manuscript tables (including the two compact
main-text summaries), and the vector story overview regenerate from these files.
The two appendix conceptual illustrations are supplied separately in the formal-figure
archive; analysis/image_prompts.json records their historical prompts and edits.
analysis/REPRODUCIBILITY.md distinguishes the verified analysis scope from a full
GPU rerun and records the audited repository revision. Current figure provenance
and explicitly archived legacy metadata accompany this reconstruction package.

Optional audit_*.py scripts, when included, use the full repository data and
prediction archives for further analyses. package_delivery.py likewise expects
the full working tree and a compiled manuscript when creating all delivery files.
"""
    figures_readme = "# Formal CoReTrace figures\n\n" + "\n".join(
        f"- {stem}.pdf and {stem}.png" for stem in FORMAL_FIGURES
    ) + "\n\nThe main paper has four figures: the vector story overview and the three numerical\n" \
        "diagnosis, intervention, and content-validation figures. The appendix has the\n" \
        "two supplied conceptual illustrations plus four numerical figures. The seven\n" \
        "numerical PDFs have 300-dpi PNG previews; the vector overview has a 400-dpi\n" \
        "preview. Appendix conceptual PDFs embed their supplied PNGs unchanged.\n" \
        "captions.json records figure roles; the manuscript provides the final captions.\n"

    with tempfile.TemporaryDirectory(prefix=".coretrace_package_", dir=output) as temporary:
        work = Path(temporary)
        archive_stats = {}
        archive_stats[ARTIFACT_NAMES[0]] = archive_write(work / ARTIFACT_NAMES[0], manuscript)
        archive_stats[ARTIFACT_NAMES[1]] = archive_write(
            work / ARTIFACT_NAMES[1], figures, {"README.md": figures_readme})
        archive_stats[ARTIFACT_NAMES[2]] = archive_write(
            work / ARTIFACT_NAMES[2], code,
            {"README.md": code_readme, "analysis/requirements.txt": requirements_text(versions),
             "SOURCE.json": json.dumps(metadata, indent=2, ensure_ascii=False) + "\n"})
        verified = ({"performed": False, "passed": None}
                    if not args.verify_reproduction else verify_reconstruction(work / ARTIFACT_NAMES[2], work))
        shutil.copy2(PAPER / "main.pdf", work / ARTIFACT_NAMES[3])
        artifact_info = {name: {"bytes": (work / name).stat().st_size, "sha256": sha256(work / name)}
                         for name in ARTIFACT_NAMES}
        manifest = {
            "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "source": metadata,
            "formal_figures": list(FORMAL_FIGURES),
            "archives": archive_stats,
            "artifacts": artifact_info,
            "reconstruction_verification": verified,
            "optional_verification_code_included": bool(args.include_audit_code),
        }
        manifest_name = "delivery_manifest.json"
        (work / manifest_name).write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        checksum_names = [*ARTIFACT_NAMES, manifest_name]
        (work / "SHA256SUMS.txt").write_text(
            "".join(f"{sha256(work / name)}  {name}\n" for name in checksum_names), encoding="utf-8")
        changed = [path.relative_to(ROOT).as_posix() for path, state in initial_state.items()
                   if not path.is_file() or (path.stat().st_size, path.stat().st_mtime_ns) != state]
        if changed:
            raise RuntimeError("Source files changed during packaging; rerun after edits finish: "
                               + ", ".join(sorted(changed)))
        for name in [*checksum_names, "SHA256SUMS.txt"]:
            os.replace(work / name, output / name)
    print(json.dumps({"output_directory": str(output), "artifacts": artifact_info,
                      "reconstruction_verification": verified,
                      "checksum_file": str(output / "SHA256SUMS.txt")}, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (FileNotFoundError, ValueError, RuntimeError, subprocess.TimeoutExpired) as exc:
        print(f"Packaging error: {exc}", file=sys.stderr)
        raise SystemExit(1)
