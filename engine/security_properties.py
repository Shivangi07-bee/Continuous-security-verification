import json
from pathlib import Path


SECURITY_PROPERTIES = {
    "payment_transaction_integrity": {
        "description": "Payment processing must preserve transaction integrity.",
        "affected_services": ["paymentservice", "checkoutservice"],
        "verification_type": "transaction_flow",
    },
    "service_interaction_integrity": {
        "description": "Service-to-service interactions must remain within expected relationships.",
        "affected_services": [
            "paymentservice",
            "checkoutservice",
            "adservice",
            "frontend",
        ],
        "verification_type": "service_relationship",
    },
    "interface_contract_integrity": {
        "description": "Service interfaces must remain compatible after changes.",
        "affected_services": [
            "paymentservice",
            "checkoutservice",
            "currencyservice",
        ],
        "verification_type": "interface_contract",
    },
    "deployment_integrity": {
        "description": "Security-relevant deployment relationships must remain valid.",
        "affected_services": [],
        "verification_type": "deployment",
    },
}


def get_properties():
    return SECURITY_PROPERTIES


def get_properties_for_services(services):
    selected = {}

    for name, prop in SECURITY_PROPERTIES.items():
        if not prop["affected_services"]:
            continue

        if any(service in prop["affected_services"] for service in services):
            selected[name] = prop

    return selected


def save_properties(output="output/security_properties.json"):
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)

    path.write_text(
        json.dumps(SECURITY_PROPERTIES, indent=2),
        encoding="utf-8",
    )

    return path


if __name__ == "__main__":
    path = save_properties()

    print(json.dumps({
        "status": "success",
        "properties": len(SECURITY_PROPERTIES),
        "output": str(path.resolve()),
    }, indent=2))