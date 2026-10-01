# Continuous Security Verification for Evolving Microservice Systems

A repository-aware security verification framework for detecting security-relevant changes in evolving microservice architectures and selectively verifying the affected security properties.

## Research Problem

Microservice systems continuously evolve through source-code, API-contract, configuration, and dependency changes.

Traditional security validation may repeatedly analyze the entire system even when only a small part has changed.

This project investigates a repository-aware approach:

Repository Change
→ Change Understanding
→ Service/Relationship Analysis
→ Security Impact Mapping
→ Evidence Collection
→ Targeted Security Verification

## Subject System

The framework is evaluated using Google's Online Boutique microservice application.

The subject system contains multiple independently deployed services communicating through service interfaces.

The Online Boutique repository is kept separate from this framework.

## Framework Architecture

The framework currently contains:

- Change Extraction Engine
- Change Semantic Analyzer
- Relationship Builder
- Security Impact Mapper
- Security Property Selector
- Evidence Collector
- Security Rule Verifier
- Targeted Verifier
- Continuous Verification Pipeline

## Experimental Evaluation

Four controlled repository-evolution experiments were performed.

| Experiment | Change Type | Result |
|---|---|---|
| E1 | Authorization regression | FAIL |
| E2 | Transaction validation | PASS |
| E3 | API contract evolution | REVIEW |
| E4 | Documentation-only change | NOT TARGETED |

### E1 — Authorization Regression

The payment authorization condition was changed from:

`amount > 0`

to:

`amount >= 0`

The framework detected that the security condition was weakened and reported a verification failure.

### E2 — Transaction Evolution

A transaction-related validation change was introduced in the payment service.

The framework identified the affected transaction security property and produced a PASS result.

### E3 — API Contract Evolution

The PaymentService protobuf contract was changed.

The framework identified the interface artifact and mapped the change to security-relevant service interaction and contract properties.

The change was marked for REVIEW.

### E4 — Unrelated Change

A documentation-only README modification was introduced.

The framework generated zero security-rule checks, demonstrating that the change was not targeted for security verification.

## Project Structure

```text
security-verification/
│
├── engine/
│   ├── change_extractor.py
│   ├── change_semantics.py
│   ├── relationship_builder.py
│   ├── security_impact_mapper.py
│   ├── property_selector.py
│   ├── security_properties.py
│   ├── security_property_model.py
│   ├── evidence_collector.py
│   ├── security_rule_verifier.py
│   ├── targeted_verifier.py
│   └── pipeline.py
│
├── output/
│   └── experimental_results.json
│
├── .gitignore
└── README.md