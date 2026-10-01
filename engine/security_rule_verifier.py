import argparse
import json
import re
from pathlib import Path


SECURITY_RULES = {
    "payment_authorization": {
        "description": "Payment amount must be strictly greater than zero.",
        "pattern": r"Number\s*\(\s*call\.request\.amount\s*\)\s*>\s*0",
    },
    "payment_transaction_integrity": {
        "description": "Transaction amount must be a valid finite numeric value.",
        "pattern": r"Number\.isFinite\s*\(\s*transactionAmount\s*\)",
    },
}


def load_json(path):
    return json.loads(
        Path(path).read_text(
            encoding="utf-8"
        )
    )


def extract_changed_code(evidence_report):
    changed_code = []

    for item in evidence_report.get(
        "evidence",
        []
    ):
        changed_code.append({
            "service": item.get("service"),
            "file": item.get("file"),
            "security_property": item.get(
                "security_property"
            ),
            "added_lines": item.get(
                "added_lines",
                []
            ),
            "removed_lines": item.get(
                "removed_lines",
                []
            ),
        })

    return changed_code


def deduplicate_evidence(items):
    unique = {}

    for item in items:
        key = (
            item.get("service"),
            item.get("file"),
            item.get("security_property"),
        )

        if key not in unique:
            unique[key] = {
                **item,
                "added_lines": [],
                "removed_lines": [],
            }

        unique[key]["added_lines"].extend(
            item.get("added_lines", [])
        )

        unique[key]["removed_lines"].extend(
            item.get("removed_lines", [])
        )

    for item in unique.values():
        item["added_lines"] = list(
            dict.fromkeys(
                item["added_lines"]
            )
        )

        item["removed_lines"] = list(
            dict.fromkeys(
                item["removed_lines"]
            )
        )

    return list(unique.values())


def verify_payment_authorization(item):
    added_lines = item.get(
        "added_lines",
        []
    )

    removed_lines = item.get(
        "removed_lines",
        []
    )

    added_code = "\n".join(
        added_lines
    )

    removed_code = "\n".join(
        removed_lines
    )

    rule = SECURITY_RULES[
        "payment_authorization"
    ]

    insecure_operator = bool(
        re.search(
            r"Number\s*\(\s*call\.request\.amount\s*\)\s*>=\s*0",
            added_code
        )
    )

    secure_rule_present = bool(
        re.search(
            rule["pattern"],
            added_code
        )
    )

    secure_rule_removed = bool(
        re.search(
            rule["pattern"],
            removed_code
        )
    )

    if insecure_operator:
        return {
            "status": "FAIL",
            "reason": (
                "The authorization condition was weakened "
                "from a strictly positive amount check to "
                "a non-negative amount check."
            ),
            "rule": rule["description"],
            "evidence": added_lines,
        }

    if secure_rule_present:
        return {
            "status": "PASS",
            "reason": (
                "The changed code preserves the required "
                "positive payment amount authorization rule."
            ),
            "rule": rule["description"],
            "evidence": added_lines,
        }

    if secure_rule_removed:
        return {
            "status": "FAIL",
            "reason": (
                "The required payment authorization rule "
                "was removed or weakened."
            ),
            "rule": rule["description"],
            "evidence": removed_lines,
        }

    return {
        "status": "REVIEW",
        "reason": (
            "The authorization property changed, but the "
            "security rule could not be determined from "
            "the available repository evidence."
        ),
        "rule": rule["description"],
        "evidence": (
            added_lines +
            removed_lines
        ),
    }


def verify_payment_transaction_integrity(item):
    added_lines = item.get(
        "added_lines",
        []
    )

    removed_lines = item.get(
        "removed_lines",
        []
    )

    added_code = "\n".join(
        added_lines
    )

    rule = SECURITY_RULES[
        "payment_transaction_integrity"
    ]

    validation_present = bool(
        re.search(
            rule["pattern"],
            added_code
        )
    )

    transaction_amount_present = bool(
        re.search(
            r"const\s+transactionAmount\s*=\s*Number\s*\(",
            added_code
        )
    )

    if validation_present and transaction_amount_present:
        return {
            "status": "PASS",
            "reason": (
                "The changed payment logic validates that "
                "the transaction amount is a finite numeric value."
            ),
            "rule": rule["description"],
            "evidence": added_lines,
        }

    if removed_lines and not added_lines:
        return {
            "status": "FAIL",
            "reason": (
                "Transaction validation logic was removed "
                "without a corresponding replacement."
            ),
            "rule": rule["description"],
            "evidence": removed_lines,
        }

    return {
        "status": "REVIEW",
        "reason": (
            "A transaction-integrity change was detected, "
            "but the concrete transaction validation rule "
            "could not be established."
        ),
        "rule": rule["description"],
        "evidence": (
            added_lines +
            removed_lines
        ),
    }


def verify_property(item):
    property_name = item.get(
        "security_property"
    )

    if property_name == "payment_authorization":
        return verify_payment_authorization(
            item
        )

    if property_name == "payment_transaction_integrity":
        return verify_payment_transaction_integrity(
            item
        )

    return {
        "status": "REVIEW",
        "reason": (
            "No concrete security rule is currently "
            "defined for this security property."
        ),
        "rule": None,
        "evidence": (
            item.get("added_lines", []) +
            item.get("removed_lines", [])
        ),
    }


def run_verification(evidence_report):
    evidence = extract_changed_code(
        evidence_report
    )

    evidence = deduplicate_evidence(
        evidence
    )

    results = []

    for item in evidence:
        verification = verify_property(
            item
        )

        results.append({
            "service": item.get(
                "service"
            ),
            "file": item.get(
                "file"
            ),
            "security_property": item.get(
                "security_property"
            ),
            "verification": verification,
        })

    return results


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Rule-based security verification "
            "against changed repository code"
        )
    )

    parser.add_argument(
        "--evidence-report",
        default=(
            "output/evidence_report.json"
        ),
    )

    parser.add_argument(
        "--output",
        default=(
            "output/security_rule_report.json"
        ),
    )

    args = parser.parse_args()

    evidence_report = load_json(
        args.evidence_report
    )

    results = run_verification(
        evidence_report
    )

    passed = sum(
        1
        for item in results
        if item["verification"]["status"]
        == "PASS"
    )

    failed = sum(
        1
        for item in results
        if item["verification"]["status"]
        == "FAIL"
    )

    review = sum(
        1
        for item in results
        if item["verification"]["status"]
        == "REVIEW"
    )

    output_data = {
        "engine": "security-rule-verifier",
        "version": "1.2",
        "total_checks": len(results),
        "passed": passed,
        "failed": failed,
        "review_required": review,
        "results": results,
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
            output_data,
            indent=2
        ),
        encoding="utf-8"
    )

    print(
        json.dumps(
            {
                "status": "success",
                "total_checks": len(results),
                "passed": passed,
                "failed": failed,
                "review_required": review,
                "output": str(
                    output.resolve()
                ),
            },
            indent=2
        )
    )


if __name__ == "__main__":
    main()