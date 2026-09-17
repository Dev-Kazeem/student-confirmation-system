from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .models import Notification


@login_required
def notification_list(request):
    qs = request.user.notifications.order_by("-created_at")
    paginator = Paginator(qs, 20)
    page = paginator.get_page(request.GET.get("page"))
    return render(request, "notifications/list.html", {"page": page})


@login_required
def mark_read(request, pk):
    n = get_object_or_404(Notification, pk=pk, recipient=request.user)
    if not n.is_read:
        n.is_read = True
        n.save(update_fields=["is_read"])
    if n.link_url:
        return redirect(n.link_url)
    return redirect("notifications:list")


@login_required
def mark_all_read(request):
    if request.method != "POST":
        return redirect("notifications:list")
    updated = request.user.notifications.filter(is_read=False).update(is_read=True)
    messages.success(request, f"Marked {updated} notification(s) as read.")
    return redirect("notifications:list")