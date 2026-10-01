import argparse
import json
import subprocess
from pathlib import Path


def git(repo, *args):
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    )
    return result.stdout.strip()


def get_diff(repo, base, head, path):
    """
    Get the repository diff.

    WORKTREE means compare the base commit with
    the current working tree.
    """

    if head.upper() in ("WORKTREE", "WORKING_TREE"):
        return git(
            repo,
            "diff",
            "--unified=5",
            base,
            "--",
            path,
        )

    return git(
        repo,
        "diff",
        "--unified=5",
        base,
        head,
        "--",
        path,
    )


def collect_evidence(repo, base, head, impact_report):
    evidence = []

    for impact in impact_report.get(
        "security_impacts",
        []
    ):

        path = impact.get("file")

        if not path:
            continue

        try:
            diff = get_diff(
                repo,
                base,
                head,
                path,
            )
        except subprocess.CalledProcessError:
            diff = ""

        added_lines = []
        removed_lines = []

        for line in diff.splitlines():

            if (
                line.startswith("+")
                and not line.startswith("+++")
            ):
                added_lines.append(line[1:])

            elif (
                line.startswith("-")
                and not line.startswith("---")
            ):
                removed_lines.append(line[1:])

        changed_lines = (
            added_lines + removed_lines
        )

        evidence_available = bool(
            changed_lines
        )

        evidence.append({
            "service": impact.get(
                "service"
            ),
            "file": path,
            "security_property": impact.get(
                "security_property"
            ),
            "impact_source": impact.get(
                "impact_source"
            ),
            "reason": impact.get(
                "reason"
            ),
            "evidence_type": "repository_diff",
            "added_lines": added_lines,
            "removed_lines": removed_lines,
            "changed_lines": changed_lines,
            "lines_added": len(added_lines),
            "lines_removed": len(removed_lines),
            "evidence_available": evidence_available,
        })

    return evidence


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Repository-aware evidence collector"
        )
    )

    parser.add_argument(
        "--repo",
        required=True
    )

    parser.add_argument(
        "--base",
        required=True
    )

    parser.add_argument(
        "--head",
        default="WORKTREE"
    )

    parser.add_argument(
        "--impact-report",
        default=(
            "output/security_impact_report.json"
        )
    )

    parser.add_argument(
        "--output",
        default="output/evidence_report.json"
    )

    args = parser.parse_args()

    repo = Path(
        args.repo
    ).resolve()

    impact_report = json.loads(
        Path(
            args.impact_report
        ).read_text(
            encoding="utf-8"
        )
    )

    evidence = collect_evidence(
        repo,
        args.base,
        args.head,
        impact_report,
    )

    available = sum(
        1
        for item in evidence
        if item.get(
            "evidence_available",
            False
        )
    )

    result = {
        "engine": "evidence-collector",
        "version": "1.1",
        "base_commit": args.base,
        "head_commit": args.head,
        "evidence": evidence,
        "total_evidence_items": len(
            evidence
        ),
        "evidence_available": available,
    }

    output = Path(
        args.output
    )

    output.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    output.write_text(
        json.dumps(
            result,
            indent=2
        ),
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "status": "success",
                "evidence_items": len(
                    evidence
                ),
                "evidence_available": available,
                "output": str(
                    output.resolve()
                ),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()