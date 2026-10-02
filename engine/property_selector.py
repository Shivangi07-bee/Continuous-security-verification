import argparse
import json
from pathlib import Path


def load_json(path):
    return json.loads(
        Path(path).read_text(encoding="utf-8")
    )


def select_properties(impact_report):
    properties = []

    for impact in impact_report.get(
        "security_impacts",
        []
    ):
        properties.append({
            "service": impact.get("service"),
            "file": impact.get("file"),
            "security_property": impact.get(
                "security_property",
                "unknown_property"
            ),
            "severity": impact.get(
                "severity",
                "medium"
            ),
            "category": impact.get(
                "category",
                "security"
            ),
            "verification_strategy": impact.get(
                "verification_strategy",
                "targeted_repository_verification"
            ),
            "reason": impact.get(
                "reason",
                ""
            ),
            "verification_required": impact.get(
                "verification_required",
                True
            ),
        })

    unique = {}

    for item in properties:
        key = (
            item["service"],
            item["file"],
            item["security_property"],
        )
        unique[key] = item

    return list(unique.values())


def main():
    parser = argparse.ArgumentParser(
        description="Security property selector"
    )

    parser.add_argument(
        "--impact-report",
        required=True,
    )

    parser.add_argument(
        "--output",
        default="output/security_property_specification.json",
    )

    args = parser.parse_args()

    impact_report = load_json(
        args.impact_report
    )

    properties = select_properties(
        impact_report
    )

    result = {
        "engine": "security-property-selector",
        "version": "1.1",
        "security_properties": properties,
        "total_properties": len(properties),
    }

    output = Path(args.output)

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
                "status": "success",
                "security_properties": len(properties),
                "output": str(output.resolve()),
            },
            indent=2
        )
    )


if __name__ == "__main__":
    main()