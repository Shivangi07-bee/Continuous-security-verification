import argparse
import json
import re
import subprocess
from pathlib import Path


SERVICE_ROOTS = {
    "src",
    "services",
    "service",
    "apps",
    "packages",
    "microservices",
    "components",
}


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
    """
    Infer a microservice/application name from
    common repository layouts.

    Supported examples:

        src/paymentservice/server.js
        services/orders/app.py
        apps/auth/main.py
        packages/catalog/index.js
        service/frontend/main.go

    If no service boundary can be inferred,
    return 'repository'.
    """

    normalized = path.replace("\\", "/")
    parts = normalized.split("/")

    if len(parts) >= 2:
        root = parts[0].lower()

        if root in SERVICE_ROOTS:
            return parts[1]

    return "repository"


def classify_file(path):
    """
    Classify the changed repository artifact.
    """

    normalized = path.replace("\\", "/")
    lower = normalized.lower()
    name = Path(lower).name

    if lower.endswith(".proto"):
        return "interface_contract"

    if name in {
        "dockerfile",
        "docker-compose.yml",
        "docker-compose.yaml",
    }:
        return "deployment"

    if (
        "kubernetes" in lower
        or "k8s" in lower
        or "/helm/" in lower
        or "/kustomize/" in lower
    ):
        return "deployment"

    if name in {
        "package.json",
        "package-lock.json",
        "yarn.lock",
        "pnpm-lock.yaml",
        "requirements.txt",
        "poetry.lock",
        "pyproject.toml",
        "go.mod",
        "go.sum",
        "cargo.toml",
        "cargo.lock",
        "pom.xml",
        "build.gradle",
        "build.gradle.kts",
    }:
        return "dependency_manifest"

    if lower.endswith(
        (
            ".yaml",
            ".yml",
            ".json",
            ".toml",
            ".ini",
            ".conf",
        )
    ):
        return "configuration"

    if lower.endswith(
        (
            ".py",
            ".js",
            ".jsx",
            ".ts",
            ".tsx",
            ".java",
            ".go",
            ".rs",
            ".cpp",
            ".cc",
            ".c",
            ".cs",
            ".php",
            ".rb",
            ".swift",
            ".kt",
        )
    ):
        return "source_code"

    if lower.endswith(
        (
            ".md",
            ".txt",
            ".rst",
        )
    ):
        return "documentation"

    return "other"


def extract_symbols(diff):
    """
    Extract common function/class declarations
    from changed lines.
    """

    symbols = []

    patterns = [
        r"\bdef\s+([A-Za-z_][A-Za-z0-9_]*)",
        r"\bclass\s+([A-Za-z_][A-Za-z0-9_]*)",
        r"\bfunction\s+([A-Za-z_][A-Za-z0-9_]*)",
        r"\bfunc\s+([A-Za-z_][A-Za-z0-9_]*)",
    ]

    for line in diff.splitlines():

        if not (
            line.startswith("+")
            or line.startswith("-")
        ):
            continue

        if line.startswith("+++"):
            continue

        for pattern in patterns:

            matches = re.findall(
                pattern,
                line,
            )

            symbols.extend(matches)

    return list(dict.fromkeys(symbols))


def get_changed_files(repo, base, head):
    """
    Return repository changes.

    WORKTREE means compare BASE against
    the current working tree.
    """

    if head.upper() in {
        "WORKTREE",
        "WORKING_TREE",
    }:

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

    return raw.splitlines()


def get_file_diff(
    repo,
    base,
    head,
    path,
):
    """
    Obtain the actual diff for one changed file.
    """

    if head.upper() in {
        "WORKTREE",
        "WORKING_TREE",
    }:

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


def parse_change_line(line):
    """
    Parse git --name-status output.

    Handles:

        M file
        A file
        D file
        R100 old new
        C100 old new
    """

    parts = line.split("\t")

    if not parts:
        return None

    status = parts[0]

    if status.startswith("R") and len(parts) >= 3:

        return {
            "status": "R",
            "old_path": parts[1],
            "path": parts[2],
        }

    if status.startswith("C") and len(parts) >= 3:

        return {
            "status": "C",
            "old_path": parts[1],
            "path": parts[2],
        }

    if len(parts) >= 2:

        return {
            "status": status[0],
            "path": parts[1],
        }

    return None


def extract_changes(
    repo,
    base,
    head,
):
    """
    Extract structured repository evolution.
    """

    changes = []

    lines = get_changed_files(
            repo,
            base,
            head,
        )

    for line in lines:

        parsed = parse_change_line(line)

        if not parsed:
            continue

        path = parsed["path"]

        service = infer_service(path)

        artifact_type = classify_file(path)

        try:

            diff = get_file_diff(
                    repo,
                    base,
                    head,
                    path,
                )

        except subprocess.CalledProcessError:

            diff = ""

        symbols = extract_symbols(diff)

        change = {
            "status":
                parsed["status"],

            "path":
                path,

            "service":
                service,

            "artifact_type":
                artifact_type,

            "symbols":
                symbols,
        }

        if "old_path" in parsed:

            change["old_path"] = parsed["old_path"]

        changes.append(change)

    return changes


def main():

    parser = argparse.ArgumentParser(
        description=(
            "Generic repository-aware "
            "change extraction engine"
        )
    )

    parser.add_argument(
        "--repo",
        required=True,
    )

    parser.add_argument(
        "--base",
        required=True,
    )

    parser.add_argument(
        "--head",
        default="WORKTREE",
    )

    parser.add_argument(
        "--output",
        default=(
            "output/change_report.json"
        ),
    )

    args = parser.parse_args()

    repo = Path(
            args.repo
        ).resolve()

    changes = extract_changes(
            repo,
            args.base,
            args.head,
        )

    affected_services = sorted(
            {
                change["service"]
                for change in changes
            }
        )

    result = {
        "engine":
            "change-extraction-engine",

        "version":
            "2.0",

        "repository":
            str(repo),

        "base_commit":
            args.base,

        "head_commit":
            args.head,

        "changed_files":
            len(changes),

        "affected_services":
            affected_services,

        "changes":
            changes,
    }

    output = Path(
            args.output
        )

    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output.write_text(
        json.dumps(
            result,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "status":
                    "success",

                "changed_files":
                    len(changes),

                "affected_services":
                    affected_services,

                "output":
                    str(
                        output.resolve()
                    ),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()