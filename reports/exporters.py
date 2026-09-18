"""
CSV export helpers.

Each exporter receives a Django QuerySet and yields CSV rows as strings.
Views wrap these in a StreamingHttpResponse for large datasets.
"""

import csv


class Echo:
    """An object that implements just the write method of the file-like interface."""

    def write(self, value):
        return value


def _stream(rows):
    """Yield CSV lines from an iterable of row-iterables."""
    writer = csv.writer(Echo())
    for row in rows:
        yield writer.writerow(row)


# ---------------------------------------------------------------------------
# Application status report
# ---------------------------------------------------------------------------
def applications_by_status(applications):
    yield from _stream(
        [
            [
                "Reference",
                "Student",
                "JAMB number",
                "Admission number",
                "Department",
                "Programme",
                "Session",
                "Status",
                "Submitted",
                "Approved",
                "Rejected",
                "Reviewing officer",
            ],
            *(
                [
                    str(a.reference),
                    a.student.get_full_name() or a.student.username,
                    a.admission_record.jamb_number,
                    a.admission_record.admission_number or "",
                    a.admission_record.department.name,
                    a.admission_record.programme.name,
                    a.session.name,
                    a.get_status_display(),
                    a.submitted_at.isoformat() if a.submitted_at else "",
                    a.approved_at.isoformat() if a.approved_at else "",
                    a.rejected_at.isoformat() if a.rejected_at else "",
                    (
                        a.reviewing_officer.get_full_name()
                        or a.reviewing_officer.username
                        if a.reviewing_officer
                        else ""
                    ),
                ]
                for a in applications.iterator()
            ),
        ]
    )


# ---------------------------------------------------------------------------
# Department report
# ---------------------------------------------------------------------------
def applications_by_department(rows):
    """
    rows is a list of dicts:
        {department, total, approved, rejected, pending}
    """
    yield from _stream(
        [
            ["Department", "Total", "Approved", "Rejected", "Pending"],
            *(
                [
                    r["department"],
                    r["total"],
                    r["approved"],
                    r["rejected"],
                    r["pending"],
                ]
                for r in rows
            ),
        ]
    )


# ---------------------------------------------------------------------------
# Approved students
# ---------------------------------------------------------------------------
def approved_students(applications):
    yield from _stream(
        [
            [
                "Reference",
                "Student",
                "JAMB number",
                "Admission number",
                "Department",
                "Programme",
                "Session",
                "Approved on",
                "Verification code",
            ],
            *(
                [
                    str(a.reference),
                    a.student.get_full_name() or a.student.username,
                    a.admission_record.jamb_number,
                    a.admission_record.admission_number or "",
                    a.admission_record.department.name,
                    a.admission_record.programme.name,
                    a.session.name,
                    a.approved_at.isoformat() if a.approved_at else "",
                    (
                        getattr(a, "confirmation_slip", None).verification_code
                        if hasattr(a, "confirmation_slip")
                        else ""
                    ),
                ]
                for a in applications.iterator()
            ),
        ]
    )


# ---------------------------------------------------------------------------
# Rejected applications
# ---------------------------------------------------------------------------
def rejected_applications(applications):
    yield from _stream(
        [
            [
                "Reference",
                "Student",
                "JAMB number",
                "Department",
                "Programme",
                "Session",
                "Rejected on",
                "Reason",
            ],
            *(
                [
                    str(a.reference),
                    a.student.get_full_name() or a.student.username,
                    a.admission_record.jamb_number,
                    a.admission_record.department.name,
                    a.admission_record.programme.name,
                    a.session.name,
                    a.rejected_at.isoformat() if a.rejected_at else "",
                    a.rejection_reason or "",
                ]
                for a in applications.iterator()
            ),
        ]
    )


# ---------------------------------------------------------------------------
# Pending review
# ---------------------------------------------------------------------------
def pending_review(applications):
    yield from _stream(
        [
            [
                "Reference",
                "Student",
                "JAMB number",
                "Department",
                "Programme",
                "Session",
                "Status",
                "Submitted",
                "Reviewing officer",
            ],
            *(
                [
                    str(a.reference),
                    a.student.get_full_name() or a.student.username,
                    a.admission_record.jamb_number,
                    a.admission_record.department.name,
                    a.admission_record.programme.name,
                    a.session.name,
                    a.get_status_display(),
                    a.submitted_at.isoformat() if a.submitted_at else "",
                    (
                        a.reviewing_officer.get_full_name()
                        or a.reviewing_officer.username
                        if a.reviewing_officer
                        else ""
                    ),
                ]
                for a in applications.iterator()
            ),
        ]
    )


# ---------------------------------------------------------------------------
# Document verification
# ---------------------------------------------------------------------------
def document_verification(documents):
    yield from _stream(
        [
            [
                "Application",
                "Student",
                "Document type",
                "Status",
                "Uploaded",
                "Reviewed by",
                "Reviewed on",
                "Comment",
            ],
            *(
                [
                    str(d.application.reference),
                    d.application.student.get_full_name() or d.application.student.username,
                    d.document_type.name,
                    d.get_status_display(),
                    d.uploaded_at.isoformat() if d.uploaded_at else "",
                    (
                        d.reviewed_by.get_full_name() or d.reviewed_by.username
                        if d.reviewed_by
                        else ""
                    ),
                    d.reviewed_at.isoformat() if d.reviewed_at else "",
                    d.review_comment or "",
                ]
                for d in documents.iterator()
            ),
        ]
    )