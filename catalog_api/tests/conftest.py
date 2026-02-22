import pytest

try:
    import respx
    # Quick probe to ensure respx works with this httpx build in this env.
    RESPX_OK = True
    try:
        import httpx
        with respx.mock as m:
            m.get("https://example.com/").respond(200, json={"ok": 1})
            r = httpx.get("https://example.com/")
            # if r raised or status not 200, consider respx unusable
            if r.status_code != 200:
                RESPX_OK = False
    except Exception:
        RESPX_OK = False

    @pytest.fixture
    def respx_mock():
        """Provide a respx mocker fixture for HTTPX mocking. Skips if respx appears unusable."""
        if not RESPX_OK:
            pytest.skip("respx present but not usable in this environment; skip mocked HTTP tests")
        with respx.mock as m:
            yield m
except Exception:
    @pytest.fixture
    def respx_mock():
        pytest.skip("respx not installed; install test dependencies to run mocked tests")
