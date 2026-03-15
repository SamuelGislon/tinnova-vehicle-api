def assert_standard_error_payload(
    response,
    *,
    expected_status: int,
    expected_code: str,
):
    assert response.status_code == expected_status
    assert response.headers.get("x-request-id")

    payload = response.json()
    assert list(payload.keys()) == ["error"]

    error = payload["error"]
    assert error["code"] == expected_code
    assert "message" in error
    assert "details" in error
    assert "path" in error
    assert "method" in error
    assert "timestamp" in error
    assert "request_id" in error

    return error
