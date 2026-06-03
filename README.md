# ASC RCM Command Center Lite

ASC RCM Command Center Lite is a synthetic ambulatory surgery center (ASC) and
surgical revenue cycle prototype. It is intended for demonstrating command-center
workflows across scheduling, case readiness, charge capture, denial prevention,
and operational revenue cycle review using synthetic examples only.

The project is beginning a transition from Clinical RI Lite to an ASC-focused
revenue cycle command center. Existing Clinical RI Lite behavior and examples
should remain available as legacy clinical revenue integrity examples while new
ASC-specific capabilities are developed in the `asc_rcm_lite` package.

## Packages

- `asc_rcm_lite`: New top-level package for ASC RCM Command Center Lite
  functionality.
- `clinical_ri_lite`: Legacy clinical revenue integrity examples, including the
  existing AKI, sepsis, and respiratory examples and tests when present in the
  checkout.

## Compliance Boundaries

This repository is a prototype built around synthetic scenarios.

- It is not clinical software.
- It does not provide coding advice.
- It does not provide billing advice.
- It is not connected to real payers, clearinghouses, EHRs, practice management
  systems, or patient data.
- Outputs should be treated as operational workflow examples only and must not be
  used for patient care, claims submission, reimbursement decisions, or compliance
  determinations.

See `docs/COMPLIANCE_GUARDRAILS.md` for the project guardrails.
