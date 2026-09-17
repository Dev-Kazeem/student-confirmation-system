def notifications(request):
    """
    Add `unread_notifications_count` to every template context for
    authenticated users.
    """
    if not getattr(request, "user", None) or not request.user.is_authenticated:
        return {"unread_notifications_count": 0}
    count = request.user.notifications.filter(is_read=False).count()
    return {"unread_notifications_count": count}