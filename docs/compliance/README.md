# Compliance Pack

This folder is the working compliance pack for Omni Logistics ZW (Pty) Ltd.

It is not legal advice and should be reviewed by legal/compliance counsel before formal submission to the Information Regulator or before publication as a final policy pack.

## Purpose
- Centralise the documents and templates needed to answer POPIA and PAIA self-assessments.
- Separate what the platform already does from what the organisation must prove through governance records.
- Give the team an evidence pack that can be improved over time instead of answering questionnaires ad hoc.

## Documents in this folder
- `01_gap_matrix.md`: current high-level readiness view and immediate priorities.
- `02_paia_manual_draft.md`: working draft structure for a PAIA manual.
- `03_data_subject_request_procedure.md`: operating procedure for access, correction, deletion, objection, and related requests.
- `04_security_incident_response_plan.md`: working security-compromise and breach-response playbook.
- `05_records_retention_schedule.md`: starter retention schedule.
- `06_processing_activities_register_template.md`: template for a record of processing activities.
- `07_operator_and_processor_checklist.md`: minimum checklist for operator / processor agreements.
- `08_data_subject_request_register_template.md`: register template for subject-rights and PAIA-type requests.
- `09_security_incident_register_template.md`: register template for incidents and compromises.
- `10_compliance_evidence_register.md`: evidence index for audit and regulator preparation.

## Immediate priorities
1. Finalise a South Africa-aligned PAIA manual.
2. Finalise a POPIA-aligned privacy notice and subject-rights process.
3. Start and maintain the processing activities register.
4. Start and maintain the security incident register.
5. Finalise operator agreements with POPIA clauses.
6. Keep evidence of training, reviews, and annual updates.

## Related app evidence
These platform controls already support compliance evidence:
- Role-based access control: `/Users/tinotendamutami/omniv3/backend/app/core/auth.py`
- Immutable audit logging: `/Users/tinotendamutami/omniv3/backend/app/services/admin_activity.py`
- Enquiry consent capture: `/Users/tinotendamutami/omniv3/backend/app/api/routes/enquiries.py`
- Public privacy notice: `/Users/tinotendamutami/omniv3/client-web/src/routes/privacy/+page.svelte`
- Public access-to-information page: `/Users/tinotendamutami/omniv3/client-web/src/routes/access-to-information/+page.svelte`
