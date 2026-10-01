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
    return result.stdout.strip()


def infer_service(path):
    parts = Path(path).parts

    if "src" in parts:
        i = parts.index("src")
        if i + 1 < len(parts):
            return parts[i + 1]

    return None


def classify_file(path):
    p = path.lower()

    if p.endswith(".proto"):
        return "interface_contract"

    if "dockerfile" in p:
        return "container"

    if any(x in p for x in ["kubernetes", "helm", "kustomize"]):
        return "deployment"

    if any(x in p for x in [
        "requirements", "package.json", "go.mod",
        "pom.xml", "build.gradle", "cargo.toml"
    ]):
        return "dependency"

    if p.endswith((".yaml", ".yml", ".json", ".toml")):
        return "configuration"

    if p.endswith((
        ".py", ".go", ".java", ".js", ".ts",
        ".cpp", ".c", ".cs", ".rs", ".php"
    )):
        return "source_code"

    return "other"


def extract_symbols(diff):
    symbols = set()

    patterns = [
        r"(?:def|async\s+def)\s+([A-Za-z_]\w*)",
        r"(?:func)\s+([A-Za-z_]\w*)",
        r"(?:class)\s+([A-Za-z_]\w*)",
        r"(?:function)\s+([A-Za-z_]\w*)",
    ]

    for line in diff.splitlines():
        line = line.lstrip("+- ")

        for pattern in patterns:
            for match in re.finditer(pattern, line):
                symbols.add(match.group(1))

    return sorted(symbols)


def extract_changes(repo, base, head):
    if head == "WORKTREE":
     raw = git(
        repo,
        "diff",
        "--name-status",
        "--find-renames",
        "--find-copies",
        base,
    )
    else:
     raw = git(
        repo,
        "diff",
        "--name-status",
        "--find-renames",
        "--find-copies",
        base,
        head,
    )

    changes = []

    for line in raw.splitlines():
        if not line.strip():
            continue

        fields = line.split("\t")
        status = fields[0]

        old_path = None
        path = fields[-1]

        if status.startswith(("R", "C")) and len(fields) >= 3:
            old_path = fields[1]
            path = fields[2]

        change_type = {
            "A": "added",
            "M": "modified",
            "D": "deleted",
        }.get(status[0], status)

        if head == "WORKTREE":
         diff = git(
        repo,
        "diff",
        "--unified=3",
        base,
        "--",
        path,
    )
        else:
         diff = git(
        repo,
        "diff",
        "--unified=3",
        base,
        head,
        "--",
        path,
    )

        added = sum(
            1 for x in diff.splitlines()
            if x.startswith("+") and not x.startswith("+++")
        )

        removed = sum(
            1 for x in diff.splitlines()
            if x.startswith("-") and not x.startswith("---")
        )

        artifact = classify_file(path)

        impact = []

        if artifact == "source_code":
            impact.append("service_behavior")

        if artifact == "interface_contract":
            impact.append("service_contract")

        if artifact == "dependency":
            impact.append("dependency_graph")

        if artifact == "deployment":
            impact.append("deployment_topology")

        changes.append({
            "status": status,
            "change_type": change_type,
            "path": path,
            "old_path": old_path,
            "service": infer_service(path),
            "artifact_type": artifact,
            "lines_added": added,
            "lines_removed": removed,
            "symbols_touched": extract_symbols(diff),
            "potential_impact_domains": impact,
        })

    return changes


def main():
    parser = argparse.ArgumentParser(
        description="Repository-aware change extraction engine"
    )

    parser.add_argument("--repo", required=True)
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", default="HEAD")
    parser.add_argument(
        "--output",
        default="output/change_report.json"
    )

    args = parser.parse_args()

    repo = Path(args.repo).resolve()

    changes = extract_changes(
        repo,
        args.base,
        args.head
    )

    report = {
        "engine": "change-extraction-engine",
        "version": "1.0",
        "repository": str(repo),
        "base_commit": args.base,
        "head_commit": args.head,
        "changed_files": len(changes),
        "affected_services": sorted({
            c["service"]
            for c in changes
            if c["service"]
        }),
        "changes": changes,
    }

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    output.write_text(
        json.dumps(report, indent=2),
        encoding="utf-8"
    )

    print(json.dumps({
        "status": "success",
        "changed_files": len(changes),
        "affected_services": report["affected_services"],
        "output": str(output.resolve())
    }, indent=2))


if __name__ == "__main__":
    main()