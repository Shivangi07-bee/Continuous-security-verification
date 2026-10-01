import json
from pathlib import Path

from security_properties import get_properties_for_services


def select_properties(impact_report):
    services = set()

    for impact in impact_report.get("security_impacts", []):
        service = impact.get("service")
        if service:
            services.add(service)

    properties = get_properties_for_services(services)

    return {
        "services_analyzed": sorted(services),
        "selected_properties": properties,
        "total_properties": len(properties),
    }


def main():
    input_file = Path("output/security_impact_report.json")
    output_file = Path("output/selected_security_properties.json")

    report = json.loads(input_file.read_text(encoding="utf-8"))

    result = select_properties(report)

    output_file.write_text(
        json.dumps(result, indent=2),
        encoding="utf-8",
    )

    print(json.dumps({
        "status": "success",
        "selected_properties": result["total_properties"],
        "output": str(output_file.resolve()),
    }, indent=2))


if __name__ == "__main__":
    main()