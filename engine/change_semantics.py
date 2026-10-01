import argparse
import json
import re
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
    return result.stdout


def analyze_diff(diff):
    added_lines = []
    removed_lines = []

    for line in diff.splitlines():
        if line.startswith("+++") or line.startswith("---"):
            continue

        if line.startswith("+"):
            added_lines.append(line[1:].strip())

        elif line.startswith("-"):
            removed_lines.append(line[1:].strip())

    added_text = " ".join(added_lines).lower()
    removed_text = " ".join(removed_lines).lower()

    signals = []

    patterns = {
        "authorization_change": [
            "authorization",
            "authorize",
            "permission",
            "isadmin",
            "role",
            "access",
        ],
        "authentication_change": [
            "authentication",
            "authenticate",
            "token",
            "jwt",
            "credential",
        ],
        "transaction_change": [
            "transaction",
            "payment",
            "charge",
            "amount",
            "currency",
        ],
        "service_call_change": [
            "grpc",
            "client",
            "call",
            "request",
            "response",
        ],
        "interface_change": [
            "rpc ",
            "message ",
            "service ",
            "returns",
        ],
        "state_change": [
            "status",
            "state",
            "pending",
            "complete",
            "failed",
        ],
    }

    for signal, keywords in patterns.items():
        added_matches = [
            keyword for keyword in keywords
            if keyword in added_text
        ]

        removed_matches = [
            keyword for keyword in keywords
            if keyword in removed_text
        ]

        if added_matches or removed_matches:
            signals.append({
                "semantic_domain": signal,
                "added_indicators": added_matches,
                "removed_indicators": removed_matches,
            })

    return {
        "lines_added": len(added_lines),
        "lines_removed": len(removed_lines),
        "semantic_signals": signals,
    }


def analyze_file(repo, base, head, path):
    if head.upper() == "WORKTREE":
        diff = git(
            repo,
            "diff",
            "--unified=5",
            base,
            "--",
            path,
        )
    else:
        diff = git(
            repo,
            "diff",
            "--unified=5",
            base,
            head,
            "--",
            path,
        )

    result = analyze_diff(diff)

    return {
        "path": path,
        **result,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Repository-aware change semantics analyzer"
    )

    parser.add_argument("--repo", required=True)
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", default="WORKTREE")
    parser.add_argument(
        "--change-report",
        default="output/change_report.json",
    )
    parser.add_argument(
        "--output",
        default="output/change_semantics.json",
    )

    args = parser.parse_args()

    repo = Path(args.repo).resolve()

    with open(args.change_report, "r", encoding="utf-8") as f:
        change_report = json.load(f)

    analyses = []

    for change in change_report["changes"]:
        analyses.append(
            analyze_file(
                repo,
                args.base,
                args.head,
                change["path"],
            )
        )

    result = {
        "engine": "change-semantics-analyzer",
        "version": "1.0",
        "repository": str(repo),
        "base_commit": args.base,
        "head_commit": args.head,
        "analyses": analyses,
    }

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    output.write_text(
        json.dumps(result, indent=2),
        encoding="utf-8",
    )

    print(json.dumps({
        "status": "success",
        "files_analyzed": len(analyses),
        "output": str(output.resolve()),
    }, indent=2))


if __name__ == "__main__":
    main()