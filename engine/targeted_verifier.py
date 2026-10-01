import argparse
import json
from pathlib import Path


def load_json(path):
    return json.loads(
        Path(path).read_text(encoding="utf-8")
    )


def get_specifications(property_report):
    """
    Accept both:
    - specifications
    - security_properties
    - security_impacts
    """

    if isinstance(property_report.get("specifications"), list):
        return property_report["specifications"]

    if isinstance(property_report.get("security_properties"), list):
        return property_report["security_properties"]

    if isinstance(property_report.get("security_impacts"), list):
        specifications = []

        for item in property_report["security_impacts"]:
            specifications.append({
                "service": item.get("service"),
                "file": item.get("file"),
                "security_property": item.get(
                    "security_property",
                    "unknown_property"
                ),
                "severity": item.get(
                    "severity",
                    "medium"
                ),
                "category": item.get(
                    "category",
                    "security"
                ),
                "verification_strategy": item.get(
                    "verification_strategy",
                    "targeted_repository_verification"
                ),
            })

        return specifications

    return []


def get_evidence(evidence_report):
    """
    Accept different evidence report structures.
    """

    if isinstance(evidence_report.get("evidence"), list):
        return evidence_report["evidence"]

    if isinstance(evidence_report.get("items"), list):
        return evidence_report["items"]

    return []


def verify_property(specification, evidence):
    property_name = specification.get(
        "security_property",
        "unknown_property"
    )

    matching_evidence = [
        item
        for item in evidence
        if item.get("security_property") == property_name
    ]

    # If no explicit evidence exists, still perform a
    # targeted repository verification decision.
    if not matching_evidence:

        category = specification.get(
            "category",
            "security"
        )

        if category == "authorization":
            return {
                "status": "REVIEW",
                "reason": (
                    "Authorization-sensitive change detected; "
                    "manual security validation is required."
                ),
            }

        return {
            "status": "REVIEW",
            "reason": (
                "Security property was affected, but no "
                "matching repository evidence was available."
            ),
        }

    evidence_available = any(
        item.get("evidence_available", False)
        for item in matching_evidence
    )

    if not evidence_available:
        return {
            "status": "REVIEW",
            "reason": (
                "Property is affected but changed-code "
                "evidence is unavailable."
            ),
        }

    if specification.get("category") == "authorization":
        return {
            "status": "REVIEW",
            "reason": (
                "Authorization-sensitive change detected; "
                "manual security validation is required."
            ),
        }

    return {
        "status": "PASS",
        "reason": (
            "Security property mapped to repository evidence "
            "and targeted verification scope."
        ),
    }


def run_verification(property_report, evidence_report):
    specifications = get_specifications(property_report)
    evidence = get_evidence(evidence_report)

    results = []

    for specification in specifications:

        verification = verify_property(
            specification,
            evidence
        )

        results.append({
            "service": specification.get(
                "service",
                "unknown"
            ),
            "file": specification.get(
                "file",
                "unknown"
            ),
            "security_property": specification.get(
                "security_property",
                "unknown_property"
            ),
            "severity": specification.get(
                "severity",
                "medium"
            ),
            "verification_strategy": specification.get(
                "verification_strategy",
                "targeted_repository_verification"
            ),
            "verification": verification,
        })

    return results


def main():

    parser = argparse.ArgumentParser(
        description=(
            "Evidence-aware targeted security verifier"
        )
    )

    parser.add_argument(
        "--property-report",
        default=(
            "output/security_property_specification.json"
        ),
    )

    parser.add_argument(
        "--evidence-report",
        default="output/evidence_report.json",
    )

    parser.add_argument(
        "--output",
        default="output/verification_report.json",
    )

    args = parser.parse_args()

    property_report = load_json(
        args.property_report
    )

    evidence_report = load_json(
        args.evidence_report
    )

    results = run_verification(
        property_report,
        evidence_report
    )

    passed = sum(
        1
        for result in results
        if result["verification"]["status"] == "PASS"
    )

    review = sum(
        1
        for result in results
        if result["verification"]["status"] == "REVIEW"
    )

    output_data = {
        "engine": "evidence-aware-targeted-verifier",
        "version": "2.1",
        "total_checks": len(results),
        "passed": passed,
        "review_required": review,
        "results": results,
    }

    output = Path(args.output)
    output.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    output.write_text(
        json.dumps(
            output_data,
            indent=2
        ),
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "status": "success",
                "total_checks": len(results),
                "passed": passed,
                "review_required": review,
                "output": str(
                    output.resolve()
                ),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()