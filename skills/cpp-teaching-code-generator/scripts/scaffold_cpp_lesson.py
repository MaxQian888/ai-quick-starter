#!/usr/bin/env python3
"""Generate a compilable C++ lesson starter for classroom use."""

from __future__ import annotations

import argparse
import re
import textwrap
from pathlib import Path

LEVEL_OBJECTIVES = {
    "beginner": [
        "Read and trace a small C++ program confidently",
        "Connect variables, loops, and output behavior",
        "Modify a baseline solution without breaking compilation",
    ],
    "intermediate": [
        "Design helper functions with clear responsibilities",
        "Handle edge cases while keeping code readable",
        "Explain baseline complexity in plain language",
    ],
    "advanced": [
        "Compare design alternatives and trade-offs",
        "Balance readability with performance constraints",
        "Justify abstraction and API choices",
    ],
}

LEVEL_PRACTICE = {
    "beginner": [
        "Replace one hard-coded value with user input and keep behavior correct.",
        "Add input validation for negative numbers.",
        "Write one extra test case in comments and predict output before running.",
    ],
    "intermediate": [
        "Extract repeated logic into a helper function with a clear name.",
        "Handle empty input without crashing or producing misleading output.",
        "Refactor one loop using a standard algorithm while preserving results.",
    ],
    "advanced": [
        "Add a second implementation and compare complexity.",
        "Generalize one function signature without reducing clarity.",
        "Document a performance bottleneck and propose an improvement.",
    ],
}

PATTERN_LABEL = {
    "concept-demo": "Single concept walkthrough",
    "guided-implementation": "Starter code with TODO blocks",
    "bug-fix-lab": "Debugging-focused practice",
    "compare-approaches": "Baseline vs optimized trade-offs",
    "mini-project": "Small integrated application",
}

LEVEL_CHOICES = tuple(LEVEL_OBJECTIVES.keys())
PATTERN_CHOICES = tuple(PATTERN_LABEL.keys())
STANDARD_CHOICES = ("c++11", "c++14", "c++17", "c++20", "c++23")


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return slug or "lesson"


def escaped(text: str) -> str:
    return text.replace("\\", "\\\\").replace('"', '\\"')


def render_header(topic: str, level: str, pattern: str, standard: str, filename: str) -> str:
    lines = [
        "/*",
        f"Topic: {topic}",
        f"Level: {level}",
        f"Pattern: {pattern} ({PATTERN_LABEL[pattern]})",
        f"Standard: {standard}",
        "",
        "Learning objectives:",
    ]
    lines.extend(f"- {item}" for item in LEVEL_OBJECTIVES[level])
    lines.extend(
        [
            "",
            "Practice tasks:",
        ]
    )
    lines.extend(f"- TODO: {item}" for item in LEVEL_PRACTICE[level])
    lines.extend(
        [
            "",
            "Build:",
            f'  g++ -std={standard} -Wall -Wextra -pedantic "{filename}" -o lesson',
            "Run:",
            "  ./lesson",
            "*/",
        ]
    )
    return "\n".join(lines)


def render_pattern(pattern: str, topic: str) -> tuple[str, str]:
    topic_literal = escaped(topic)

    if pattern == "concept-demo":
        code = textwrap.dedent(
            f"""\
            void run_concept_demo(const std::vector<int>& data) {{
                std::cout << "[Concept Demo] Topic: {topic_literal}\\n";
                int total = std::accumulate(data.begin(), data.end(), 0);
                std::cout << "Total: " << total << "\\nValues:";
                for (int value : data) {{
                    std::cout << ' ' << value;
                }}
                std::cout << "\\n";
            }}
            """
        )
        main = textwrap.dedent(
            """\
            int main() {
                std::vector<int> sample{2, 4, 6, 8};
                run_concept_demo(sample);
                return 0;
            }
            """
        )
        return code, main

    if pattern == "guided-implementation":
        code = textwrap.dedent(
            f"""\
            int guided_solution(const std::vector<int>& data) {{
                int answer = 0;
                // TODO(student): Replace baseline logic using topic "{topic_literal}".
                for (int value : data) {{
                    answer += value;
                }}
                return answer;
            }}
            """
        )
        main = textwrap.dedent(
            """\
            int main() {
                std::vector<int> sample{1, 3, 5, 7};
                int answer = guided_solution(sample);
                std::cout << "Guided result: " << answer << "\\n";
                return 0;
            }
            """
        )
        return code, main

    if pattern == "bug-fix-lab":
        code = textwrap.dedent(
            """\
            /*
            Buggy snippet for students to inspect:
              int avg = total / count;  // count might be 0
            */
            int safe_average(const std::vector<int>& data) {
                if (data.empty()) {
                    return 0;
                }
                int total = std::accumulate(data.begin(), data.end(), 0);
                return total / static_cast<int>(data.size());
            }
            """
        )
        main = textwrap.dedent(
            """\
            int main() {
                std::vector<int> sample{10, 20, 30};
                std::cout << "Safe average: " << safe_average(sample) << "\\n";
                return 0;
            }
            """
        )
        return code, main

    if pattern == "compare-approaches":
        code = textwrap.dedent(
            """\
            int sum_with_loop(const std::vector<int>& data) {
                int total = 0;
                for (int value : data) {
                    total += value;
                }
                return total;
            }

            int sum_with_algorithm(const std::vector<int>& data) {
                return std::accumulate(data.begin(), data.end(), 0);
            }
            """
        )
        main = textwrap.dedent(
            """\
            int main() {
                std::vector<int> sample{5, 10, 15, 20};
                std::cout << "Loop sum: " << sum_with_loop(sample) << "\\n";
                std::cout << "Algorithm sum: " << sum_with_algorithm(sample) << "\\n";
                return 0;
            }
            """
        )
        return code, main

    code = textwrap.dedent(
        """\
        struct Student {
            std::string name;
            int score;
        };

        double class_average(const std::vector<Student>& roster) {
            if (roster.empty()) {
                return 0.0;
            }
            int total = 0;
            for (const auto& student : roster) {
                total += student.score;
            }
            return static_cast<double>(total) / static_cast<double>(roster.size());
        }
        """
    )
    main = textwrap.dedent(
        """\
        int main() {
            std::vector<Student> roster{
                {"Alice", 88},
                {"Bob", 76},
                {"Charlie", 91}
            };
            std::cout << "Class average: " << class_average(roster) << "\\n";
            return 0;
        }
        """
    )
    return code, main


def render_cpp(topic: str, level: str, pattern: str, standard: str, output_name: str) -> str:
    body, main = render_pattern(pattern, topic)
    header = render_header(topic, level, pattern, standard, output_name)
    return (
        header
        + "\n"
        + "#include <iostream>\n"
        + "#include <numeric>\n"
        + "#include <string>\n"
        + "#include <vector>\n\n"
        + body.rstrip()
        + "\n\n"
        + main.rstrip()
        + "\n"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scaffold a C++ teaching starter file based on topic, level, and lesson pattern."
    )
    parser.add_argument("--topic", required=True, help="Teaching topic, such as 'binary search basics'.")
    parser.add_argument(
        "--level",
        choices=LEVEL_CHOICES,
        default="beginner",
        help="Learner level. Default: beginner.",
    )
    parser.add_argument(
        "--pattern",
        choices=PATTERN_CHOICES,
        default="concept-demo",
        help="Lesson pattern. Default: concept-demo.",
    )
    parser.add_argument(
        "--standard",
        choices=STANDARD_CHOICES,
        default="c++17",
        help="C++ language standard. Default: c++17.",
    )
    parser.add_argument("--output", help="Output .cpp path. Default: <topic>_<level>.cpp in current directory.")
    parser.add_argument("--force", action="store_true", help="Overwrite output file if it already exists.")
    return parser.parse_args()


def resolve_output_path(topic: str, level: str, output: str | None) -> Path:
    if output:
        path = Path(output)
    else:
        path = Path(f"{slugify(topic)}_{level}.cpp")
    if path.suffix.lower() != ".cpp":
        path = path.with_suffix(".cpp")
    return path


def create_lesson_file(
    topic: str,
    level: str,
    pattern: str,
    standard: str,
    output_path: Path,
    force: bool = False,
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists() and not force:
        raise FileExistsError(
            f"Refusing to overwrite existing file: {output_path}. Use --force to overwrite."
        )

    cpp_content = render_cpp(
        topic=topic,
        level=level,
        pattern=pattern,
        standard=standard,
        output_name=output_path.name,
    )
    output_path.write_text(cpp_content, encoding="utf-8")
    return output_path


def main() -> None:
    args = parse_args()
    output_path = resolve_output_path(args.topic, args.level, args.output)
    try:
        generated = create_lesson_file(
            topic=args.topic,
            level=args.level,
            pattern=args.pattern,
            standard=args.standard,
            output_path=output_path,
            force=args.force,
        )
    except FileExistsError as exc:
        raise SystemExit(str(exc)) from exc
    print(f"Generated C++ lesson starter: {generated}")


if __name__ == "__main__":
    main()
