import argparse
import json
import re
from pathlib import Path


IGNORED_DIRS = {
    ".git",
    "node_modules",
    "__pycache__",
    "genproto",
    "vendor",
}


def get_services(src_dir):
    return {
        p.name
        for p in src_dir.iterdir()
        if p.is_dir() and p.name.endswith("service")
    }


def scan_relationships(src_dir, services):
    relationships = []

    files = [
        p for p in src_dir.rglob("*")
        if p.is_file()
        and not any(part in IGNORED_DIRS for part in p.parts)
        and p.suffix.lower() in {
            ".go", ".js", ".ts", ".py", ".java",
            ".proto", ".yaml", ".yml", ".json"
        }
    ]

    for source_file in files:
        try:
            text = source_file.read_text(
                encoding="utf-8",
                errors="ignore"
            )
        except OSError:
            continue

        source_service = None

        for service in services:
            if service in source_file.parts:
                source_service = service
                break

        if not source_service:
            continue

        for target_service in services:
            if target_service == source_service:
                continue

            pattern = rf"\b{re.escape(target_service)}\b"

            if re.search(pattern, text, re.IGNORECASE):
                relationships.append({
                    "source_service": source_service,
                    "target_service": target_service,
                    "evidence_file": str(
                        source_file.relative_to(src_dir)
                    ),
                    "relationship_type": "service_reference"
                })

    return relationships


def main():
    parser = argparse.ArgumentParser(
        description="Repository-aware service relationship builder"
    )

    parser.add_argument("--repo", required=True)
    parser.add_argument(
        "--change-report",
        default="output/change_report.json"
    )
    parser.add_argument(
        "--output",
        default="output/relationship_report.json"
    )

    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    src_dir = repo / "src"

    change_report = Path(args.change_report)

    report = json.loads(
        change_report.read_text(encoding="utf-8")
    )

    services = get_services(src_dir)
    relationships = scan_relationships(src_dir, services)

    affected = set(report["affected_services"])

    impacted_relationships = [
        r for r in relationships
        if r["source_service"] in affected
        or r["target_service"] in affected
    ]

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    result = {
        "engine": "relationship-builder",
        "version": "1.0",
        "repository": str(repo),
        "services_discovered": sorted(services),
        "total_relationships": len(relationships),
        "affected_services": sorted(affected),
        "impacted_relationships": impacted_relationships,
        "relationships": relationships,
    }

    output.write_text(
        json.dumps(result, indent=2),
        encoding="utf-8"
    )

    print(json.dumps({
        "status": "success",
        "services": len(services),
        "relationships": len(relationships),
        "impacted_relationships": len(
            impacted_relationships
        ),
        "output": str(output.resolve())
    }, indent=2))


if __name__ == "__main__":
    main()