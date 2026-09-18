from django.core.paginator import Paginator
from django.shortcuts import render

from accounts.decorators import admin_required
from accounts.models import User

from .models import AuditLog


@admin_required
def auditlog_list(request):
    qs = AuditLog.objects.select_related("user").order_by("-created_at")

    q = request.GET.get("q", "").strip()
    action = request.GET.get("action", "").strip()
    user_id = request.GET.get("user", "").strip()
    date_from = request.GET.get("from", "").strip()
    date_to = request.GET.get("to", "").strip()

    if q:
        qs = qs.filter(description__icontains=q)
    if action:
        qs = qs.filter(action=action)
    if user_id:
        qs = qs.filter(user_id=user_id)
    if date_from:
        qs = qs.filter(created_at__date__gte=date_from)
    if date_to:
        qs = qs.filter(created_at__date__lte=date_to)

    paginator = Paginator(qs, 50)
    page = paginator.get_page(request.GET.get("page"))

    return render(
        request,
        "auditlogs/list.html",
        {
            "page": page,
            "total": qs.count(),
            "actions": AuditLog.Action.choices,
            "users": User.objects.order_by("username"),
            "filters": {
                "q": q,
                "action": action,
                "user": user_id,
                "from": date_from,
                "to": date_to,
            },
        },
    )


@admin_required
def auditlog_detail(request, pk):
    from django.shortcuts import get_object_or_404

    log = get_object_or_404(AuditLog.objects.select_related("user"), pk=pk)
    return render(request, "auditlogs/detail.html", {"log": log})