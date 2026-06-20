#!/usr/bin/env python3
"""
One-time timestamp repair utility for existing Milvus memory collections.

This script is intended for collections where memory `time` values were stored with
coarse second precision, causing repeated timestamps.

Repair modes:
1) images: Map entries to image filename epochs from a directory, in chronological order.
2) id:     Use entry `id` (float-like insertion timestamp) as fallback unique timestamp.

Default behavior is dry-run. Use --apply to write changes.
"""

import argparse
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from pymilvus import Collection, connections, utility

TIME_OFFSET = 1721761000.0
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def parse_epoch_from_filename(path_value: str) -> Optional[float]:
    """Extract trailing unix epoch from names like *_1776181854.610.jpg."""
    try:
        stem = Path(path_value).stem
    except Exception:
        return None

    match = re.search(r"_(\d{9,}(?:\.\d+)?)$", stem)
    if not match:
        return None

    try:
        return float(match.group(1))
    except ValueError:
        return None


def is_coarse_epoch(ts: float) -> bool:
    """True when timestamp has effectively no fractional precision."""
    if ts < 1_000_000_000:
        return False
    return abs(ts - round(ts)) < 1e-6


def restore_epoch(stored_time_field) -> float:
    """Convert stored Milvus time field back to unix epoch."""
    if isinstance(stored_time_field, list) and stored_time_field:
        val = float(stored_time_field[0])
    else:
        val = float(stored_time_field)
    if val < 1_000_000_000:
        return val + TIME_OFFSET
    return val


def to_stored_time_vector(epoch_time: float) -> List[float]:
    """Convert unix epoch back to stored vector format."""
    return [float(epoch_time) - TIME_OFFSET, 0.0]


def collect_image_timestamps(image_dir: str) -> List[float]:
    p = Path(image_dir)
    if not p.exists():
        return []

    timestamps: List[float] = []
    for entry in p.iterdir():
        if not entry.is_file():
            continue
        if entry.suffix.lower() not in IMAGE_EXTENSIONS:
            continue
        ts = parse_epoch_from_filename(entry.name)
        if ts is not None:
            timestamps.append(ts)

    timestamps.sort()
    return timestamps


def load_all_rows(collection: Collection, limit: int) -> List[Dict]:
    """Load rows with batching to avoid Milvus offset+limit issues."""
    rows: List[Dict] = []
    batch_size = min(1000, limit)
    offset = 0

    while len(rows) < limit:
        current_limit = min(batch_size, limit - len(rows))
        if current_limit <= 0:
            break

        batch = collection.query(
            expr="id != ''",
            output_fields=["*"],
            limit=current_limit,
            offset=offset,
        )
        if not batch:
            break

        rows.extend(batch)
        offset += current_limit

    return rows


def infer_updated_times(
    rows: List[Dict],
    mode: str,
    image_timestamps: Optional[List[float]] = None,
) -> List[Tuple[str, float, float]]:
    """
    Return list of (id, old_epoch, new_epoch) for rows that should be updated.
    """
    updates: List[Tuple[str, float, float]] = []

    # Stable chronological order for mapping.
    def id_as_float(r: Dict) -> float:
        try:
            return float(r.get("id", "0"))
        except (TypeError, ValueError):
            return 0.0

    ordered_rows = sorted(rows, key=id_as_float)

    if mode == "images":
        if not image_timestamps:
            return updates

        n_rows = len(ordered_rows)
        n_imgs = len(image_timestamps)

        if n_imgs >= n_rows:
            mapped = image_timestamps[-n_rows:]
        else:
            mapped = image_timestamps

        for idx, row in enumerate(ordered_rows):
            if idx >= len(mapped):
                break
            row_id = str(row["id"])
            old_epoch = restore_epoch(row.get("time", 0.0))
            new_epoch = float(mapped[idx])

            # Update only when old value is coarse or significantly different.
            if is_coarse_epoch(old_epoch) or abs(old_epoch - new_epoch) > 0.05:
                updates.append((row_id, old_epoch, new_epoch))

    elif mode == "id":
        for row in ordered_rows:
            row_id = str(row["id"])
            old_epoch = restore_epoch(row.get("time", 0.0))
            try:
                new_epoch = float(row_id)
            except ValueError:
                continue

            if old_epoch < 1_000_000_000:
                continue

            if is_coarse_epoch(old_epoch) or abs(old_epoch - new_epoch) > 0.05:
                updates.append((row_id, old_epoch, new_epoch))

    return updates


def apply_updates(collection: Collection, rows_by_id: Dict[str, Dict], updates: List[Tuple[str, float, float]]) -> int:
    """Apply updates by upserting full rows with corrected time field."""
    updated_count = 0

    for row_id, _old_epoch, new_epoch in updates:
        row = rows_by_id.get(row_id)
        if row is None:
            continue

        row["time"] = to_stored_time_vector(new_epoch)

        try:
            collection.upsert([row])
            updated_count += 1
            continue
        except Exception:
            # Fallback for environments where upsert is unavailable.
            pass

        try:
            escaped_id = row_id.replace('"', '\\"')
            collection.delete(expr=f'id == "{escaped_id}"')
            collection.insert([row])
            updated_count += 1
        except Exception as e:
            print(f"[repair] Failed to update id={row_id}: {e}")

    return updated_count


def main():
    parser = argparse.ArgumentParser(description="Repair duplicated/coarse memory timestamps in Milvus")
    parser.add_argument("--collection", "-c", required=True, help="Milvus collection name")
    parser.add_argument("--db-ip", default="127.0.0.1", help="Milvus DB host")
    parser.add_argument("--db-port", type=int, default=19530, help="Milvus DB port")
    parser.add_argument("--mode", choices=["images", "id"], default="images", help="Timestamp reconstruction mode")
    parser.add_argument("--image-dir", default="/tmp/webots_memory", help="Directory of captured images for --mode images")
    parser.add_argument("--limit", type=int, default=20000, help="Max rows to inspect")
    parser.add_argument("--apply", action="store_true", help="Write updates (default is dry-run)")

    args = parser.parse_args()

    connections.connect(host=args.db_ip, port=args.db_port)

    if not utility.has_collection(args.collection):
        print(f"[repair] Collection not found: {args.collection}")
        return

    collection = Collection(args.collection)
    collection.load()

    rows = load_all_rows(collection, limit=args.limit)
    print(f"[repair] Loaded rows: {len(rows)}")

    if not rows:
        print("[repair] Nothing to do")
        return

    rows_by_id = {str(r.get("id")): r for r in rows if r.get("id") is not None}

    image_timestamps: Optional[List[float]] = None
    if args.mode == "images":
        image_timestamps = collect_image_timestamps(args.image_dir)
        print(f"[repair] Image timestamps found: {len(image_timestamps)} from {args.image_dir}")
        if not image_timestamps:
            print("[repair] No image timestamps found; retry with --mode id or valid --image-dir")
            return

    updates = infer_updated_times(rows, mode=args.mode, image_timestamps=image_timestamps)
    print(f"[repair] Candidate updates: {len(updates)}")

    preview_n = min(10, len(updates))
    for i in range(preview_n):
        row_id, old_epoch, new_epoch = updates[i]
        print(
            f"[preview {i+1}] id={row_id} old={old_epoch:.3f} new={new_epoch:.3f} "
            f"delta={new_epoch - old_epoch:+.3f}s"
        )

    if not args.apply:
        print("[repair] Dry-run only. Re-run with --apply to write changes.")
        return

    changed = apply_updates(collection, rows_by_id, updates)
    print(f"[repair] Updated rows: {changed}")


if __name__ == "__main__":
    main()
