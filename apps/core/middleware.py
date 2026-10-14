from django.utils.cache import add_never_cache_headers


class PrivateResponseMiddleware:
    """Do not leave private assessment or recovery responses in browser/proxy caches."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        private_request = request.user.is_authenticated or request.path.startswith(
            ("/accounts/", "/practicals/integrations/")
        )
        response = self.get_response(request)
        if private_request and not request.path.startswith("/static/"):
            add_never_cache_headers(response)
        response["X-Content-Type-Options"] = "nosniff"
        policy = "frame-ancestors 'none'; base-uri 'self'; object-src 'none'"
        # Approved launch forms redirect to external resources; do not block them.
        if request.path.startswith("/accounts/"):
            policy += "; form-action 'self'"
        response["Content-Security-Policy"] = policy
        return response
