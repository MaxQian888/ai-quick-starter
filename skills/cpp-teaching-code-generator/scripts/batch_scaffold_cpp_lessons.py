#!/usr/bin/env python3
"""Batch-generate C++ lesson starters from topic lists."""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path

from scaffold_cpp_lesson import (
    LEVEL_CHOICES,
    PATTERN_CHOICES,
    STANDARD_CHOICES,
    create_lesson_file,
    slugify,
)


@dataclass(frozen=True)
class LessonSpec:
    topic: str
    level: str
    pattern: str
    standard: str
    output: str | None = None


def normalize_choice(field: str, value: str, choices: tuple[str, ...], context: str) -> str:
    cleaned = value.strip().lower()
    if cleaned not in choices:
        options = ", ".join(choices)
        raise ValueError(f"{context}: invalid {field} '{value}'. Expected one of: {options}")
    return cleaned


def parse_text_line(raw_line: str, defaults: LessonSpec, context: str) -> LessonSpec | None:
    line = raw_line.strip()
    if not line or line.startswith("#"):
        return None

    if "|" not in line:
        return LessonSpec(
            topic=line,
            level=defaults.level,
            pattern=defaults.pattern,
            standard=defaults.standard,
            output=None,
        )

    parts = [segment.strip() for segment in line.split("|")]
    topic = parts[0]
    if not topic:
        raise ValueError(f"{context}: topic cannot be empty.")
    level = normalize_choice("level", parts[1], LEVEL_CHOICES, context) if len(parts) > 1 and parts[1] else defaults.level
    pattern = (
        normalize_choice("pattern", parts[2], PATTERN_CHOICES, context) if len(parts) > 2 and parts[2] else defaults.pattern
    )
    standard = (
        normalize_choice("standard", parts[3], STANDARD_CHOICES, context)
        if len(parts) > 3 and parts[3]
        else defaults.standard
    )
    output = parts[4] if len(parts) > 4 and parts[4] else None
    return LessonSpec(topic=topic, level=level, pattern=pattern, standard=standard, output=output)


def get_row_value(row: dict[str, str], key: str) -> str:
    for row_key, row_value in row.items():
        if row_key and row_key.strip().lower() == key:
            return (row_value or "").strip()
    return ""


def load_specs_from_csv(path: Path, defaults: LessonSpec) -> list[LessonSpec]:
    specs: list[LessonSpec] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            return specs
        has_topic = any((name or "").strip().lower() == "topic" for name in reader.fieldnames)
        if not has_topic:
            raise ValueError(f"{path}: CSV must include a 'topic' column.")

        for index, row in enumerate(reader, start=2):
            context = f"{path}:{index}"
            topic = get_row_value(row, "topic")
            if not topic:
                continue
            level_text = get_row_value(row, "level")
            pattern_text = get_row_value(row, "pattern")
            standard_text = get_row_value(row, "standard")
            output = get_row_value(row, "output") or get_row_value(row, "filename") or None
            level = normalize_choice("level", level_text, LEVEL_CHOICES, context) if level_text else defaults.level
            pattern = (
                normalize_choice("pattern", pattern_text, PATTERN_CHOICES, context)
                if pattern_text
                else defaults.pattern
            )
            standard = (
                normalize_choice("standard", standard_text, STANDARD_CHOICES, context)
                if standard_text
                else defaults.standard
            )
            specs.append(LessonSpec(topic=topic, level=level, pattern=pattern, standard=standard, output=output))
    return specs


def load_specs_from_text(path: Path, defaults: LessonSpec) -> list[LessonSpec]:
    specs: list[LessonSpec] = []
    for index, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        context = f"{path}:{index}"
        spec = parse_text_line(raw_line, defaults, context)
        if spec:
            specs.append(spec)
    return specs


def load_specs_from_file(path: Path, defaults: LessonSpec) -> list[LessonSpec]:
    if path.suffix.lower() == ".csv":
        return load_specs_from_csv(path, defaults)
    return load_specs_from_text(path, defaults)


def make_default_output_path(
    out_dir: Path,
    index: int,
    topic: str,
    include_index: bool,
    used_paths: set[Path],
) -> Path:
    base = slugify(topic)
    if include_index:
        return out_dir / f"{index:02d}_{base}.cpp"

    candidate = out_dir / f"{base}.cpp"
    suffix = 2
    while candidate in used_paths:
        candidate = out_dir / f"{base}_{suffix}.cpp"
        suffix += 1
    return candidate


def resolve_output_path(
    spec: LessonSpec,
    out_dir: Path,
    index: int,
    include_index: bool,
    used_paths: set[Path],
) -> Path:
    if spec.output:
        provided = Path(spec.output)
        return provided if provided.is_absolute() else (out_dir / provided)
    return make_default_output_path(
        out_dir=out_dir,
        index=index,
        topic=spec.topic,
        include_index=include_index,
        used_paths=used_paths,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Batch-generate C++ lesson starter files from repeated --topic values or a topics file."
    )
    parser.add_argument(
        "--topic",
        action="append",
        default=[],
        help="Topic to generate. Repeat this argument to add multiple topics.",
    )
    parser.add_argument(
        "--topics-file",
        help="Path to .txt/.md (one topic per line) or .csv with at least a topic column.",
    )
    parser.add_argument(
        "--out-dir",
        default="lessons",
        help="Output directory for generated .cpp files. Default: lessons.",
    )
    parser.add_argument(
        "--level",
        choices=LEVEL_CHOICES,
        default="beginner",
        help="Default learner level. Can be overridden per row in input files.",
    )
    parser.add_argument(
        "--pattern",
        choices=PATTERN_CHOICES,
        default="guided-implementation",
        help="Default lesson pattern. Can be overridden per row in input files.",
    )
    parser.add_argument(
        "--standard",
        choices=STANDARD_CHOICES,
        default="c++17",
        help="Default C++ standard. Can be overridden per row in input files.",
    )
    parser.add_argument(
        "--start-index",
        type=int,
        default=1,
        help="Starting index when filename numbering is enabled. Default: 1.",
    )
    parser.add_argument(
        "--no-index",
        action="store_true",
        help="Disable numeric filename prefixes for auto-generated filenames.",
    )
    parser.add_argument("--force", action="store_true", help="Overwrite existing files.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    out_dir = Path(args.out_dir)
    defaults = LessonSpec(
        topic="",
        level=args.level,
        pattern=args.pattern,
        standard=args.standard,
        output=None,
    )

    specs = [
        LessonSpec(
            topic=topic.strip(),
            level=defaults.level,
            pattern=defaults.pattern,
            standard=defaults.standard,
            output=None,
        )
        for topic in args.topic
        if topic.strip()
    ]

    if args.topics_file:
        file_specs = load_specs_from_file(Path(args.topics_file), defaults)
        specs.extend(file_specs)

    if not specs:
        raise SystemExit("No topics provided. Use --topic or --topics-file.")

    out_dir.mkdir(parents=True, exist_ok=True)
    used_paths: set[Path] = set()
    generated: list[Path] = []

    for idx, spec in enumerate(specs, start=args.start_index):
        output_path = resolve_output_path(
            spec=spec,
            out_dir=out_dir,
            index=idx,
            include_index=not args.no_index,
            used_paths=used_paths,
        )
        if output_path in used_paths:
            raise SystemExit(f"Duplicate output path in batch: {output_path}")
        used_paths.add(output_path)
        try:
            create_lesson_file(
                topic=spec.topic,
                level=spec.level,
                pattern=spec.pattern,
                standard=spec.standard,
                output_path=output_path,
                force=args.force,
            )
        except FileExistsError as exc:
            raise SystemExit(str(exc)) from exc
        generated.append(output_path)
        print(
            f"[{len(generated):02d}] {output_path} "
            f"(topic='{spec.topic}', level={spec.level}, pattern={spec.pattern}, std={spec.standard})"
        )

    print(f"Generated {len(generated)} lesson file(s).")


if __name__ == "__main__":
    main()
