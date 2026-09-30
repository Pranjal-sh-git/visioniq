"""Comprehensive security and SSRF protection unit tests for VisionIQ.

Covers:
1. localhost / 127.0.0.1 / ::1
2. RFC1918 private IP ranges (10.x, 172.16.x, 192.168.x)
3. Cloud metadata endpoints (169.254.169.254, metadata.google.internal)
4. Malicious redirect targets (open redirect pointing to localhost / metadata)
5. Unsupported schemes (file://, ftp://, gopher://, dict://)
6. Oversized response payload rejection (>10MB)
7. Request timeout handling
8. Valid public HTTPS image fetching and end-to-end identify_product flow
"""

import io
from unittest.mock import MagicMock, patch
from PIL import Image
import pytest
import requests

from services.security import (
    SSRFProtectionError,
    is_ip_blocked,
    validate_url,
    safe_fetch_image,
    DEFAULT_MAX_IMAGE_SIZE_BYTES,
)
from services.product_search.embeddings import load_image
from services.vision.open_world_identifier import _image_to_data_uri


def create_dummy_jpeg_bytes() -> bytes:
    """Creates a minimal valid JPEG image in bytes."""
    img = Image.new("RGB", (32, 32), color=(255, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


# ============================================================================
# 1. IP Range & Hostname Validation Tests
# ============================================================================

@pytest.mark.parametrize(
    "ip_str, expected_blocked",
    [
        ("127.0.0.1", True),
        ("127.0.0.254", True),
        ("::1", True),
        ("10.0.0.1", True),
        ("10.255.255.255", True),
        ("172.16.0.1", True),
        ("172.31.255.255", True),
        ("192.168.1.1", True),
        ("192.168.0.254", True),
        ("169.254.169.254", True),
        ("169.254.1.1", True),
        ("0.0.0.0", True),
        ("::", True),
        ("224.0.0.1", True),
        ("240.0.0.1", True),
        ("::ffff:127.0.0.1", True),
        ("::ffff:169.254.169.254", True),
        ("::ffff:10.0.0.1", True),
        ("8.8.8.8", False),
        ("1.1.1.1", False),
        ("93.184.216.34", False),  # example.com
    ],
)
def test_is_ip_blocked(ip_str: str, expected_blocked: bool):
    """Verifies that all restricted, loopback, private, and metadata IPs are blocked."""
    assert is_ip_blocked(ip_str) == expected_blocked


# ============================================================================
# 2. URL Scheme & Hostname Rejection Tests
# ============================================================================

@pytest.mark.parametrize(
    "forbidden_url",
    [
        "file:///etc/passwd",
        "file:///C:/Windows/win.ini",
        "ftp://ftp.example.com/image.jpg",
        "gopher://127.0.0.1:70/",
        "dict://127.0.0.1:11211/stat",
        "data:text/plain;base64,SGVsbG8=",
        "http://localhost/image.png",
        "http://localhost:8000/secret.jpg",
        "http://127.0.0.1/admin.png",
        "http://127.0.0.1:8080/test.jpg",
        "http://[::1]/test.jpg",
        "http://169.254.169.254/latest/meta-data/",
        "http://metadata.google.internal/computeMetadata/v1/",
        "http://10.0.0.5:8080/internal.png",
        "http://192.168.1.100/router.jpg",
        "http://172.16.5.10/database.png",
    ],
)
def test_validate_url_rejects_dangerous_targets(forbidden_url: str):
    """Verifies that validate_url strictly rejects non-HTTP schemes and private/metadata destinations."""
    with pytest.raises(SSRFProtectionError):
        validate_url(forbidden_url)


# ============================================================================
# 3. Malicious Redirect SSRF Tests
# ============================================================================

def test_safe_fetch_image_blocks_redirect_to_localhost():
    """Verifies that a public URL redirecting to 127.0.0.1 is blocked at the redirect hop."""
    mock_session = MagicMock()

    # Step 1: Initial public URL returns 302 redirecting to http://127.0.0.1/evil.jpg
    redirect_resp = MagicMock()
    redirect_resp.status_code = 302
    redirect_resp.headers = {"Location": "http://127.0.0.1/evil.jpg"}

    mock_session.get.return_value = redirect_resp

    with patch("services.security.requests.Session", return_value=mock_session):
        with patch("services.security.socket.getaddrinfo") as mock_dns:
            # First resolution for public domain returns public IP
            mock_dns.side_effect = [
                [(2, 1, 6, "", ("93.184.216.34", 80))],
                [(2, 1, 6, "", ("127.0.0.1", 80))],
            ]

            with pytest.raises(SSRFProtectionError) as exc_info:
                safe_fetch_image("http://public-site.com/redirect-to-localhost.jpg")

            assert "private, loopback, or metadata" in str(exc_info.value) or "blocked" in str(exc_info.value)


def test_safe_fetch_image_blocks_redirect_to_cloud_metadata():
    """Verifies that a redirect targeting 169.254.169.254 is caught and blocked."""
    mock_session = MagicMock()

    redirect_resp = MagicMock()
    redirect_resp.status_code = 301
    redirect_resp.headers = {"Location": "http://169.254.169.254/latest/meta-data/"}

    mock_session.get.return_value = redirect_resp

    with patch("services.security.requests.Session", return_value=mock_session):
        with patch("services.security.socket.getaddrinfo") as mock_dns:
            mock_dns.side_effect = [
                [(2, 1, 6, "", ("93.184.216.34", 80))],
                [(2, 1, 6, "", ("169.254.169.254", 80))],
            ]

            with pytest.raises(SSRFProtectionError) as exc_info:
                safe_fetch_image("http://public-site.com/redirect-to-meta.jpg")

            assert "private, loopback, or metadata" in str(exc_info.value) or "blocked" in str(exc_info.value)


# ============================================================================
# 4. Oversized Payload & DoS Protection Tests
# ============================================================================

def test_safe_fetch_image_rejects_oversized_content_length():
    """Verifies that responses with Content-Length > 10MB are rejected immediately before download."""
    mock_session = MagicMock()
    resp = MagicMock()
    resp.status_code = 200
    resp.headers = {"Content-Length": str(15 * 1024 * 1024)}  # 15 MB

    mock_session.get.return_value = resp

    with patch("services.security.requests.Session", return_value=mock_session):
        with patch("services.security.socket.getaddrinfo", return_value=[(2, 1, 6, "", ("93.184.216.34", 80))]):
            with pytest.raises(SSRFProtectionError) as exc_info:
                safe_fetch_image("http://public-site.com/huge-image.jpg")

            assert "exceeds maximum limit" in str(exc_info.value)


def test_safe_fetch_image_rejects_oversized_streaming_chunks():
    """Verifies that streaming chunks exceeding max_size_bytes abort immediately."""
    mock_session = MagicMock()
    resp = MagicMock()
    resp.status_code = 200
    resp.headers = {}  # No Content-Length provided
    # Return 11 chunks of 1MB each
    resp.iter_content.return_value = [b"A" * (1024 * 1024) for _ in range(11)]

    mock_session.get.return_value = resp

    with patch("services.security.requests.Session", return_value=mock_session):
        with patch("services.security.socket.getaddrinfo", return_value=[(2, 1, 6, "", ("93.184.216.34", 80))]):
            with pytest.raises(SSRFProtectionError) as exc_info:
                safe_fetch_image("http://public-site.com/chunked-bomb.jpg")

            assert "exceeded maximum allowed size" in str(exc_info.value)


# ============================================================================
# 5. Timeout Handling Tests
# ============================================================================

def test_safe_fetch_image_timeout_handling():
    """Verifies that connection timeouts raise a clean SSRFProtectionError."""
    mock_session = MagicMock()
    mock_session.get.side_effect = requests.exceptions.Timeout("Connection timed out after 5.0s")

    with patch("services.security.requests.Session", return_value=mock_session):
        with patch("services.security.socket.getaddrinfo", return_value=[(2, 1, 6, "", ("93.184.216.34", 80))]):
            with pytest.raises(SSRFProtectionError) as exc_info:
                safe_fetch_image("http://public-site.com/slow-endpoint.jpg")

            assert "timed out" in str(exc_info.value).lower()


# ============================================================================
# 6. Valid Public HTTPS Image Fetching Test
# ============================================================================

def test_safe_fetch_image_valid_public_https():
    """Verifies that a legitimate public HTTPS image URL is fetched and validated successfully."""
    dummy_jpeg = create_dummy_jpeg_bytes()

    mock_session = MagicMock()
    resp = MagicMock()
    resp.status_code = 200
    resp.headers = {"Content-Length": str(len(dummy_jpeg))}
    resp.iter_content.return_value = [dummy_jpeg]

    mock_session.get.return_value = resp

    with patch("services.security.requests.Session", return_value=mock_session):
        with patch("services.security.socket.getaddrinfo", return_value=[(2, 1, 6, "", ("104.16.132.229", 443))]):
            data = safe_fetch_image("https://images.unsplash.com/photo-sample.jpg")
            assert data == dummy_jpeg
            # Check load_image returns PIL image
            pil_img = load_image("https://images.unsplash.com/photo-sample.jpg")
            assert isinstance(pil_img, Image.Image)


# ============================================================================
# 7. End-to-End Image Loader Integration Tests
# ============================================================================

def test_load_image_rejects_ssrf_url():
    """Verifies that load_image in embeddings.py blocks SSRF URLs with SSRFProtectionError."""
    with pytest.raises(SSRFProtectionError):
        load_image("http://127.0.0.1:8000/secret.png")


def test_image_to_data_uri_rejects_ssrf_url():
    """Verifies that _image_to_data_uri in open_world_identifier.py blocks SSRF URLs."""
    with pytest.raises(SSRFProtectionError):
        _image_to_data_uri("http://169.254.169.254/latest/meta-data/")
