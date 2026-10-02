import argparse
import json
from pathlib import Path


# ---------------------------------------------------------
# Known security mappings
# These preserve the existing Online Boutique experiments.
# ---------------------------------------------------------

KNOWN_SEMANTIC_PROPERTY_MAP = {
    "authorization_change":
        "payment_authorization",

    "transaction_change":
        "payment_transaction_integrity",
}


# ---------------------------------------------------------
# Generic security-property mapping
# ---------------------------------------------------------

GENERIC_SEMANTIC_PROPERTY_MAP = {
    "authorization_change":
        "authorization_integrity",

    "authentication_change":
        "authentication_integrity",

    "transaction_change":
        "transaction_integrity",

    "service_call_change":
        "service_interaction_integrity",

    "interface_change":
        "service_contract_integrity",

    "state_change":
        "state_integrity",
}


def generic_property_for_artifact(
    artifact_type
):
    """
    Assign a generic security property based
    on the type of repository artifact changed.
    """

    if artifact_type == "interface_contract":
        return "service_contract_integrity"

    if artifact_type == "deployment":
        return "deployment_security_integrity"

    if artifact_type == "dependency_manifest":
        return "dependency_integrity"

    if artifact_type == "configuration":
        return "configuration_security_integrity"

    if artifact_type == "source_code":
        return "source_security_integrity"

    return None


def map_security_impact(
    change_report,
    relationship_report,
    semantics_report,
):
    impacts = []

    semantic_by_path = {
        item.get("path"):
            item.get(
                "semantic_signals",
                []
            )
        for item in semantics_report.get(
            "analyses",
            []
        )
    }

    relationships = relationship_report.get(
        "impacted_relationships",
        []
    )

    for change in change_report.get(
        "changes",
        []
    ):

        service = change.get(
            "service",
            "repository"
        )

        path = change.get(
            "path"
        )

        artifact = change.get(
            "artifact_type",
            "other"
        )

        semantic_signals = semantic_by_path.get(
            path,
            []
        )


        # -------------------------------------------------
        # 1. Semantic security impacts
        # -------------------------------------------------

        for signal in semantic_signals:

            semantic_domain = signal.get(
                "semantic_domain"
            )

            # Preserve existing Online Boutique
            # property names.
            property_name = (
                KNOWN_SEMANTIC_PROPERTY_MAP.get(
                    semantic_domain
                )
            )

            # Generic fallback for other repositories.
            if not property_name:

                property_name = (
                    GENERIC_SEMANTIC_PROPERTY_MAP.get(
                        semantic_domain
                    )
                )

            if not property_name:
                continue

            impacts.append({

                "service":
                    service,

                "file":
                    path,

                "artifact_type":
                    artifact,

                "security_property":
                    property_name,

                "reason":
                    (
                        "Semantic analysis detected "
                        f"{semantic_domain} in the "
                        "changed repository artifact."
                    ),

                "impact_source":
                    "semantic_analysis",

                "verification_required":
                    True,
            })


        # -------------------------------------------------
        # 2. Artifact-level security impact
        # -------------------------------------------------

        artifact_property = (
            generic_property_for_artifact(
                artifact
            )
        )

        if artifact_property:

            impacts.append({

                "service":
                    service,

                "file":
                    path,

                "artifact_type":
                    artifact,

                "security_property":
                    artifact_property,

                "reason":
                    (
                        "A security-relevant repository "
                        f"artifact of type '{artifact}' "
                        "was changed."
                    ),

                "impact_source":
                    "artifact_analysis",

                "verification_required":
                    True,
            })


        # -------------------------------------------------
        # 3. Service relationship impact
        # -------------------------------------------------

        for relationship in relationships:

            source = relationship.get(
                    "source_service"
                )

            target = relationship.get(
                    "target_service"
                )

            if (
                source == service
                or target == service
            ):

                impacts.append({

                    "service":
                        service,

                    "file":
                        path,

                    "artifact_type":
                        artifact,

                    "security_property":
                        "service_interaction_integrity",

                    "reason":
                        (
                            "The changed service is connected "
                            f"to the service relationship "
                            f"{source} -> {target}."
                        ),

                    "impact_source":
                        "relationship",

                    "verification_required":
                        True,
                })


    # -----------------------------------------------------
    # Remove duplicate impacts
    # -----------------------------------------------------

    unique = {}

    for impact in impacts:

        key = (
            impact.get("service"),
            impact.get("file"),
            impact.get(
                "security_property"
            ),
            impact.get(
                "impact_source"
            ),
        )

        unique[key] = impact


    return list(
        unique.values()
    )


def main():

    parser = argparse.ArgumentParser(
        description=(
            "Generic repository-aware "
            "security impact mapper"
        )
    )

    parser.add_argument(
        "--change-report",
        default=(
            "output/change_report.json"
        ),
    )

    parser.add_argument(
        "--relationship-report",
        default=(
            "output/relationship_report.json"
        ),
    )

    parser.add_argument(
        "--semantics-report",
        default=(
            "output/change_semantics.json"
        ),
    )

    parser.add_argument(
        "--output",
        default=(
            "output/security_impact_report.json"
        ),
    )

    args = parser.parse_args()


    change_report = json.loads(
        Path(
            args.change_report
        ).read_text(
            encoding="utf-8"
        )
    )

    relationship_report = json.loads(
        Path(
            args.relationship_report
        ).read_text(
            encoding="utf-8"
        )
    )

    semantics_report = json.loads(
        Path(
            args.semantics_report
        ).read_text(
            encoding="utf-8"
        )
    )


    impacts = map_security_impact(
        change_report,
        relationship_report,
        semantics_report,
    )


    result = {

        "engine":
            "security-impact-mapper",

        "version":
            "2.0",

        "mode":
            "repository-generic",

        "security_impacts":
            impacts,

        "total_impacts":
            len(impacts),
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

                "security_impacts":
                    len(impacts),

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