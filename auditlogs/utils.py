def get_client_ip(request) -> str | None:
    """
    Return the client's IP address from a Django request, accounting for
    reverse proxies that set X-Forwarded-For.
    """
    if request is None:
        return None
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")