# Data + Policy Plan

## V1
Use synthetic household/case data with deterministic ground truth.

Use public sources only to ground workflow, terminology, realistic changes, and the policy library.

Official starting points:
- California CDSS Eligibility & Assistance Standards manual
  https://www.cdss.ca.gov/inforesources/letters-regulations/legislation-and-regulations/calworks-calfresh-regulations/eligibility-and-assistance-standards
- California CDSS forms
  https://www.cdss.ca.gov/inforesources/forms-brochures
- USDA SNAP
  https://www.fns.usda.gov/snap
- Census SIPP 2025
  https://www.census.gov/data/datasets/2025/demo/sipp/2025-data.html

Do NOT make ingestion of SIPP/SNAP QC a V1 dependency.

## Frozen policy library
Each item stores:
- id
- title
- source
- source_url
- jurisdiction
- effective_date
- topic
- authority_level
- text/excerpt

Freeze the corpus by version/date so runs are comparable.

Never fabricate text and label it as real law. If a synthetic benchmark instruction is needed, mark it `benchmark_synthetic_instruction`.
