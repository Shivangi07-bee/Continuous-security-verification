import argparse
import json
from pathlib import Path


PROPERTY_RULES = {
    "paymentservice": [
        {
            "property": "payment_transaction_integrity",
            "reason": "Payment processing logic may affect transaction integrity.",
        },
        {
            "property": "payment_authorization",
            "reason": "Changes to payment-service behavior may affect authorization decisions.",
        },
        {
            "property": "service_interaction_integrity",
            "reason": "Dependent services may rely on payment-service responses.",
        },
    ],
    "checkoutservice": [
        {
            "property": "checkout_transaction_integrity",
            "reason": "Checkout changes may affect transaction consistency.",
        }
    ],
}


SEMANTIC_PROPERTY_MAP = {
    "authorization_change": "payment_authorization",
    "transaction_change": "payment_transaction_integrity",
}


def map_security_impact(
    change_report,
    relationship_report,
    semantics_report,
):
    impacts = []

    semantic_by_path = {
        item["path"]: item.get("semantic_signals", [])
        for item in semantics_report.get("analyses", [])
    }

    relationships = relationship_report.get(
        "impacted_relationships",
        []
    )

    for change in change_report.get("changes", []):
        service = change.get("service")
        artifact = change.get("artifact_type")
        path = change.get("path")

        semantic_signals = semantic_by_path.get(path, [])

        # ---------------------------------------------------------
        # 1. Interface/API contract changes
        # ---------------------------------------------------------
        if artifact == "interface_contract":
            impacts.append({
                "service": service,
                "file": path,
                "artifact_type": artifact,
                "security_property": "service_contract_integrity",
                "reason": (
                    "A service interface contract changed; "
                    "consumers may be affected by the modified API contract."
                ),
                "impact_source": "interface_change",
                "verification_required": True,
            })

        # ---------------------------------------------------------
        # 2. Semantic security impact
        # ---------------------------------------------------------
        for signal in semantic_signals:
            semantic_domain = signal.get("semantic_domain")

            property_name = SEMANTIC_PROPERTY_MAP.get(
                semantic_domain
            )

            if property_name:
                impacts.append({
                    "service": service,
                    "file": path,
                    "artifact_type": artifact,
                    "security_property": property_name,
                    "reason": (
                        f"Semantic analysis detected "
                        f"{semantic_domain} in the changed artifact."
                    ),
                    "impact_source": "semantic_analysis",
                    "verification_required": True,
                })

        # ---------------------------------------------------------
        # 3. Service-specific security properties
        # ---------------------------------------------------------
        candidates = PROPERTY_RULES.get(service, [])

        semantic_properties = {
            SEMANTIC_PROPERTY_MAP.get(
                signal.get("semantic_domain")
            )
            for signal in semantic_signals
        }

        for candidate in candidates:
            property_name = candidate["property"]

            # Always preserve service interaction integrity.
            if property_name == "service_interaction_integrity":
                impacts.append({
                    "service": service,
                    "file": path,
                    "artifact_type": artifact,
                    "security_property": property_name,
                    "reason": candidate["reason"],
                    "impact_source": "service_change",
                    "verification_required": True,
                })

            # Add service-specific properties only when the
            # semantic analysis indicates that they are relevant.
            elif property_name in semantic_properties:
                impacts.append({
                    "service": service,
                    "file": path,
                    "artifact_type": artifact,
                    "security_property": property_name,
                    "reason": candidate["reason"],
                    "impact_source": "service_change",
                    "verification_required": True,
                })

        # ---------------------------------------------------------
        # 4. Relationship-based impact
        # ---------------------------------------------------------
        for relationship in relationships:
            if (
                relationship.get("source_service") == service
                or relationship.get("target_service") == service
            ):
                impacts.append({
                    "service": service,
                    "file": path,
                    "artifact_type": artifact,
                    "security_property": "service_interaction_integrity",
                    "reason": (
                        f"Change is connected to "
                        f"{relationship.get('source_service')} -> "
                        f"{relationship.get('target_service')}."
                    ),
                    "impact_source": "relationship",
                    "verification_required": True,
                })

    # -------------------------------------------------------------
    # Remove duplicates
    # -------------------------------------------------------------
    unique = {}

    for impact in impacts:
        key = (
            impact["service"],
            impact["security_property"],
            impact["impact_source"],
        )

        unique[key] = impact

    return list(unique.values())


def main():
    parser = argparse.ArgumentParser(
        description="Repository-aware security impact mapper"
    )

    parser.add_argument(
        "--change-report",
        default="output/change_report.json",
    )

    parser.add_argument(
        "--relationship-report",
        default="output/relationship_report.json",
    )

    parser.add_argument(
        "--semantics-report",
        default="output/change_semantics.json",
    )

    parser.add_argument(
        "--output",
        default="output/security_impact_report.json",
    )

    args = parser.parse_args()

    # -------------------------------------------------------------
    # Load change report
    # -------------------------------------------------------------
    change_report = json.loads(
        Path(args.change_report).read_text(
            encoding="utf-8"
        )
    )

    # -------------------------------------------------------------
    # Load relationship report
    # -------------------------------------------------------------
    relationship_report = json.loads(
        Path(args.relationship_report).read_text(
            encoding="utf-8"
        )
    )

    # -------------------------------------------------------------
    # Load semantic analysis report
    # -------------------------------------------------------------
    semantics_report = json.loads(
        Path(args.semantics_report).read_text(
            encoding="utf-8"
        )
    )

    # -------------------------------------------------------------
    # Map security impact
    # -------------------------------------------------------------
    impacts = map_security_impact(
        change_report,
        relationship_report,
        semantics_report,
    )

    result = {
        "engine": "security-impact-mapper",
        "version": "1.2",
        "security_impacts": impacts,
        "total_impacts": len(impacts),
    }

    # -------------------------------------------------------------
    # Write output
    # -------------------------------------------------------------
    output = Path(args.output)

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
                "status": "success",
                "security_impacts": len(impacts),
                "output": str(output.resolve()),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()