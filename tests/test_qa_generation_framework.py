#!/usr/bin/env python3
"""Unit tests for ``qa_generation_framework.py``.

These tests cover the non-GUI building blocks of the QA generation framework:

* ``trajectory_length_prefix`` — bucketing of trajectory durations into the
  SHORT / MEDIUM / LONG UUID prefixes.
* ``load_entries_from_json`` — parsing of both the structured export format
  produced by ``milvus_memory_inspector_multimodal*.py --export-json`` and a
  flat list-of-dicts format, including restoration of the Milvus time offset.
* ``ImageIndex`` — per-role image directory indexing and nearest-timestamp
  lookup with a configurable ``max_delta`` tolerance.
* ``write_qa_csv`` — CSV serialisation that mirrors
  ``remembr/data/navqa/data.csv``.

The Tkinter GUI itself is intentionally not exercised here so the suite can
run headlessly in CI.
"""

import csv
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

# Make the project root importable when running ``pytest`` from the repo root.
sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))

from qa_generation_framework import (
    trajectory_length_prefix,
    load_entries_from_json,
    ImageIndex,
    write_qa_csv,
    CSV_HEADER,
    LEGACY_MILVUS_TIME_OFFSET,
)


class TestTrajectoryPrefix(unittest.TestCase):
    """Boundary tests for the SHORT/MEDIUM/LONG bucketing of trajectory length.

    Spec (from the user requirement):
        SHORT  : < 2 min
        MEDIUM : 2 min ≤ d ≤ 7 min
        LONG   : > 7 min
    """

    def test_short(self):
        """Durations strictly under 2 minutes map to SHORT."""
        self.assertEqual(trajectory_length_prefix(0), "SHORT")
        # 119 s is just under the 2-minute boundary.
        self.assertEqual(trajectory_length_prefix(119), "SHORT")

    def test_medium(self):
        """The inclusive 2–7 minute window maps to MEDIUM."""
        self.assertEqual(trajectory_length_prefix(120), "MEDIUM")  # exactly 2 min
        self.assertEqual(trajectory_length_prefix(300), "MEDIUM")  # mid-range
        self.assertEqual(trajectory_length_prefix(420), "MEDIUM")  # exactly 7 min

    def test_long(self):
        """Anything above 7 minutes maps to LONG."""
        self.assertEqual(trajectory_length_prefix(421), "LONG")
        self.assertEqual(trajectory_length_prefix(3600), "LONG")


class TestLoadEntriesFromJson(unittest.TestCase):
    """Exercises both supported JSON shapes and the Milvus time-offset fix."""

    def test_structured_export_format(self):
        """The ``--export-json`` format: nested ``position``/``orientation``/
        ``content`` blocks. Entries must be sorted by time on load.

        Uses unix-scale timestamps (> 1e9) so the loader treats them as
        already-full timestamps and does not apply the legacy offset.
        """
        base = LEGACY_MILVUS_TIME_OFFSET  # a plausible "real" session epoch
        data = {
            "metadata": {"collection_name": "x"},
            "items": [
                {
                    # Second in time — should appear last after sorting.
                    "timestamp": base + 10.0,
                    "position": {"x": 1.0, "y": 2.0, "z": 0.0,
                                 "raw": [1.0, 2.0, 0.0]},
                    "orientation": {"theta_radians": 0.5},
                    "content": {"visual_caption": "a tree",
                                "audio_caption": "birds"},
                },
                {
                    # First in time — should appear first after sorting.
                    "timestamp": base + 5.0,
                    "position": {"x": 0.0, "y": 0.0, "z": 0.0,
                                 "raw": [0.0, 0.0, 0.0]},
                    "orientation": {"theta_radians": 0.0},
                    "content": {"visual_caption": "start",
                                "audio_caption": ""},
                },
            ],
        }
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            path = f.name
        try:
            entries = load_entries_from_json(path)
            self.assertEqual(len(entries), 2)
            # Loader must sort ascending by time, and must not mutate
            # already-full unix timestamps.
            self.assertEqual(entries[0]["time"], base + 5.0)
            self.assertEqual(entries[1]["time"], base + 10.0)
            # Field extraction from the nested structure.
            self.assertEqual(entries[1]["caption"], "a tree")
            self.assertEqual(entries[1]["audio_caption"], "birds")
            self.assertEqual(entries[1]["position"], [1.0, 2.0, 0.0])
        finally:
            os.unlink(path)

    def test_flat_format(self):
        """A flat list of dicts (e.g. a hand-written or alternative export).
        Verifies that ``time`` stored as ``[t, 0.0]`` (legacy fp32 vector
        form) and ``robot_data`` stored as a JSON string are both decoded.
        """
        base = LEGACY_MILVUS_TIME_OFFSET
        data = [
            # Legacy list-form time with a full unix value in the first slot.
            {"time": [base + 3.0, 0.0], "position": [1, 2, 3], "theta": 0.1,
             "caption": "c", "audio_caption": "a", "robot_id": "ground",
             "robot_data": json.dumps({"ground": {"caption": "c"}})},
        ]
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            path = f.name
        try:
            entries = load_entries_from_json(path)
            self.assertEqual(len(entries), 1)
            # Legacy ``[t, 0.0]`` vector collapses to scalar t.
            self.assertEqual(entries[0]["time"], base + 3.0)
            self.assertEqual(entries[0]["robot_id"], "ground")
            # JSON-encoded robot_data must be decoded to a dict.
            self.assertEqual(entries[0]["robot_data"],
                             {"ground": {"caption": "c"}})
        finally:
            os.unlink(path)

    def test_new_schema_time_passthrough(self):
        """Post-fix schema: ``time`` is a full unix timestamp (fp64, > 1e9).
        The loader must leave it untouched — no offset addition."""
        big_ts = LEGACY_MILVUS_TIME_OFFSET + 50.0  # clearly a unix timestamp
        data = [{"time": big_ts, "position": [0, 0, 0], "theta": 0.0,
                 "caption": "", "audio_caption": ""}]
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            path = f.name
        try:
            entries = load_entries_from_json(path)  # default: no offset
            self.assertEqual(entries[0]["time"], big_ts)
        finally:
            os.unlink(path)

    def test_legacy_offset_restored_automatically(self):
        """Back-compat: a JSON export produced by the *old* schema stores the
        offset-subtracted value (< 1e9). The loader should auto-detect this
        and add the legacy offset back so it lines up with image filenames."""
        data = [{"time": 100.0, "position": [0, 0, 0], "theta": 0.0,
                 "caption": "", "audio_caption": ""}]
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            path = f.name
        try:
            entries = load_entries_from_json(path)  # default time_offset=0
            # Auto-restoration: small value triggers the legacy offset.
            self.assertEqual(entries[0]["time"],
                             100.0 + LEGACY_MILVUS_TIME_OFFSET)
        finally:
            os.unlink(path)

    def test_user_override_time_offset(self):
        """A user-supplied ``time_offset`` overrides the legacy default for
        the auto-restoration path."""
        custom = 500.0
        data = [{"time": 10.0, "position": [0, 0, 0], "theta": 0.0,
                 "caption": "", "audio_caption": ""}]
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            path = f.name
        try:
            entries = load_entries_from_json(path, time_offset=custom)
            self.assertEqual(entries[0]["time"], 10.0 + custom)
        finally:
            os.unlink(path)


class TestImageIndex(unittest.TestCase):
    """Per-role image indexing and nearest-timestamp matching."""

    def test_single_robot_match(self):
        """Single-robot mode: only ``pioneer_image_*`` files in the supplied
        directory are indexed; the closest-in-time image is returned."""
        with tempfile.TemporaryDirectory() as d:
            # Three pioneer images at distinct timestamps.
            for ts in (100.000, 105.500, 110.250):
                Path(d, f"pioneer_image_000001_{ts:.3f}.jpg").write_bytes(b"x")
            # A spot image in the same directory must be ignored in single mode.
            Path(d, "spot_image_000001_105.500.jpg").write_bytes(b"x")

            idx = ImageIndex({"robot": d}, "single")
            # 105.4 is closest to the 105.500 image.
            imgs = idx.images_for_entry({"time": 105.4})
            self.assertIn("robot", imgs)
            self.assertTrue(imgs["robot"].endswith("105.500.jpg"))
            self.assertIn("pioneer_image_", imgs["robot"])

    def test_multi_robot_separate_dirs(self):
        """Multi-robot mode: ground and aerial images live in *separate*
        directories; both must be returned for the same entry timestamp."""
        with tempfile.TemporaryDirectory() as gd, tempfile.TemporaryDirectory() as ad:
            Path(gd, "spot_image_000001_200.000.jpg").write_bytes(b"x")
            Path(ad, "mavic_image_000001_200.100.jpg").write_bytes(b"x")

            idx = ImageIndex({"ground": gd, "aerial": ad}, "multi")
            imgs = idx.images_for_entry({"time": 200.05})
            # Both robots' images should be located simultaneously.
            self.assertEqual(set(imgs.keys()), {"ground", "aerial"})

    def test_max_delta_configurable(self):
        """``max_delta`` (set via ``--image-max-delta``) controls how far apart
        an image timestamp may be from the entry timestamp and still match."""
        with tempfile.TemporaryDirectory() as d:
            Path(d, "pioneer_image_000001_100.000.jpg").write_bytes(b"x")

            # With a tight tolerance of 1 s, an entry at t=103 has no match.
            tight = ImageIndex({"robot": d}, "single", max_delta=1.0)
            self.assertIsNone(tight.find_closest("robot", 103.0))

            # With a loose tolerance of 10 s, the same entry now matches.
            loose = ImageIndex({"robot": d}, "single", max_delta=10.0)
            self.assertIsNotNone(loose.find_closest("robot", 103.0))

            # A per-call override beats the instance default.
            self.assertIsNotNone(tight.find_closest("robot", 103.0,
                                                    max_delta=10.0))

    def test_no_match_outside_max_delta(self):
        """An image far outside the tolerance window must not be returned."""
        with tempfile.TemporaryDirectory() as d:
            Path(d, "pioneer_image_000001_100.000.jpg").write_bytes(b"x")
            idx = ImageIndex({"robot": d}, "single")  # default max_delta=5.0
            self.assertIsNone(idx.find_closest("robot", 200.0))

    def test_missing_dir(self):
        """A non-existent image directory is handled gracefully (empty index)."""
        idx = ImageIndex({"robot": "/nonexistent/path/xyz"}, "single")
        self.assertEqual(idx.images_for_entry({"time": 1.0}), {})


class TestWriteQaCsv(unittest.TestCase):
    """CSV output must use the exact header from ``remembr/data/navqa/data.csv``
    and round-trip rows verbatim."""

    def test_roundtrip(self):
        """Write two QA rows, read them back, and confirm header + content."""
        rows = [
            ["LONG_abc", "0", "Where is the tree?", "07:59:00", "position",
             "", "[position]", "spatial"],
            ["LONG_def", "0", "Did you see a dog?", "07:59:10", "binary",
             "Yes", "yes", "descriptive"],
        ]
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False) as f:
            path = f.name
        try:
            write_qa_csv(path, rows)
            with open(path, newline="", encoding="utf-8") as f:
                reader = list(csv.reader(f))
            # First line is the fixed header; subsequent lines are the rows.
            self.assertEqual(reader[0], CSV_HEADER)
            self.assertEqual(reader[1], rows[0])
            self.assertEqual(reader[2], rows[1])
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
