import threading

_thread_locals = threading.local()


def get_current_request():
    return getattr(_thread_locals, "request", None)


class AuditLogMiddleware:
    """Stashes the current request in thread-local storage so signal
    handlers deep in the ORM (e.g. Product post_save) can still resolve
    request.user / IP without every caller having to pass it through."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _thread_locals.request = request
        try:
            response = self.get_response(request)
        finally:
            _thread_locals.request = None
        return response
