import argparse
import json
from pathlib import Path


SECURITY_PROPERTIES = {
    "payment_transaction_integrity": {
        "category": "transaction",
        "invariant": (
            "A payment transaction must preserve its amount, "
            "payment identity, and transaction state across service interactions."
        ),
        "verification_strategy": "transaction_state_consistency",
        "severity": "high",
    },

    "payment_authorization": {
        "category": "authorization",
        "invariant": (
            "A payment operation must only be accepted when the "
            "required authorization context is valid."
        ),
        "verification_strategy": "authorization_precondition",
        "severity": "critical",
    },

    "service_interaction_integrity": {
        "category": "service_interaction",
        "invariant": (
            "A service interaction must preserve the expected "
            "contract and security assumptions between communicating services."
        ),
        "verification_strategy": "interaction_contract_consistency",
        "severity": "high",
    },

    "service_contract_integrity": {
        "category": "interface",
        "invariant": (
            "Changes to an exposed service contract must remain "
            "compatible with its dependent service interactions."
        ),
        "verification_strategy": "interface_compatibility",
        "severity": "high",
    },

    "checkout_transaction_integrity": {
        "category": "transaction",
        "invariant": (
            "A checkout operation must preserve the consistency "
            "of the order and payment workflow."
        ),
        "verification_strategy": "workflow_state_consistency",
        "severity": "high",
    },
}


def build_specification(impact_report):
    specifications = []

    for impact in impact_report.get("security_impacts", []):
        property_name = impact.get("security_property")

        definition = SECURITY_PROPERTIES.get(property_name)

        if not definition:
            continue

        specifications.append({
            "service": impact.get("service"),
            "file": impact.get("file"),
            "security_property": property_name,
            "category": definition["category"],
            "invariant": definition["invariant"],
            "verification_strategy": definition["verification_strategy"],
            "severity": definition["severity"],
            "impact_source": impact.get("impact_source"),
            "verification_required": impact.get(
                "verification_required",
                True
            ),
        })

    # Remove duplicate specifications
    unique = {}

    for specification in specifications:
        key = (
            specification["service"],
            specification["security_property"],
        )
        unique[key] = specification

    return list(unique.values())


def main():
    parser = argparse.ArgumentParser(
        description="Security property specification engine"
    )

    parser.add_argument(
        "--impact-report",
        default="output/security_impact_report.json"
    )

    parser.add_argument(
        "--output",
        default="output/security_property_specification.json"
    )

    args = parser.parse_args()

    impact_report = json.loads(
        Path(args.impact_report).read_text(
            encoding="utf-8"
        )
    )

    specifications = build_specification(
        impact_report
    )

    result = {
        "engine": "security-property-model",
        "version": "1.0",
        "specifications": specifications,
        "total_properties": len(specifications),
    }

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    output.write_text(
        json.dumps(result, indent=2),
        encoding="utf-8"
    )

    print(json.dumps({
        "status": "success",
        "security_properties": len(specifications),
        "output": str(output.resolve())
    }, indent=2))


if __name__ == "__main__":
    main()