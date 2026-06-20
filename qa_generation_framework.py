#!/usr/bin/env python3
"""
Question & Answer Generation Framework for ReMEmbR

Allows a user to step through a robot trajectory (single-robot or multi-robot),
view the captured image(s) and memory entry at each timestamp, and enter one or
more question/answer pairs for that timestamp.

Each QA pair is assigned a UUID prefixed with the trajectory-length category:
    SHORT  : trajectory < 2 minutes
    MEDIUM : 2 minutes <= trajectory <= 7 minutes
    LONG   : trajectory > 7 minutes

When the user finishes, a CSV is written that follows the same column layout as
`remembr/data/navqa/data.csv`:
    UUID, Seq ID, Question, Timestamp with answer, Type, Text answer,
    Parsable answer, Question Category

Data sources:
    --source milvus  : pull memory entries directly from a Milvus collection
    --source json    : load a JSON file produced by
                       milvus_memory_inspector_multimodal*.py --export-json

Robot modes:
    --mode single    : single robot (pioneer3at) — one image per entry
    --mode multi     : multi-robot (spot ground + mavic aerial) — up to two
                       images per entry
"""

import argparse
import csv
import glob
import json
import os
import re
import sys
import uuid
from datetime import datetime
from pathlib import Path

import tkinter as tk
from tkinter import ttk, messagebox, filedialog

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

QUESTION_TYPES = ["binary", "position", "time", "text", "duration"]

# As of the April-2026 schema fix, Milvus stores `time` as a full-precision
# DOUBLE (raw unix seconds). No offset restoration is needed for collections
# built with the new schema. The constant below is kept only so that users
# loading *old* exported JSON files (which stored offset-subtracted fp32
# values) can pass `--time-offset 1721761000` to reconstruct full timestamps.
LEGACY_MILVUS_TIME_OFFSET = 1721761000

CSV_HEADER = [
    "UUID",
    "Seq ID",
    "Question",
    "Timestamp with answer",
    "Type",
    "Text answer",
    "Parsable answer",
    "Question Category",
]

# filename pattern: <prefix>_image_<count>_<timestamp>.jpg
IMAGE_TS_RE = re.compile(r"_(\d+\.\d+)\.(?:jpg|jpeg|png)$", re.IGNORECASE)

# Per-robot filename prefixes used by the Webots controllers.
# Each role lists the prefixes that mark an image as belonging to that role;
# an empty list means "accept any image in that role's directory".
ROBOT_IMAGE_PREFIXES = {
    "single": {"robot": ["pioneer_image_"]},
    "multi": {
        "ground": ["spot_image_"],
        "aerial": ["mavic_image_"],
    },
}

# Default image directories per role (mirrors the Webots controllers).
DEFAULT_IMAGE_DIRS = {
    "single": {"robot": "/tmp/webots_memory"},
    "multi": {
        "ground": "/tmp/webots_memory_ground",
        "aerial": "/tmp/webots_memory_aerial",
    },
}


# ---------------------------------------------------------------------------
# Trajectory-length helpers
# ---------------------------------------------------------------------------

def trajectory_length_prefix(duration_seconds):
    """Return SHORT / MEDIUM / LONG for a trajectory duration in seconds."""
    minutes = duration_seconds / 60.0
    if minutes < 2.0:
        return "SHORT"
    elif minutes <= 7.0:
        return "MEDIUM"
    else:
        return "LONG"


# ---------------------------------------------------------------------------
# Memory-entry loading
# ---------------------------------------------------------------------------

def _normalize_entry(time_val, position, theta, caption, audio_caption,
                     robot_id=None, detection_results=None, robot_data=None):
    return {
        "time": float(time_val),
        "position": list(position) if position is not None else [0.0, 0.0, 0.0],
        "theta": float(theta) if theta is not None else 0.0,
        "caption": caption or "",
        "audio_caption": audio_caption or "",
        "robot_id": robot_id or "",
        "detection_results": detection_results or {},
        "robot_data": robot_data or {},
    }


def _restore_unix_time(t, time_offset):
    """If `t` looks like an offset-subtracted value (clearly below a plausible
    unix timestamp, i.e. < 1e9), add the Milvus offset back so the returned
    value is a real unix timestamp comparable to the timestamps embedded in
    image filenames. For data written by the current (post-fix) schema this
    is a no-op because `t` is already a full unix timestamp.

    ``time_offset`` overrides the legacy default; 0 means "use the legacy
    default when a fallback is needed".
    """
    t = float(t)
    if t < 1_000_000_000:
        return t + (time_offset if time_offset else LEGACY_MILVUS_TIME_OFFSET)
    return t


def load_entries_from_json(json_path, time_offset=0):
    """Load memory entries from an export produced by the inspector scripts."""
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    items = data.get("items", data) if isinstance(data, dict) else data
    entries = []
    for item in items:
        # Handle both the structured export format and a flat format.
        if "content" in item and isinstance(item["content"], dict):
            pos = item.get("position", {})
            if isinstance(pos, dict):
                pos = pos.get("raw", [pos.get("x", 0.0), pos.get("y", 0.0), pos.get("z", 0.0)])
            theta = item.get("orientation", {}).get("theta_radians", 0.0)
            entries.append(_normalize_entry(
                time_val=_restore_unix_time(item.get("timestamp", 0.0), time_offset),
                position=pos,
                theta=theta,
                caption=item["content"].get("visual_caption", ""),
                audio_caption=item["content"].get("audio_caption", ""),
                robot_id=item.get("robot_id"),
                detection_results=item.get("detection_results"),
                robot_data=item.get("robot_data"),
            ))
        else:
            t = item.get("time", item.get("timestamp", 0.0))
            if isinstance(t, list):
                t = t[0] if t else 0.0
            rd = item.get("robot_data")
            if isinstance(rd, str):
                try:
                    rd = json.loads(rd)
                except Exception:
                    rd = {}
            entries.append(_normalize_entry(
                time_val=_restore_unix_time(t, time_offset),
                position=item.get("position", [0.0, 0.0, 0.0]),
                theta=item.get("theta", 0.0),
                caption=item.get("caption", ""),
                audio_caption=item.get("audio_caption", ""),
                robot_id=item.get("robot_id"),
                detection_results=item.get("detection_results"),
                robot_data=rd,
            ))

    entries.sort(key=lambda e: e["time"])
    return entries


def load_entries_from_milvus(collection_name, db_ip, db_port, mode,
                             time_offset=0):
    """Load memory entries directly from a Milvus collection."""
    from pymilvus import connections, Collection, utility

    connections.connect(host=db_ip, port=db_port)
    if not utility.has_collection(collection_name):
        raise ValueError(f"Collection '{collection_name}' not found")

    col = Collection(collection_name)
    col.load()

    if mode == "multi":
        output_fields = ["caption", "audio_caption", "detection_results",
                         "time", "position", "theta", "robot_id", "robot_data"]
    else:
        output_fields = ["caption", "audio_caption", "time", "position", "theta"]

    # "time >= 0" matches every row: `time` is a positive unix timestamp
    # (and Milvus .query() requires a non-empty filter expression).
    results = col.query(expr="time >= 0", output_fields=output_fields, limit=16384)

    entries = []
    for r in results:
        t = r.get("time", 0.0)
        if isinstance(t, list):
            t = t[0] if t else 0.0
        det = r.get("detection_results")
        if isinstance(det, str) and det:
            try:
                det = json.loads(det)
            except Exception:
                det = {}
        rd = r.get("robot_data")
        if isinstance(rd, str) and rd:
            try:
                rd = json.loads(rd)
            except Exception:
                rd = {}
        entries.append(_normalize_entry(
            time_val=_restore_unix_time(t, time_offset),
            position=r.get("position", [0.0, 0.0, 0.0]),
            theta=r.get("theta", 0.0),
            caption=r.get("caption", ""),
            audio_caption=r.get("audio_caption", ""),
            robot_id=r.get("robot_id"),
            detection_results=det,
            robot_data=rd,
        ))

    entries.sort(key=lambda e: e["time"])
    return entries


# ---------------------------------------------------------------------------
# Image lookup
# ---------------------------------------------------------------------------

class ImageIndex:
    """Indexes images (one directory per robot role) by the timestamp embedded
    in each filename, e.g. ``spot_image_000012_1721761234.567.jpg``.

    Args:
        role_dirs: mapping ``{role: directory}``. In single-robot mode this is
            ``{"robot": <dir>}``; in multi-robot mode it is
            ``{"ground": <dir>, "aerial": <dir>}``.
        mode: ``"single"`` or ``"multi"`` — selects which filename prefixes are
            accepted for each role.
        max_delta: maximum allowed |entry_time − image_time| in seconds for an
            image to be considered a match.
    """

    def __init__(self, role_dirs, mode, max_delta=5.0):
        self.mode = mode
        self.max_delta = float(max_delta)
        self.index = {}  # role -> sorted list of (timestamp, path)
        prefixes = ROBOT_IMAGE_PREFIXES[mode]

        for role, role_prefixes in prefixes.items():
            matched = []
            image_dir = role_dirs.get(role)
            if image_dir and os.path.isdir(image_dir):
                all_files = []
                for ext in ("*.jpg", "*.jpeg", "*.png"):
                    all_files.extend(glob.glob(os.path.join(image_dir, ext)))
                for fp in all_files:
                    name = os.path.basename(fp)
                    if role_prefixes and not any(name.startswith(p)
                                                 for p in role_prefixes):
                        continue
                    m = IMAGE_TS_RE.search(name)
                    if m:
                        matched.append((float(m.group(1)), fp))
                matched.sort(key=lambda x: x[0])
            self.index[role] = matched

    def find_closest(self, role, timestamp, max_delta=None):
        """Return the image path whose embedded timestamp is closest to
        ``timestamp``. ``max_delta`` overrides the instance default if given."""
        if max_delta is None:
            max_delta = self.max_delta
        candidates = self.index.get(role, [])
        if not candidates:
            return None
        best = min(candidates, key=lambda c: abs(c[0] - timestamp))
        if abs(best[0] - timestamp) <= max_delta:
            return best[1]
        return None

    def images_for_entry(self, entry):
        """Return ``{role: image_path}`` for a memory entry."""
        out = {}
        for role in self.index:
            path = self.find_closest(role, entry["time"])
            if path:
                out[role] = path
        return out


# ---------------------------------------------------------------------------
# Tkinter GUI
# ---------------------------------------------------------------------------

class QAGeneratorApp:
    IMAGE_MAX_SIZE = (480, 360)

    def __init__(self, root, entries, image_index, mode, seq_id, output_csv,
                 traj_prefix):
        self.root = root
        self.entries = entries
        self.image_index = image_index
        self.mode = mode
        self.seq_id = seq_id
        self.output_csv = output_csv
        self.traj_prefix = traj_prefix

        self.idx = 0
        self.qa_rows = []          # all collected rows (list of lists)
        self._photo_refs = []      # keep PhotoImage refs alive

        self.root.title(f"ReMEmbR QA Generator — {mode}-robot — {traj_prefix}")
        self.root.protocol("WM_DELETE_WINDOW", self._on_finish)

        self._build_ui()
        self._show_entry()

    # -- UI construction -------------------------------------------------

    def _build_ui(self):
        main = ttk.Frame(self.root, padding=8)
        main.pack(fill="both", expand=True)

        # Top: progress + nav buttons
        top = ttk.Frame(main)
        top.pack(fill="x")
        self.progress_var = tk.StringVar()
        ttk.Label(top, textvariable=self.progress_var,
                  font=("TkDefaultFont", 10, "bold")).pack(side="left")
        ttk.Button(top, text="Finish & Export CSV",
                   command=self._on_finish).pack(side="right")
        ttk.Button(top, text="Next ▶", command=self._on_next).pack(side="right", padx=4)
        ttk.Button(top, text="◀ Prev", command=self._on_prev).pack(side="right")

        # Middle: images (left) + memory entry (right)
        mid = ttk.Frame(main)
        mid.pack(fill="both", expand=True, pady=6)

        self.image_frame = ttk.LabelFrame(mid, text="Robot image(s)", padding=4)
        self.image_frame.pack(side="left", fill="both", expand=True)

        info_frame = ttk.LabelFrame(mid, text="Memory entry", padding=4)
        info_frame.pack(side="left", fill="both", expand=True, padx=(6, 0))
        self.info_text = tk.Text(info_frame, width=55, height=20, wrap="word")
        self.info_text.pack(fill="both", expand=True)
        self.info_text.configure(state="disabled")

        # Bottom: QA input form
        form = ttk.LabelFrame(main, text="Add question / answer for this timestamp",
                              padding=6)
        form.pack(fill="x", pady=4)

        row = 0
        ttk.Label(form, text="Question:").grid(row=row, column=0, sticky="ne")
        self.q_text = tk.Text(form, width=70, height=2, wrap="word")
        self.q_text.grid(row=row, column=1, columnspan=3, sticky="we", padx=4, pady=2)

        row += 1
        ttk.Label(form, text="Type:").grid(row=row, column=0, sticky="e")
        self.type_var = tk.StringVar(value=QUESTION_TYPES[0])
        ttk.Combobox(form, textvariable=self.type_var, values=QUESTION_TYPES,
                     state="readonly", width=14).grid(row=row, column=1,
                                                      sticky="w", padx=4)

        ttk.Label(form, text="Question Category:").grid(row=row, column=2, sticky="e")
        self.cat_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.cat_var, width=24).grid(row=row, column=3,
                                                                  sticky="w", padx=4)

        row += 1
        ttk.Label(form, text="Text answer:").grid(row=row, column=0, sticky="e")
        self.text_ans_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.text_ans_var, width=50).grid(
            row=row, column=1, columnspan=3, sticky="we", padx=4, pady=2)

        row += 1
        ttk.Label(form, text="Parsable answer:").grid(row=row, column=0, sticky="e")
        self.pars_ans_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.pars_ans_var, width=50).grid(
            row=row, column=1, columnspan=3, sticky="we", padx=4, pady=2)

        row += 1
        ttk.Label(form, text="Timestamp with answer:").grid(row=row, column=0, sticky="e")
        self.ts_ans_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.ts_ans_var, width=24).grid(
            row=row, column=1, sticky="w", padx=4)
        ttk.Label(form, text="(auto-filled from entry; edit if needed)",
                  foreground="gray").grid(row=row, column=2, columnspan=2, sticky="w")

        row += 1
        btns = ttk.Frame(form)
        btns.grid(row=row, column=0, columnspan=4, pady=(6, 0))
        ttk.Button(btns, text="Add QA pair",
                   command=self._on_add_qa).pack(side="left", padx=4)
        ttk.Button(btns, text="Add QA pair & Next ▶",
                   command=lambda: (self._on_add_qa(), self._on_next())
                   ).pack(side="left", padx=4)
        ttk.Button(btns, text="Clear form",
                   command=self._clear_form).pack(side="left", padx=4)

        form.columnconfigure(1, weight=1)
        form.columnconfigure(3, weight=1)

        # Recorded QA list for current session
        rec = ttk.LabelFrame(main, text="Recorded QA pairs (this session)", padding=4)
        rec.pack(fill="both", expand=False, pady=4)
        self.rec_list = tk.Listbox(rec, height=6)
        self.rec_list.pack(fill="both", expand=True)

    # -- Entry display ---------------------------------------------------

    def _show_entry(self):
        if not self.entries:
            messagebox.showerror("No data", "No memory entries loaded.")
            self.root.destroy()
            return

        self.idx = max(0, min(self.idx, len(self.entries) - 1))
        entry = self.entries[self.idx]

        self.progress_var.set(
            f"Entry {self.idx + 1} / {len(self.entries)}   "
            f"| trajectory: {self.traj_prefix}   "
            f"| QA pairs so far: {len(self.qa_rows)}"
        )

        # Images
        for w in self.image_frame.winfo_children():
            w.destroy()
        self._photo_refs.clear()

        images = self.image_index.images_for_entry(entry)
        if not images:
            ttk.Label(self.image_frame,
                      text="(no matching image found in image directory)",
                      foreground="gray").pack(padx=10, pady=10)
        else:
            for role, path in images.items():
                sub = ttk.Frame(self.image_frame)
                sub.pack(side="left", padx=4, pady=4)
                ttk.Label(sub, text=f"{role}: {os.path.basename(path)}",
                          font=("TkDefaultFont", 8)).pack()
                if PIL_AVAILABLE:
                    try:
                        img = Image.open(path)
                        img.thumbnail(self.IMAGE_MAX_SIZE)
                        photo = ImageTk.PhotoImage(img)
                        self._photo_refs.append(photo)
                        tk.Label(sub, image=photo).pack()
                    except Exception as e:
                        ttk.Label(sub, text=f"(failed to load: {e})",
                                  foreground="red").pack()
                else:
                    ttk.Label(sub, text="(Pillow not installed — cannot render)",
                              foreground="gray").pack()

        # Memory-entry text
        self.info_text.configure(state="normal")
        self.info_text.delete("1.0", "end")
        self.info_text.insert("end", self._format_entry(entry))
        self.info_text.configure(state="disabled")

        # Pre-fill the answer timestamp with this entry's timestamp
        self.ts_ans_var.set(self._format_timestamp(entry["time"]))

    def _format_timestamp(self, t):
        if t > 1_000_000_000:  # looks like a unix timestamp
            try:
                return datetime.fromtimestamp(t).strftime("%H:%M:%S")
            except Exception:
                pass
        return f"{t:.3f}"

    def _format_entry(self, entry):
        lines = [
            f"Time:           {entry['time']:.3f}  ({self._format_timestamp(entry['time'])})",
            f"Position:       {entry['position']}",
            f"Theta:          {entry['theta']:.4f} rad",
        ]
        if entry["robot_id"]:
            lines.append(f"Robot ID(s):    {entry['robot_id']}")
        lines.append("")
        lines.append("Visual caption:")
        lines.append(f"  {entry['caption'] or '(none)'}")
        lines.append("")
        lines.append("Audio caption:")
        lines.append(f"  {entry['audio_caption'] or '(none)'}")
        if entry["detection_results"]:
            lines.append("")
            lines.append("Detection results:")
            lines.append("  " + json.dumps(entry["detection_results"], indent=2)
                         .replace("\n", "\n  "))
        if entry["robot_data"]:
            lines.append("")
            lines.append("Per-robot data:")
            lines.append("  " + json.dumps(entry["robot_data"], indent=2)
                         .replace("\n", "\n  "))
        return "\n".join(lines)

    # -- Actions ---------------------------------------------------------

    def _clear_form(self, keep_ts=True):
        self.q_text.delete("1.0", "end")
        self.type_var.set(QUESTION_TYPES[0])
        self.cat_var.set("")
        self.text_ans_var.set("")
        self.pars_ans_var.set("")
        if not keep_ts:
            self.ts_ans_var.set("")

    def _on_add_qa(self):
        question = self.q_text.get("1.0", "end").strip()
        if not question:
            messagebox.showwarning("Missing question", "Please enter a question.")
            return False

        qa_uuid = f"{self.traj_prefix}_{uuid.uuid4()}"
        row = [
            qa_uuid,
            self.seq_id,
            question,
            self.ts_ans_var.get().strip(),
            self.type_var.get().strip(),
            self.text_ans_var.get().strip(),
            self.pars_ans_var.get().strip(),
            self.cat_var.get().strip(),
        ]
        self.qa_rows.append(row)
        self.rec_list.insert("end",
                             f"[{qa_uuid[:18]}…] {row[4]:<8} | {question[:60]}")
        self.rec_list.see("end")
        self.progress_var.set(
            f"Entry {self.idx + 1} / {len(self.entries)}   "
            f"| trajectory: {self.traj_prefix}   "
            f"| QA pairs so far: {len(self.qa_rows)}"
        )
        self._clear_form(keep_ts=True)
        return True

    def _on_next(self):
        if self.idx < len(self.entries) - 1:
            self.idx += 1
            self._show_entry()
        else:
            if messagebox.askyesno("End of trajectory",
                                   "This was the last entry. Finish and export CSV?"):
                self._on_finish()

    def _on_prev(self):
        if self.idx > 0:
            self.idx -= 1
            self._show_entry()

    def _on_finish(self):
        if not self.qa_rows:
            if not messagebox.askyesno("No QA pairs",
                                       "No QA pairs recorded. Exit without saving?"):
                return
            self.root.destroy()
            return

        out = self.output_csv
        if not out:
            out = filedialog.asksaveasfilename(
                title="Save QA CSV",
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv")],
                initialfile=f"qa_{self.traj_prefix.lower()}_"
                            f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            )
            if not out:
                return

        try:
            write_qa_csv(out, self.qa_rows)
            messagebox.showinfo("Saved",
                                f"Wrote {len(self.qa_rows)} QA pairs to:\n{out}")
        except Exception as e:
            messagebox.showerror("Save failed", str(e))
            return
        self.root.destroy()


# ---------------------------------------------------------------------------
# CSV output
# ---------------------------------------------------------------------------

def write_qa_csv(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(CSV_HEADER)
        writer.writerows(rows)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def build_argparser():
    p = argparse.ArgumentParser(
        description="Interactive QA-pair generation for ReMEmbR trajectories")

    p.add_argument("--mode", choices=["single", "multi"], default="single",
                   help="single-robot (pioneer3at) or multi-robot (spot + mavic)")

    p.add_argument("--source", choices=["milvus", "json"], default="milvus",
                   help="Load memory entries from Milvus or from an exported JSON file")
    p.add_argument("--json-file", help="Path to exported JSON (required if --source json)")

    p.add_argument("--collection", "-c", default=None,
                   help="Milvus collection name "
                        "(default: webots_simulation for single, webots_multirobot for multi)")
    p.add_argument("--db-ip", default="127.0.0.1")
    p.add_argument("--db-port", type=int, default=19530)

    p.add_argument("--image-dir",
                   default=DEFAULT_IMAGE_DIRS["single"]["robot"],
                   help="[single mode] directory containing pioneer_image_* files")
    p.add_argument("--ground-image-dir",
                   default=DEFAULT_IMAGE_DIRS["multi"]["ground"],
                   help="[multi mode] directory containing spot_image_* files")
    p.add_argument("--aerial-image-dir",
                   default=DEFAULT_IMAGE_DIRS["multi"]["aerial"],
                   help="[multi mode] directory containing mavic_image_* files")
    p.add_argument("--image-max-delta", type=float, default=5.0,
                   help="Max |entry_time - image_time| (seconds) allowed when "
                        "matching an image to a memory entry")
    p.add_argument("--time-offset", type=float, default=0,
                   help="Legacy offset to add back to timestamps that look "
                        "offset-subtracted (i.e. < 1e9). Only needed for data "
                        f"written by the pre-fix schema; set to "
                        f"{LEGACY_MILVUS_TIME_OFFSET} when loading old JSON "
                        "exports.")

    p.add_argument("--seq-id", default="0",
                   help="Seq ID written to every row of the output CSV")
    p.add_argument("--output", "-o", default=None,
                   help="Output CSV path (if omitted, a save dialog is shown on finish)")
    return p


def main():
    args = build_argparser().parse_args()

    if args.collection is None:
        args.collection = ("webots_multirobot" if args.mode == "multi"
                           else "webots_simulation")

    # Load entries
    if args.source == "json":
        if not args.json_file:
            print("--json-file is required when --source json", file=sys.stderr)
            sys.exit(1)
        entries = load_entries_from_json(args.json_file,
                                         time_offset=args.time_offset)
    else:
        entries = load_entries_from_milvus(args.collection, args.db_ip,
                                           args.db_port, args.mode,
                                           time_offset=args.time_offset)

    if not entries:
        print("No memory entries found.", file=sys.stderr)
        sys.exit(1)

    duration = entries[-1]["time"] - entries[0]["time"]
    traj_prefix = trajectory_length_prefix(duration)
    print(f"[QA Generator] Loaded {len(entries)} entries, "
          f"trajectory duration {duration:.1f}s → {traj_prefix}")

    if args.mode == "multi":
        role_dirs = {"ground": args.ground_image_dir,
                     "aerial": args.aerial_image_dir}
    else:
        role_dirs = {"robot": args.image_dir}

    image_index = ImageIndex(role_dirs, args.mode,
                             max_delta=args.image_max_delta)
    for role, items in image_index.index.items():
        print(f"[QA Generator] Indexed {len(items)} '{role}' images "
              f"from {role_dirs.get(role)} (max_delta={args.image_max_delta}s)")

    root = tk.Tk()
    QAGeneratorApp(root, entries, image_index, args.mode, args.seq_id,
                   args.output, traj_prefix)
    root.mainloop()


if __name__ == "__main__":
    main()
