import csv
from io import BytesIO
from xml.sax.saxutils import escape

from django.db.models import Count
from django.http import HttpResponse
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from apps.accounts.models import User
from apps.academics.models import CourseOffering
from apps.practicals.models import Assessment, PracticalSubmission, PracticalTask


def platform_metrics():
    return {
        "active_users": User.objects.filter(approval_status=User.ApprovalStatus.ACTIVE).count(),
        "active_students": User.objects.filter(
            role=User.Role.STUDENT, approval_status=User.ApprovalStatus.ACTIVE
        ).count(),
        "active_lecturers": User.objects.filter(
            role=User.Role.LECTURER, approval_status=User.ApprovalStatus.ACTIVE
        ).count(),
        "active_offerings": CourseOffering.objects.filter(is_active=True).count(),
        "published_tasks": PracticalTask.objects.filter(status=PracticalTask.Status.PUBLISHED).count(),
        "submitted_attempts": PracticalSubmission.objects.exclude(
            status=PracticalSubmission.Status.DRAFT
        ).count(),
        "awaiting_review": PracticalSubmission.objects.filter(
            status__in=[PracticalSubmission.Status.SUBMITTED, PracticalSubmission.Status.RESUBMITTED]
        ).count(),
        "released_results": Assessment.objects.filter(status=Assessment.Status.RELEASED).count(),
    }


def filter_submissions(queryset, cleaned):
    if cleaned.get("offering"):
        queryset = queryset.filter(task__offering=cleaned["offering"])
    if cleaned.get("status"):
        queryset = queryset.filter(status=cleaned["status"])
    if cleaned.get("date_from"):
        queryset = queryset.filter(created_at__date__gte=cleaned["date_from"])
    if cleaned.get("date_to"):
        queryset = queryset.filter(created_at__date__lte=cleaned["date_to"])
    return queryset


def _safe_csv(value):
    text = "" if value is None else str(value)
    suspicious = text.startswith(("\t", "\r", "\n")) or text.lstrip(" \t\r\n").startswith(("=", "+", "-", "@"))
    return f"'{text}" if suspicious else text


def _csv_response(filename, headers, rows):
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    response.write("\ufeff")
    writer = csv.writer(response)
    writer.writerow(headers)
    for row in rows:
        writer.writerow([_safe_csv(value) for value in row])
    return response


def users_csv_response():
    users = User.objects.select_related(
        "academic_profile__faculty", "academic_profile__department", "academic_profile__programme"
    ).all()

    def rows():
        for user in users:
            profile = getattr(user, "academic_profile", None)
            yield (
                user.full_name,
                user.email,
                user.get_role_display(),
                user.get_approval_status_display(),
                profile.student_or_staff_id if profile else "",
                profile.faculty.name if profile else "",
                profile.department.name if profile else "",
                profile.programme.name if profile and profile.programme else "",
                timezone.localtime(user.date_joined).strftime("%Y-%m-%d %H:%M"),
            )

    return _csv_response(
        "atu-users.csv",
        ["Full name", "Email", "Role", "Status", "Academic ID", "Faculty", "Department", "Programme", "Registered"],
        rows(),
    )


def submissions_csv_response(submissions):
    def rows():
        for submission in submissions:
            assessment = getattr(submission, "assessment", None)
            yield (
                submission.student.full_name,
                submission.student.email,
                submission.task.offering.course.code,
                submission.task.title,
                submission.attempt_number,
                submission.get_status_display(),
                submission.submitted_at and timezone.localtime(submission.submitted_at).strftime("%Y-%m-%d %H:%M"),
                submission.resource_version,
                submission.run_session_id,
                submission.get_run_status_display(),
                assessment.score if assessment and assessment.status == Assessment.Status.RELEASED else "",
                assessment.released_at and timezone.localtime(assessment.released_at).strftime("%Y-%m-%d %H:%M") if assessment and assessment.status == Assessment.Status.RELEASED else "",
            )

    return _csv_response(
        "atu-submissions.csv",
        ["Student", "Email", "Course", "Task", "Attempt", "Status", "Submitted", "Resource version", "Run/session ID", "Run status", "Released score", "Released at"],
        rows(),
    )


def audit_csv_response(events):
    return _csv_response(
        "atu-audit-events.csv",
        ["Timestamp", "Action", "Actor", "Actor email", "Target type", "Target ID", "IP address"],
        (
            (
                timezone.localtime(event.created_at).strftime("%Y-%m-%d %H:%M:%S"),
                event.action,
                event.actor.full_name if event.actor else "System",
                event.actor.email if event.actor else "",
                event.target_type,
                event.target_id,
                event.ip_address or "",
            )
            for event in events
        ),
    )


def summary_pdf_response(*, development_label=False):
    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=16 * mm,
        leftMargin=16 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title="ATU Virtual Laboratory Administrative Summary",
        author="ATU Virtual Laboratory Management Platform",
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#0b2948"),
        alignment=TA_CENTER,
        spaceAfter=8,
    )
    small = ParagraphStyle("Small", parent=styles["BodyText"], fontSize=8, leading=10)
    story = [
        Paragraph("ATU Virtual Laboratory Management Platform", title_style),
        Paragraph("Administrative Summary Report", styles["Heading2"]),
        Paragraph(
            f"Generated {timezone.localtime():%d %B %Y at %H:%M} (Africa/Accra)",
            styles["BodyText"],
        ),
    ]
    if development_label:
        story.append(
            Paragraph(
                "DEVELOPMENT PREVIEW - DEMONSTRATION DATA",
                ParagraphStyle("Demo", parent=styles["Heading3"], textColor=colors.HexColor("#a33a00")),
            )
        )
    story.append(Spacer(1, 7 * mm))
    metrics = platform_metrics()
    metric_data = [
        [Paragraph(label.replace("_", " ").title(), small) for label in metrics],
        [str(value) for value in metrics.values()],
    ]
    metric_table = Table(metric_data, repeatRows=1, colWidths=[32 * mm] * len(metrics))
    metric_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0b2948")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 1), (-1, 1), 14),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#b9c5d1")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    story.extend([metric_table, Spacer(1, 8 * mm), Paragraph("Submission status", styles["Heading2"])])
    statuses = dict(PracticalSubmission.Status.choices)
    counts = {
        item["status"]: item["total"]
        for item in PracticalSubmission.objects.values("status").annotate(total=Count("id"))
    }
    status_data = [["Status", "Attempts"]] + [[statuses[key], counts.get(key, 0)] for key in statuses]
    status_table = Table(status_data, colWidths=[70 * mm, 35 * mm], repeatRows=1)
    status_table.setStyle(_standard_table_style())
    story.extend([status_table, PageBreak(), Paragraph("Recent submission activity", styles["Heading2"])])
    submissions = PracticalSubmission.objects.select_related(
        "student", "task__offering__course"
    ).order_by("-created_at")[:25]
    submission_data = [["Student", "Course", "Task", "Attempt", "Status", "Submitted"]]
    for item in submissions:
        submission_data.append(
            [
                Paragraph(escape(item.student.full_name), small),
                item.task.offering.course.code,
                Paragraph(escape(item.task.title), small),
                str(item.attempt_number),
                item.get_status_display(),
                timezone.localtime(item.submitted_at).strftime("%d %b %Y %H:%M") if item.submitted_at else "Draft",
            ]
        )
    submission_table = Table(
        submission_data,
        colWidths=[42 * mm, 25 * mm, 78 * mm, 18 * mm, 35 * mm, 42 * mm],
        repeatRows=1,
    )
    submission_table.setStyle(_standard_table_style())
    story.append(submission_table)
    document.build(story, onFirstPage=_page_footer, onLaterPages=_page_footer)
    response = HttpResponse(buffer.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="atu-administrative-summary.pdf"'
    return response


def _standard_table_style():
    return TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#145ca8")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#b9c5d1")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f3f7fb")]),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]
    )


def _page_footer(canvas, document):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#536273"))
    canvas.drawString(16 * mm, 9 * mm, "ATU Virtual Laboratory - Administrative use")
    canvas.drawRightString(landscape(A4)[0] - 16 * mm, 9 * mm, f"Page {document.page}")
    canvas.restoreState()
