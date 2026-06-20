#!/usr/bin/env python3
"""QA evaluation framework for ReMEmbR-style CSV question sets.

The framework reads a CSV with the same columns as the QA generation flow,
feeds each question into a model backend, and scores the model output with
type-specific metrics:

* Spatial questions: L2 distance between predicted and target coordinates.
  Correct if the distance is at most 15 meters.
* Temporal questions: L1 temporal error in minutes.
  Correct if the absolute error is at most 2 minutes.
* Descriptive questions: binary or free-form text answers.
  Binary items use exact yes/no accuracy. Free-form text items use an LLM
  judge when available, with a deterministic fallback.

The script is designed to be usable both as a CLI tool and as a lightweight
benchmarking framework for local experimentation.
"""

from __future__ import annotations

import argparse
import csv
import dataclasses
import difflib
import json
import math
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence


SPATIAL_THRESHOLD_METERS = 15.0
TEMPORAL_THRESHOLD_MINUTES = 2.0


@dataclass
class QARow:
    uuid: str
    seq_id: str
    question: str
    timestamp_with_answer: str
    raw_type: str
    text_answer: str
    parsable_answer: str
    question_category: str

    @classmethod
    def from_dict(cls, row: Dict[str, str]) -> "QARow":
        return cls(
            uuid=(row.get("UUID") or "").strip(),
            seq_id=(row.get("Seq ID") or "").strip(),
            question=(row.get("Question") or "").strip(),
            timestamp_with_answer=(row.get("Timestamp with answer") or "").strip(),
            raw_type=(row.get("Type") or "").strip().lower(),
            text_answer=(row.get("Text answer") or "").strip(),
            parsable_answer=(row.get("Parsable answer") or "").strip(),
            question_category=(row.get("Question Category") or "").strip().lower(),
        )


@dataclass
class ModelAnswer:
    raw_text: str
    text: str = ""
    binary: str = ""
    position: Optional[List[float]] = None
    time_minutes: Optional[float] = None
    duration_minutes: Optional[float] = None
    parsed: Optional[Dict[str, Any]] = None


@dataclass
class JudgeResult:
    correct: bool
    reasoning: str


class AnswerBackend:
    def answer(self, row: QARow, family: str) -> ModelAnswer:
        raise NotImplementedError


class MockAnswerBackend(AnswerBackend):
    """Deterministic fallback that mirrors available gold fields.

    This is useful for smoke tests and for validating the scoring pipeline on
    CSVs whose gold labels are already present in the row.
    """

    def answer(self, row: QARow, family: str) -> ModelAnswer:
        if family == "spatial":
            position = parse_coordinate_target(row.parsable_answer or row.text_answer)
            return ModelAnswer(raw_text=json.dumps({"position": position}), position=position, parsed={"position": position})

        if family == "temporal":
            value = parse_minutes_target(row.parsable_answer or row.text_answer)
            payload_key = "duration_minutes" if row.raw_type == "duration" else "time_minutes"
            parsed = {payload_key: value} if value is not None else {}
            return ModelAnswer(raw_text=json.dumps(parsed), time_minutes=value if row.raw_type == "time" else None, duration_minutes=value if row.raw_type == "duration" else None, parsed=parsed)

        binary = normalize_yes_no(row.parsable_answer or row.text_answer)
        if binary:
            parsed = {"binary": binary}
            return ModelAnswer(raw_text=json.dumps(parsed), binary=binary, text=binary, parsed=parsed)

        text = row.text_answer or row.parsable_answer
        parsed = {"text": text} if text else {}
        return ModelAnswer(raw_text=json.dumps(parsed), text=text, parsed=parsed)


class MlxAnswerBackend(AnswerBackend):
    def __init__(self, model_backend: str = "COMMAND_R"):
        self.model_backend = model_backend.upper()
        self._model = None
        self._tokenizer = None

    def _load_model(self) -> None:
        if self._model is not None and self._tokenizer is not None:
            return

        try:
            from mlx_lm import load  # type: ignore
        except Exception as exc:  # pragma: no cover - depends on local environment
            raise RuntimeError(
                "mlx_lm is not available. Install the MLX runtime or use --answer-backend mock."
            ) from exc

        if self.model_backend == "COMMAND_R":
            model_name = "mlx-community/c4ai-command-r-v01-4bit"
        elif self.model_backend == "GEMMA":
            model_name = "mlx-community/gemma-3n-E2B-it-lm-4bit"
        else:
            raise ValueError(f"Unsupported model backend: {self.model_backend}")

        self._model, self._tokenizer = load(model_name)

    def answer(self, row: QARow, family: str) -> ModelAnswer:
        self._load_model()

        try:
            from mlx_lm import generate  # type: ignore
        except Exception as exc:  # pragma: no cover - depends on local environment
            raise RuntimeError("mlx_lm generate is unavailable") from exc

        prompt = build_answer_prompt(row, family)
        response_text = generate(self._model, self._tokenizer, prompt=prompt, verbose=False, max_tokens=256)
        parsed = parse_model_json(response_text)

        return canonicalize_model_answer(response_text, parsed, family)


class JudgeBackend:
    def judge(self, question: str, reference: str, candidate: str) -> JudgeResult:
        raise NotImplementedError


class HeuristicJudgeBackend(JudgeBackend):
    def judge(self, question: str, reference: str, candidate: str) -> JudgeResult:
        ref_norm = normalize_text(reference)
        cand_norm = normalize_text(candidate)

        if not ref_norm and not cand_norm:
            return JudgeResult(correct=False, reasoning="Both reference and candidate are empty.")

        if ref_norm == cand_norm:
            return JudgeResult(correct=True, reasoning="Normalized answers match exactly.")

        similarity = difflib.SequenceMatcher(None, ref_norm, cand_norm).ratio()
        correct = similarity >= 0.78
        return JudgeResult(
            correct=correct,
            reasoning=f"Heuristic similarity score {similarity:.2f} against threshold 0.78.",
        )


class OpenAIJudgeBackend(JudgeBackend):
    def __init__(self, model: str = "gpt-4o"):
        self.model = model
        self.api_key = os.environ.get("OPENAI_API_KEY", "").strip()
        self.api_base = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")

    def judge(self, question: str, reference: str, candidate: str) -> JudgeResult:
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY is not set")

        prompt = (
            "You are a strict QA judge. Decide whether the candidate answer is "
            "semantically equivalent to the reference answer for the question. "
            "Return only JSON with keys correct (boolean) and reasoning (string).\n\n"
            f"Question: {question}\n"
            f"Reference answer: {reference}\n"
            f"Candidate answer: {candidate}\n"
        )

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You judge QA answer equivalence."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.0,
        }

        request = urllib.request.Request(
            f"{self.api_base}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                data = json.load(response)
        except urllib.error.URLError as exc:
            raise RuntimeError(f"OpenAI judge request failed: {exc}") from exc

        content = data["choices"][0]["message"]["content"]
        parsed = parse_model_json(content)
        correct = bool(parsed.get("correct", False))
        reasoning = str(parsed.get("reasoning", ""))
        return JudgeResult(correct=correct, reasoning=reasoning or "OpenAI judge returned a decision.")


def build_answer_prompt(row: QARow, family: str) -> str:
    if family == "spatial":
        format_hint = '{"position": [x, y, z], "text": "short answer"}'
    elif family == "temporal":
        key = "duration_minutes" if row.raw_type == "duration" else "time_minutes"
        format_hint = f'{{"{key}": 12.5, "text": "short answer"}}'
    else:
        format_hint = '{"binary": "yes|no", "text": "short answer"}'

    return (
        "You are answering a QA benchmark item. Reply with a single JSON object only. "
        "Do not include markdown.\n\n"
        f"Question family: {family}\n"
        f"Question type: {row.raw_type or 'unknown'}\n"
        f"Question: {row.question}\n\n"
        "Return this shape when possible:\n"
        f"{format_hint}\n\n"
        "Rules:\n"
        "- Spatial answers must be 3D coordinates if you know them.\n"
        "- Temporal answers must be expressed in minutes as a number.\n"
        "- Descriptive answers must be either yes/no or a concise text answer.\n"
    )


def parse_model_json(response_text: str) -> Dict[str, Any]:
    candidate = extract_json_block(response_text)
    if candidate is None:
        return {}
    try:
        parsed = json.loads(candidate)
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        return {}


def extract_json_block(text: str) -> Optional[str]:
    text = (text or "").strip()
    if not text:
        return None

    if text.startswith("{") and text.endswith("}"):
        return text

    fence = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.IGNORECASE | re.DOTALL)
    if fence:
        return fence.group(1).strip()

    start = text.find("{")
    end = text.rfind("}")
    if 0 <= start < end:
        return text[start : end + 1]

    return None


def canonicalize_model_answer(raw_text: str, parsed: Dict[str, Any], family: str) -> ModelAnswer:
    text = str(parsed.get("text", "")).strip()

    position = parsed.get("position")
    if isinstance(position, str):
        position = parse_coordinate_target(position)
    elif isinstance(position, list):
        coords = [float(v) for v in position if is_number(v)]
        position = coords if len(coords) >= 2 else None
    else:
        position = None

    time_minutes = first_number(parsed.get("time_minutes"))
    duration_minutes = first_number(parsed.get("duration_minutes"))
    binary = normalize_yes_no(str(parsed.get("binary", "")))

    if not text:
        if family == "spatial" and position is not None:
            text = json.dumps({"position": position})
        elif family == "temporal" and (time_minutes is not None or duration_minutes is not None):
            value = time_minutes if time_minutes is not None else duration_minutes
            text = json.dumps({"minutes": value})
        elif binary:
            text = binary

    return ModelAnswer(
        raw_text=raw_text,
        text=text,
        binary=binary,
        position=position,
        time_minutes=time_minutes,
        duration_minutes=duration_minutes,
        parsed=parsed,
    )


def normalize_text(value: str) -> str:
    value = (value or "").strip().lower()
    value = re.sub(r"[^a-z0-9\s]+", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def normalize_yes_no(value: str) -> str:
    text = normalize_text(value)
    if not text:
        return ""
    if text in {"yes", "y", "true", "correct", "affirmative"}:
        return "yes"
    if text in {"no", "n", "false", "incorrect", "negative"}:
        return "no"
    if text.split()[0] == "yes":
        return "yes"
    if text.split()[0] == "no":
        return "no"
    return ""


def is_number(value: Any) -> bool:
    try:
        float(value)
        return True
    except Exception:
        return False


def first_number(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        match = re.search(r"-?\d+(?:\.\d+)?", value)
        if match:
            return float(match.group(0))
    return None


def parse_minutes_target(value: str) -> Optional[float]:
    if not value:
        return None
    return first_number(value)


def parse_coordinate_target(value: str) -> Optional[List[float]]:
    if not value:
        return None

    stripped = value.strip()
    lowered = stripped.lower()
    if lowered in {"[position]", "position", "unknown", "n/a", "na", "none", "null"}:
        return None

    if stripped.startswith("[") or stripped.startswith("("):
        try:
            parsed = json.loads(stripped.replace("(", "[").replace(")", "]"))
            if isinstance(parsed, list):
                coords = [float(v) for v in parsed if is_number(v)]
                return coords if len(coords) >= 2 else None
        except Exception:
            pass

    numbers = re.findall(r"-?\d+(?:\.\d+)?", stripped)
    if len(numbers) >= 2:
        return [float(n) for n in numbers[:3]]
    return None


def parse_temporal_gold(row: QARow) -> Optional[float]:
    candidates = [row.parsable_answer, row.text_answer]
    for candidate in candidates:
        minutes = parse_minutes_target(candidate)
        if minutes is not None:
            return minutes
    return None


def parse_descriptive_gold(row: QARow) -> Optional[str]:
    binary = normalize_yes_no(row.parsable_answer)
    if binary:
        return binary
    text = row.text_answer.strip()
    return text or None


def detect_family(row: QARow) -> str:
    category = row.question_category
    raw_type = row.raw_type

    if "spatial" in category or raw_type == "position":
        return "spatial"
    if "temporal" in category or raw_type in {"time", "duration"}:
        return "temporal"
    if "descriptive" in category or raw_type in {"binary", "text"}:
        return "descriptive"
    return "descriptive"


def evaluate_spatial(gold: Optional[List[float]], pred: Optional[List[float]]) -> Dict[str, Any]:
    if gold is None or pred is None or len(gold) < 2 or len(pred) < 2:
        return {"scored": False, "reason": "Missing spatial gold or prediction."}

    gold_vec = list(gold[:3])
    pred_vec = list(pred[:3])
    while len(gold_vec) < 3:
        gold_vec.append(0.0)
    while len(pred_vec) < 3:
        pred_vec.append(0.0)

    distance = math.sqrt(sum((a - b) ** 2 for a, b in zip(gold_vec, pred_vec)))
    correct = distance <= SPATIAL_THRESHOLD_METERS
    return {
        "scored": True,
        "metric": "l2_distance",
        "distance": distance,
        "correct": correct,
        "threshold_meters": SPATIAL_THRESHOLD_METERS,
    }


def evaluate_temporal(gold: Optional[float], pred: Optional[float]) -> Dict[str, Any]:
    if gold is None or pred is None:
        return {"scored": False, "reason": "Missing temporal gold or prediction."}

    error = abs(gold - pred)
    correct = error <= TEMPORAL_THRESHOLD_MINUTES
    return {
        "scored": True,
        "metric": "l1_temporal_error_minutes",
        "error_minutes": error,
        "correct": correct,
        "threshold_minutes": TEMPORAL_THRESHOLD_MINUTES,
    }


def evaluate_descriptive(
    question: str,
    gold: Optional[str],
    pred: ModelAnswer,
    judge_backend: JudgeBackend,
) -> Dict[str, Any]:
    if gold is None:
        return {"scored": False, "reason": "Missing descriptive gold answer."}

    gold_binary = normalize_yes_no(gold)
    pred_binary = pred.binary or normalize_yes_no(pred.text)

    if gold_binary and pred_binary:
        correct = gold_binary == pred_binary
        return {
            "scored": True,
            "metric": "binary_accuracy",
            "correct": correct,
            "gold_binary": gold_binary,
            "pred_binary": pred_binary,
        }

    judge_result = judge_backend.judge(question, gold, pred.text or pred.raw_text)
    return {
        "scored": True,
        "metric": "llm_judged_text_accuracy",
        "correct": judge_result.correct,
        "judge_reasoning": judge_result.reasoning,
        "gold_text": gold,
        "pred_text": pred.text or pred.raw_text,
    }


def choose_answer_backend(name: str) -> AnswerBackend:
    backend = name.upper()
    if backend == "MOCK":
        return MockAnswerBackend()
    if backend in {"COMMAND_R", "GEMMA"}:
        return MlxAnswerBackend(backend)
    raise ValueError(f"Unsupported answer backend: {name}")


def choose_judge_backend(name: str) -> JudgeBackend:
    backend = name.lower()
    if backend == "heuristic":
        return HeuristicJudgeBackend()
    if backend == "openai":
        return OpenAIJudgeBackend()
    if backend == "auto":
        if os.environ.get("OPENAI_API_KEY", "").strip():
            return OpenAIJudgeBackend()
        return HeuristicJudgeBackend()
    raise ValueError(f"Unsupported judge backend: {name}")


def load_rows(csv_path: Path) -> List[QARow]:
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return [QARow.from_dict(row) for row in reader]


def evaluate_rows(
    rows: List[QARow],
    answer_backend: AnswerBackend,
    judge_backend: JudgeBackend,
) -> Dict[str, Any]:
    results: List[Dict[str, Any]] = []
    totals = {
        "total_rows": len(rows),
        "scored_rows": 0,
        "correct_rows": 0,
        "skipped_rows": 0,
        "per_family": {
            "spatial": {"total": 0, "scored": 0, "correct": 0, "distances": []},
            "temporal": {"total": 0, "scored": 0, "correct": 0, "errors": []},
            "descriptive": {"total": 0, "scored": 0, "correct": 0},
        },
    }

    for row in rows:
        family = detect_family(row)
        totals["per_family"][family]["total"] += 1

        model_answer = answer_backend.answer(row, family)
        if family == "spatial":
            gold = parse_coordinate_target(row.parsable_answer or row.text_answer)
            evaluation = evaluate_spatial(gold, model_answer.position)
        elif family == "temporal":
            gold = parse_temporal_gold(row)
            prediction = model_answer.time_minutes if row.raw_type == "time" else model_answer.duration_minutes
            if prediction is None:
                prediction = first_number(model_answer.text)
            evaluation = evaluate_temporal(gold, prediction)
        else:
            gold = parse_descriptive_gold(row)
            evaluation = evaluate_descriptive(row.question, gold, model_answer, judge_backend)

        row_result = {
            "uuid": row.uuid,
            "seq_id": row.seq_id,
            "question": row.question,
            "family": family,
            "raw_type": row.raw_type,
            "question_category": row.question_category,
            "gold": gold,
            "prediction": dataclasses.asdict(model_answer),
            "evaluation": evaluation,
        }
        results.append(row_result)

        if evaluation.get("scored"):
            totals["scored_rows"] += 1
            totals["per_family"][family]["scored"] += 1
            if evaluation.get("correct"):
                totals["correct_rows"] += 1
                totals["per_family"][family]["correct"] += 1

            if family == "spatial" and evaluation.get("distance") is not None:
                totals["per_family"][family]["distances"].append(float(evaluation["distance"]))
            if family == "temporal" and evaluation.get("error_minutes") is not None:
                totals["per_family"][family]["errors"].append(float(evaluation["error_minutes"]))
        else:
            totals["skipped_rows"] += 1

    return {
        "results": results,
        "summary": build_summary(totals),
    }


def build_summary(totals: Dict[str, Any]) -> Dict[str, Any]:
    total_rows = totals["total_rows"] or 1
    scored_rows = totals["scored_rows"]
    correct_rows = totals["correct_rows"]

    spatial = totals["per_family"]["spatial"]
    temporal = totals["per_family"]["temporal"]
    descriptive = totals["per_family"]["descriptive"]

    def accuracy(section: Dict[str, Any]) -> Optional[float]:
        return (section["correct"] / section["scored"]) if section["scored"] else None

    summary = {
        "overall_correctness": (correct_rows / scored_rows) if scored_rows else 0.0,
        "scored_coverage": scored_rows / total_rows,
        "total_rows": totals["total_rows"],
        "scored_rows": scored_rows,
        "correct_rows": correct_rows,
        "skipped_rows": totals["skipped_rows"],
        "by_family": {
            "spatial": {
                "accuracy": accuracy(spatial),
                "mean_l2_distance": mean(spatial["distances"]),
                "count": spatial["total"],
                "scored": spatial["scored"],
            },
            "temporal": {
                "accuracy": accuracy(temporal),
                "mean_l1_error_minutes": mean(temporal["errors"]),
                "count": temporal["total"],
                "scored": temporal["scored"],
            },
            "descriptive": {
                "accuracy": accuracy(descriptive),
                "count": descriptive["total"],
                "scored": descriptive["scored"],
            },
        },
    }
    return summary


def mean(values: Sequence[float]) -> Optional[float]:
    if not values:
        return None
    return sum(values) / len(values)


def write_report(output_path: Path, report: Dict[str, Any]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, default=str)


def print_summary(report: Dict[str, Any]) -> None:
    summary = report["summary"]
    by_family = summary["by_family"]

    print("\nQA Evaluation Summary")
    print("====================")
    print(f"Overall correctness: {summary['overall_correctness']:.3f}")
    print(f"Scored coverage:     {summary['scored_coverage']:.3f}")
    print(f"Rows scored:         {summary['scored_rows']} / {summary['total_rows']}")
    print(f"Rows skipped:        {summary['skipped_rows']}")

    spatial = by_family["spatial"]
    temporal = by_family["temporal"]
    descriptive = by_family["descriptive"]

    print("\nPer-family metrics")
    print(f"Spatial:     acc={format_optional(spatial['accuracy'])} mean_l2={format_optional(spatial['mean_l2_distance'])}")
    print(f"Temporal:    acc={format_optional(temporal['accuracy'])} mean_l1={format_optional(temporal['mean_l1_error_minutes'])}")
    print(f"Descriptive: acc={format_optional(descriptive['accuracy'])}")


def format_optional(value: Optional[float]) -> str:
    if value is None:
        return "n/a"
    return f"{value:.3f}"


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate QA CSV files with model-backed answers.")
    parser.add_argument("--csv-path", required=True, help="Path to the QA CSV file")
    parser.add_argument("--output", default="qa_evaluation_report.json", help="Output JSON report path")
    parser.add_argument(
        "--model-backend",
        default="COMMAND_R",
        choices=["COMMAND_R", "GEMMA", "MOCK"],
        help="Backend used to generate answers",
    )
    parser.add_argument(
        "--judge-backend",
        default="auto",
        choices=["auto", "openai", "heuristic"],
        help="Backend used to judge free-form descriptive answers",
    )
    parser.add_argument("--limit", type=int, default=0, help="Optional row limit for quick smoke tests")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_arg_parser().parse_args(argv)

    csv_path = Path(args.csv_path).expanduser().resolve()
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    rows = load_rows(csv_path)
    if args.limit and args.limit > 0:
        rows = rows[: args.limit]

    answer_backend = choose_answer_backend(args.model_backend)
    judge_backend = choose_judge_backend(args.judge_backend)

    report = evaluate_rows(rows, answer_backend, judge_backend)
    report["metadata"] = {
        "csv_path": str(csv_path),
        "model_backend": args.model_backend,
        "judge_backend": args.judge_backend,
        "row_count": len(rows),
    }

    output_path = Path(args.output).expanduser().resolve()
    write_report(output_path, report)
    print_summary(report)
    print(f"\nReport written to: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())