
"""
resolve_space_audit.py

Audit (and optionally clean) DaVinci Resolve-related storage: proxies, optimized media,
render cache, gallery stills, and backups. Safe by default: deletion requires explicit flags
AND interactive confirmation.

- Scan a folder (and all subfolders)
- Read file metadata only (name, size, last modified)
- Group files into categories (proxy, optimized, render_cache, stills, backups, other)
- Compute totals and list the largest files
- Print a summary and (optionally) write a JSON + CSV report

Usage examples:
  # Audit a drive/folder and write a report (JSON + CSV) without deleting anything
  python resolve_space_audit.py "D:\Videos" --report out/report

  # Show top 30 largest files under the root
  python resolve_space_audit.py "D:\Videos" --top 30

  # List only Resolve categories (size by category + paths), no deletion
  python resolve_space_audit.py "D:\Videos" --categories-only

  # Delete ALL proxy media found (after an interactive double-confirm)
  python resolve_space_audit.py "D:\Videos" --delete-category proxy

  # Delete files by extension (e.g., old .dvcc cache clips) older than 30 days
  python resolve_space_audit.py "D:\Videos" --delete-ext .dvcc --min-age-days 30

Recommended workflow:
  1) Run in audit mode and inspect the report.
  2) Start with deleting cache/proxy/optimized media you are CERTAIN can be regenerated.
  3) Keep a dry-run mindset: use --min-age-days to avoid nuking recent work.
"""

from pathlib import Path      # path handling (safer than raw strings)
import os                     # os.walk to traverse directories
import argparse               # parse command-line flags/options
import json                   # write JSON report
import csv                    # write CSV report
from datetime import datetime, timedelta # timestamps for "generated_at" and age filters

# Heuristics / common Resolve folder names (customize if yours differ)
CATEGORY_PATTERNS = {
    "proxy": ["Proxy", "ProxyMedia", "Proxies"],
    "optimized": ["OptimizedMedia", "Optimized Media"],
    "render_cache": ["CacheClip", "RenderCache", "Render Cache"],
    "stills": ["Gallery", "Stills", "GalleryStills"],
    "backups": ["Backups", "Project Backups", "Resolve Backups"],
}

# File extensions that are often large/temporary-ish (customize)
LARGE_EXTS = [
    ".mov", ".mp4", ".mxf", ".braw", ".dng", ".wav", ".caf", ".flac", ".dvcc", ".dpx",
    ".exr", ".tif", ".tiff", ".prores", ".r3d", ".mkv"
]

def human(n: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    s = 0
    f = float(n)
    while f >= 1024 and s < len(units)-1:
        f /= 1024.0
        s += 1
    return f"{f:.2f} {units[s]}"

def walk_files(root: Path):
    for dirpath, dirnames, filenames in os.walk(root):
        # skip system or hidden dirs heuristically
        # (customize if needed)
        for name in filenames:
            p = Path(dirpath) / name
            try:
                size = p.stat().st_size
                mtime = p.stat().st_mtime
            except (PermissionError, FileNotFoundError):
                continue
            yield p, size, mtime

def classify_category(path: Path) -> str | None:
    parts = [p.lower() for p in path.parts]
    for cat, needles in CATEGORY_PATTERNS.items():
        for n in needles:
            if n.lower() in parts:
                return cat
    return None

def collect_stats(root: Path, top_n: int = 30):
    total_bytes = 0
    by_ext = {}
    largest = []
    by_category_bytes = {"proxy": 0, "optimized": 0, "render_cache": 0, "stills": 0, "backups": 0, "other": 0}
    by_category_paths = {k: [] for k in by_category_bytes.keys()}

    now = datetime.now().timestamp()

    for p, size, mtime in walk_files(root):
        total_bytes += size
        ext = p.suffix.lower()
        by_ext[ext] = by_ext.get(ext, 0) + size

        cat = classify_category(p)
        if cat is None:
            cat = "other"

        by_category_bytes[cat] += size
        by_category_paths[cat].append({"path": str(p), "size": size, "mtime": mtime})

        # maintain largest list (top_n)
        largest.append((size, str(p)))
        if len(largest) > top_n * 3:
            largest.sort(reverse=True)
            largest = largest[:top_n]

    # finalize largest
    largest.sort(reverse=True)
    largest = largest[:top_n]

    # ext stats sorted
    by_ext_sorted = sorted(by_ext.items(), key=lambda kv: kv[1], reverse=True)

    return {
        "root": str(root),
        "total_bytes": total_bytes,
        "total_human": human(total_bytes),
        "by_ext": [{"ext": k, "bytes": v, "human": human(v)} for k, v in by_ext_sorted],
        "largest_files": [{"path": p, "bytes": s, "human": human(s)} for s, p in largest],
        "by_category_bytes": {k: {"bytes": v, "human": human(v)} for k, v in by_category_bytes.items()},
        "by_category_paths": by_category_paths,
        "generated_at": datetime.now().isoformat(timespec="seconds")
    }

def write_report(report_base: Path, stats: dict):
    report_base.parent.mkdir(parents=True, exist_ok=True)
    json_path = report_base.with_suffix(".json")
    csv_path = report_base.with_suffix(".csv")

    # JSON
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)

    # CSV: largest files
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["path", "bytes", "human"])
        for item in stats["largest_files"]:
            w.writerow([item["path"], item["bytes"], item["human"]])

    return str(json_path), str(csv_path)

def confirm(prompt: str) -> bool:
    ans = input(f"{prompt} [y/N]: ").strip().lower()
    return ans in ("y", "yes")

def delete_category(paths: list[dict], min_age_days: int | None):
    if min_age_days is not None:
        cutoff = datetime.now().timestamp() - (min_age_days * 86400)
        to_delete = [p for p in paths if p["mtime"] < cutoff]
    else:
        to_delete = list(paths)

    total = sum(p["size"] for p in to_delete)
    print(f"About to delete {len(to_delete)} files, total {human(total)}")
    if not confirm("Proceed with deletion?"):
        print("Aborted.")
        return 0, 0

    deleted = 0
    freed = 0
    for entry in to_delete:
        try:
            os.remove(entry["path"])
            deleted += 1
            freed += entry["size"]
        except Exception as e:
            print(f"Failed to delete {entry['path']}: {e}")

    print(f"Deleted {deleted} files, freed {human(freed)}")
    return deleted, freed

def delete_by_ext(root: Path, ext: str, min_age_days: int | None):
    ext = ext.lower()
    if not ext.startswith("."):
        ext = "." + ext

    candidates = []
    for p, size, mtime in walk_files(root):
        if p.suffix.lower() == ext:
            candidates.append({"path": str(p), "size": size, "mtime": mtime})

    total = sum(c["size"] for c in candidates)
    print(f"Found {len(candidates)} files with extension {ext} totaling {human(total)}")
    if min_age_days:
        print(f"Filtering to files older than {min_age_days} days")

    if not candidates:
        return 0, 0

    if not confirm("Proceed with deletion?"):
        print("Aborted.")
        return 0, 0

    deleted = 0
    freed = 0
    from datetime import datetime
    cutoff = datetime.now().timestamp() - (min_age_days * 86400) if min_age_days else None

    for c in candidates:
        if cutoff and c["mtime"] >= cutoff:
            continue
        try:
            os.remove(c["path"])
            deleted += 1
            freed += c["size"]
        except Exception as e:
            print(f"Failed to delete {c['path']}: {e}")

    print(f"Deleted {deleted} files, freed {human(freed)}")
    return deleted, freed

def main():
    ap = argparse.ArgumentParser(description="Audit and clean DaVinci Resolve storage (safe by default).")
    ap.add_argument("root", type=str, help="Root folder to scan (e.g., a Projects or Media drive)")
    ap.add_argument("--report", type=str, help="Base path (without extension) to write JSON + CSV reports")
    ap.add_argument("--top", type=int, default=30, help="How many largest files to list (default: 30)")
    ap.add_argument("--categories-only", action="store_true", help="Only print category sizes and exit")
    ap.add_argument("--delete-category", choices=list(CATEGORY_PATTERNS.keys()), help="Delete files in a known category (proxy/optimized/render_cache/stills/backups)")
    ap.add_argument("--delete-ext", type=str, help="Delete files by extension (e.g., .dvcc)")
    ap.add_argument("--min-age-days", type=int, help="Only delete files older than N days (safety valve)")

    args = ap.parse_args()
    root = Path(args.root).expanduser()

    if not root.exists():
        print(f"Root path does not exist: {root}")
        return 2

    stats = collect_stats(root, top_n=args.top)

    print(f"Scanned: {stats['root']}  |  Total: {stats['total_human']}  |  Generated at: {stats['generated_at']}")
    print("\n== Size by category ==")
    for cat, info in stats["by_category_bytes"].items():
        print(f"{cat:>12}: {info['human']}")

    if args.categories_only:
        return 0

    print("\n== Top largest files ==")
    for item in stats["largest_files"]:
        print(f"{item['human']:>10}  {item['path']}")

    print("\n== Top extensions by space ==")
    for item in stats["by_ext"][:20]:
        print(f"{item['human']:>10}  {item['ext'] or '(no ext)'}")

    if args.report:
        json_path, csv_path = write_report(Path(args.report), stats)
        print(f"\nWrote report: {json_path}")
        print(f"Wrote CSV:    {csv_path}")

    # Deletion flows
    if args.delete_category:
        cat = args.delete_category
        paths = stats["by_category_paths"][cat]
        if not paths:
            print(f"No files found for category '{cat}'.")
            return 0
        print(f"\nPreparing deletion for category: {cat}")
        delete_category(paths, args.min_age_days)

    if args.delete_ext:
        delete_by_ext(root, args.delete_ext, args.min_age_days)

    return 0

if __name__ == "__main__":
    raise SystemExit(main())

