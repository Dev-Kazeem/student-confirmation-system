"""
CSV importer for AdmissionRecord.

Expected CSV columns (header row required):
    jamb_number, student_name, admission_number, department_code, programme_code, session_name

- department_code and programme_code must match existing Department.code / Programme.code
- session_name must match AdmissionSession.name
- Rows with unknown codes are skipped and reported.
"""

import csv
import io

from django.db import transaction

from .models import AdmissionRecord, AdmissionSession, Department, Programme


def import_admission_records(file_obj) -> dict:
    """
    Import admission records from an uploaded CSV file.

    Returns:
        {
            "created": int,
            "updated": int,
            "errors": [ "row 3: unknown department 'XYZ'", ... ],
        }
    """
    content = file_obj.read()
    if isinstance(content, bytes):
        content = content.decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(content))

    required_headers = {
        "jamb_number",
        "student_name",
        "admission_number",
        "department_code",
        "programme_code",
        "session_name",
    }
    if not required_headers.issubset(set(reader.fieldnames or [])):
        missing = ", ".join(sorted(required_headers - set(reader.fieldnames or [])))
        return {"created": 0, "updated": 0, "errors": [f"Missing columns: {missing}"]}

    created = updated = 0
    errors: list[str] = []

    # Preload lookup tables
    dept_by_code = {d.code.lower(): d for d in Department.objects.all()}
    prog_by_code = {p.code.lower(): p for p in Programme.objects.all()}
    session_by_name = {s.name: s for s in AdmissionSession.objects.all()}

    with transaction.atomic():
        for idx, row in enumerate(reader, start=2):  # header is line 1
            jamb = (row.get("jamb_number") or "").strip()
            name = (row.get("student_name") or "").strip()
            adm = (row.get("admission_number") or "").strip() or None
            dept_code = (row.get("department_code") or "").strip().lower()
            prog_code = (row.get("programme_code") or "").strip().lower()
            session_name = (row.get("session_name") or "").strip()

            if not (jamb and name and dept_code and prog_code and session_name):
                errors.append(f"row {idx}: missing required fields")
                continue

            dept = dept_by_code.get(dept_code)
            prog = prog_by_code.get(prog_code)
            session = session_by_name.get(session_name)

            if not dept:
                errors.append(f"row {idx}: unknown department code '{dept_code}'")
                continue
            if not prog:
                errors.append(f"row {idx}: unknown programme code '{prog_code}'")
                continue
            if not session:
                errors.append(f"row {idx}: unknown session '{session_name}'")
                continue

            obj, is_created = AdmissionRecord.objects.update_or_create(
                jamb_number=jamb,
                defaults={
                    "student_name": name,
                    "admission_number": adm,
                    "department": dept,
                    "programme": prog,
                    "session": session,
                },
            )
            if is_created:
                created += 1
            else:
                updated += 1

    return {"created": created, "updated": updated, "errors": errors}