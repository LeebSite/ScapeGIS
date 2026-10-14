"""
Pytest configuration and compatibility shims for test execution.
Bridges Starlette TestClient with HTTPX >= 0.28.0 (required by google-genai).
"""
import httpx

# HTTPX 0.28+ removed the deprecated `app=` parameter from Client.__init__ in favor of `transport=ASGITransport(app=app)`.
# Starlette < 0.40 passes `app=app` directly. This compatibility hook adapts the call transparently.
_original_httpx_client_init = httpx.Client.__init__

def _compat_httpx_client_init(self, *args, **kwargs):
    if "app" in kwargs:
        app = kwargs.pop("app")
        if "transport" not in kwargs or kwargs["transport"] is None:
            kwargs["transport"] = httpx.ASGITransport(app=app)
    return _original_httpx_client_init(self, *args, **kwargs)

httpx.Client.__init__ = _compat_httpx_client_init
