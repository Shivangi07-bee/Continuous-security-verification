import argparse
import json
import re
import subprocess
from pathlib import Path


# =========================================================
# SECURITY-RELEVANT SEMANTIC DOMAINS
# =========================================================

SEMANTIC_PATTERNS = {

    "authorization_change": [
        r"\bauthoriz",
        r"\bpermission\b",
        r"\bpermissions\b",
        r"\bisadmin\b",
        r"\brole\b",
        r"\baccess\b",
        r"\bacl\b",
        r"\brbac\b",
        r"\bpolicy\b",
    ],

    "authentication_change": [
        r"\bauthenticat",
        r"\blogin\b",
        r"\blogout\b",
        r"\bcredential",
        r"\bpassword\b",
        r"\bjwt\b",
        r"\btoken\b",
        r"\bsession\b",
        r"\boauth\b",
        r"\bidentity\b",
    ],

    "transaction_change": [
        r"\btransaction\b",
        r"\bpayment\b",
        r"\bcharge\b",
        r"\bamount\b",
        r"\bcurrency\b",
        r"\bprice\b",
        r"\bbalance\b",
        r"\brefund\b",
        r"\border\b",
    ],

    "service_call_change": [
        r"\bgrpc\b",
        r"\bgrpc\.status\b",
        r"\bclient\b",
        r"\bcall\b",
        r"\brequest\b",
        r"\bresponse\b",
        r"\bhttp\b",
        r"\brest\b",
        r"\bendpoint\b",
        r"\bservice\b",
    ],

    "interface_change": [
        r"\brpc\b",
        r"\bmessage\b",
        r"\bservice\b",
        r"\breturns\b",
        r"\bprotobuf\b",
        r"\bproto\b",
        r"\bapi\b",
        r"\binterface\b",
    ],

    "state_change": [
        r"\bstatus\b",
        r"\bstate\b",
        r"\bpending\b",
        r"\bcomplete\b",
        r"\bcompleted\b",
        r"\bfailed\b",
        r"\bsuccess\b",
        r"\bactive\b",
        r"\binactive\b",
    ],
}


# =========================================================
# GIT
# =========================================================

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


# =========================================================
# DIFF EXTRACTION
# =========================================================

def get_changed_files(
    repo,
    base,
    head,
):

    if head.upper() in {
        "WORKTREE",
        "WORKING_TREE",
    }:

        return git(
            repo,
            "diff",
            "--name-only",
            base,
        )

    return git(
        repo,
        "diff",
        "--name-only",
        base,
        head,
    )


def get_file_diff(
    repo,
    base,
    head,
    path,
):

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


# =========================================================
# SEMANTIC ANALYSIS
# =========================================================

def analyze_diff(diff):

    added_lines = []
    removed_lines = []

    for line in diff.splitlines():

        if (
            line.startswith("+")
            and not line.startswith("+++")
        ):
            added_lines.append(
                line[1:]
            )

        elif (
            line.startswith("-")
            and not line.startswith("---")
        ):
            removed_lines.append(
                line[1:]
            )


    added_text = "\n".join(
        added_lines
    ).lower()

    removed_text = "\n".join(
        removed_lines
    ).lower()


    combined_text = (
        added_text
        + "\n"
        + removed_text
    )


    signals = []


    for domain, patterns in SEMANTIC_PATTERNS.items():

        matched_keywords = []


        for pattern in patterns:

            if re.search(
                pattern,
                combined_text,
                re.IGNORECASE,
            ):

                keyword = (
                    pattern
                    .replace(r"\b", "")
                    .replace("\\", "")
                )

                matched_keywords.append(
                    keyword
                )


        if matched_keywords:

            signals.append({

                "semantic_domain":
                    domain,

                "matched_keywords":
                    list(
                        dict.fromkeys(
                            matched_keywords
                        )
                    ),

                "evidence_lines":
                    len(
                        added_lines
                        + removed_lines
                    ),
            })


    return {
        "added_lines":
            added_lines,

        "removed_lines":
            removed_lines,

        "semantic_signals":
            signals,
    }


# =========================================================
# MAIN SEMANTIC ENGINE
# =========================================================

def analyze_repository(
    repo,
    base,
    head,
    change_report,
):

    analyses = []

    changes = change_report.get(
        "changes",
        []
    )


    for change in changes:

        path = change.get(
            "path"
        )

        if not path:
            continue


        try:

            diff = get_file_diff(
                repo,
                base,
                head,
                path,
            )

        except subprocess.CalledProcessError:

            diff = ""


        analysis = analyze_diff(
                diff
            )


        analyses.append({

            "path":
                path,

            "service":
                change.get(
                    "service",
                    "repository"
                ),

            "artifact_type":
                change.get(
                    "artifact_type",
                    "other"
                ),

            "semantic_signals":
                analysis[
                    "semantic_signals"
                ],

            "added_lines":
                analysis[
                    "added_lines"
                ],

            "removed_lines":
                analysis[
                    "removed_lines"
                ],

        })


    return analyses


# =========================================================
# CLI
# =========================================================

def main():

    parser = argparse.ArgumentParser(
        description=(
            "Generic repository-aware "
            "change semantic analyzer"
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
        "--change-report",
        default=(
            "output/change_report.json"
        ),
    )


    parser.add_argument(
        "--output",
        default=(
            "output/change_semantics.json"
        ),
    )


    args = parser.parse_args()


    repo = Path(
            args.repo
        ).resolve()


    change_report = json.loads(
            Path(
                args.change_report
            ).read_text(
                encoding="utf-8"
            )
        )


    analyses = analyze_repository(
            repo,
            args.base,
            args.head,
            change_report,
        )


    semantic_domains = sorted(
        {
            signal.get(
                "semantic_domain"
            )

            for analysis in analyses

            for signal in analysis.get(
                "semantic_signals",
                []
            )

            if signal.get(
                "semantic_domain"
            )
        }
    )


    result = {

        "engine":
            "change-semantic-analyzer",

        "version":
            "2.0",

        "mode":
            "repository-generic",

        "repository":
            str(repo),

        "base_commit":
            args.base,

        "head_commit":
            args.head,

        "analyses":
            analyses,

        "semantic_domains_detected":
            semantic_domains,

        "total_analyses":
            len(analyses),

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
        encoding="utf-8"
    )


    print(
        json.dumps(
            {
                "status":
                    "success",

                "analyses":
                    len(analyses),

                "semantic_domains":
                    semantic_domains,

                "output":
                    str(
                        output.resolve()
                    ),
            },
            indent=2
        )
    )


if __name__ == "__main__":
    main()