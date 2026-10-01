import argparse
import subprocess
import sys
from pathlib import Path


def run(command):
    print("\n>>>", " ".join(command))

    result = subprocess.run(command)

    if result.returncode != 0:
        print("\nPipeline stopped: a module failed.")
        sys.exit(result.returncode)


def main():
    parser = argparse.ArgumentParser(
        description="Continuous Security Verification Pipeline"
    )

    parser.add_argument("--repo", required=True)
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", default="WORKTREE")

    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent
    engine = root / "engine"
    output = root / "output"

    output.mkdir(
        parents=True,
        exist_ok=True
    )

    change_report = output / "change_report.json"
    semantics_report = output / "change_semantics.json"
    relationship_report = output / "relationship_report.json"
    impact_report = output / "security_impact_report.json"
    property_report = output / "security_property_specification.json"
    evidence_report = output / "evidence_report.json"
    verification_report = output / "verification_report.json"
    rule_report = output / "security_rule_report.json"

    python = sys.executable

    # 1. Change extraction
    run([
        python,
        str(engine / "change_extractor.py"),
        "--repo", args.repo,
        "--base", args.base,
        "--head", args.head,
        "--output", str(change_report)
    ])

    # 2. Semantic analysis
    run([
        python,
        str(engine / "change_semantics.py"),
        "--repo", args.repo,
        "--base", args.base,
        "--head", args.head,
        "--output", str(semantics_report)
    ])

    # 3. Relationship analysis
    run([
        python,
        str(engine / "relationship_builder.py"),
        "--repo", args.repo,
        "--change-report", str(change_report),
        "--output", str(relationship_report)
    ])

    # 4. Security impact mapping
    run([
        python,
        str(engine / "security_impact_mapper.py"),
        "--change-report", str(change_report),
        "--relationship-report", str(relationship_report),
        "--semantics-report", str(semantics_report),
        "--output", str(impact_report)
    ])

    # 5. Security property selection
    run([
        python,
        str(engine / "property_selector.py"),
        "--impact-report", str(impact_report),
        "--output", str(property_report)
    ])

    # 6. Evidence collection
    run([
        python,
        str(engine / "evidence_collector.py"),
        "--repo", args.repo,
        "--base", args.base,
        "--head", args.head,
        "--impact-report", str(impact_report),
        "--output", str(evidence_report)
    ])

    # 7. Existing targeted verification
    run([
        python,
        str(engine / "targeted_verifier.py"),
        "--property-report", str(property_report),
        "--evidence-report", str(evidence_report),
        "--output", str(verification_report)
    ])

    # 8. Concrete security-rule verification
    run([
        python,
        str(engine / "security_rule_verifier.py"),
        "--evidence-report", str(evidence_report),
        "--output", str(rule_report)
    ])

    print("\n========================================")
    print("CONTINUOUS SECURITY VERIFICATION COMPLETE")
    print("========================================")
    print(f"Targeted report: {verification_report}")
    print(f"Security rule report: {rule_report}")


if __name__ == "__main__":
    main()