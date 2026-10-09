# Synthetic contract corpus

All documents here are **synthetic, authored for this repo by Agent B (2026-10-09)**. Names, countries, duties, dates and commercial terms are fictional test data, not legal advice, authoritative law or counsel-approved templates. TXT is canonical; tests generate DOCX/PDF from these texts without external/private files.

Expected labels below deliberately form a small deterministic benchmark, not a legal-domain accuracy claim. Precision/recall is computed from expected versus produced labels/fields/obligation actors and recorded in EVIDENCE_B.

| Fixture | Expected clause types | Expected parties | Expected obligations (actor/action class) |
|---|---|---|---|
| nda.txt | parties, definition, confidentiality, term, notice, governing_law | Alpha Labs, Beta Research | Recipient/prohibition; Recipient/duty |
| msa.txt | parties, services, payment, liability, termination, governing_law | Atlas Buyer, Beacon Supplier | Supplier/duty; Buyer/duty; Buyer/right |
| saas.txt | parties, services, payment, renewal, notice, data_protection | Cloud Vendor, Delta Customer | Customer/duty; Provider/duty; Customer/prohibition |
| lease.txt | parties, term, payment, maintenance, termination, governing_law | Elm Landlord, Fern Tenant | Tenant/duty; Landlord/duty; Tenant/right |

Expected definition: NDA `Confidential Information`. Expected term date: NDA 2027-01-01. Expected renewal: SaaS annual renewal unless notice. Expected notice: NDA 30 days, SaaS 60 days. Expected payment deadline phrases: MSA within 30 days of invoice, SaaS within 15 days of invoice, lease on the first day of each month. Governing-law values are extracted source text only (Fictional Territory), never applicability assertions.
