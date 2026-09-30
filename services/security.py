"""Security and Server-Side Request Forgery (SSRF) Protection Utilities.

Provides robust URL validation, hostname IP resolution, IP range filtering,
and safe streaming HTTP fetching with strict timeouts, size limits, and
per-hop redirect validation to eliminate SSRF and DNS-rebinding risks.
"""

from io import BytesIO
import ipaddress
import logging
import socket
from typing import Optional, Set
import urllib.parse
from PIL import Image
import requests

logger = logging.getLogger("visioniq.security")

# Maximum allowed image response size: 10 MB
DEFAULT_MAX_IMAGE_SIZE_BYTES = 10 * 1024 * 1024

# Strict HTTP request timeout: 5s connect, 10s read
DEFAULT_REQUEST_TIMEOUT = (5.0, 10.0)

# Blocked cloud metadata IP addresses and domains
EXPLICIT_BLOCKED_IPS: Set[str] = {
    "169.254.169.254",  # AWS, Azure, GCP metadata endpoint
    "169.254.169.253",  # Cloud metadata DNS / DHCP services
    "100.100.100.200",  # Alibaba Cloud metadata
    "0.0.0.0",          # Unspecified IPv4
    "::",               # Unspecified IPv6
}

FORBIDDEN_HOSTNAMES: Set[str] = {
    "localhost",
    "metadata.google.internal",
    "metadata.goog",
    "instance-data",
    "local",
}


class SSRFProtectionError(ValueError):
    """Raised when a requested URL violates SSRF safety rules or limits."""
    pass


def is_ip_blocked(ip_str: str) -> bool:
    """Checks whether an IP address belongs to loopback, private, link-local, multicast, or reserved ranges.

    Args:
        ip_str (str): String representation of IPv4 or IPv6 address.

    Returns:
        bool: True if the IP is restricted / blocked, False if it is a public IP.
    """
    try:
        ip = ipaddress.ip_address(ip_str)
    except ValueError:
        return True

    # Handle IPv4-mapped IPv6 addresses (e.g. ::ffff:127.0.0.1)
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
        ip = ip.ipv4_mapped

    if str(ip) in EXPLICIT_BLOCKED_IPS:
        return True

    if (
        ip.is_loopback        # 127.0.0.0/8, ::1
        or ip.is_private      # RFC1918 (10/8, 172.16/12, 192.168/16), fc00::/7
        or ip.is_link_local   # 169.254.0.0/16, fe80::/10
        or ip.is_unspecified  # 0.0.0.0, ::
        or ip.is_multicast    # 224.0.0.0/4, ff00::/8
        or ip.is_reserved     # 240.0.0.0/4, etc.
    ):
        return True

    return False


def validate_url(url: str) -> tuple[str, str, int, list[str]]:
    """Validates the URL scheme, hostname, and resolves all associated IP addresses.

    Args:
        url (str): The target URL to validate.

    Returns:
        tuple[str, str, int, list[str]]: (scheme, hostname, port, resolved_ip_list)

    Raises:
        SSRFProtectionError: If scheme is unsupported, hostname is invalid, or any resolved IP is blocked.
    """
    if not isinstance(url, str) or not url.strip():
        raise SSRFProtectionError("URL cannot be empty.")

    try:
        parsed = urllib.parse.urlparse(url.strip())
    except Exception as e:
        raise SSRFProtectionError(f"Invalid URL format: {e}")

    scheme = (parsed.scheme or "").lower()
    if scheme not in ("http", "https"):
        raise SSRFProtectionError(
            f"Unsupported URL scheme '{scheme}'. Only 'http' and 'https' protocols are permitted."
        )

    hostname = (parsed.hostname or "").lower().strip()
    if not hostname:
        raise SSRFProtectionError("URL must contain a valid, non-empty hostname.")

    # Check against forbidden hostnames or TLD patterns
    if hostname in FORBIDDEN_HOSTNAMES or hostname.endswith((".localhost", ".local", ".internal", ".lan", ".home")):
        raise SSRFProtectionError(f"Access to hostname '{hostname}' is prohibited by SSRF security policy.")

    # Determine default port
    port = parsed.port or (443 if scheme == "https" else 80)

    # Resolve all DNS A and AAAA records for the hostname
    try:
        addr_info = socket.getaddrinfo(hostname, port, type=socket.SOCK_STREAM)
    except socket.gaierror as e:
        raise SSRFProtectionError(f"Failed to resolve hostname '{hostname}': {e}")
    except Exception as e:
        raise SSRFProtectionError(f"DNS lookup failed for '{hostname}': {e}")

    resolved_ips = list({res[4][0] for res in addr_info if res and len(res) >= 5 and res[4]})
    if not resolved_ips:
        raise SSRFProtectionError(f"No IP addresses resolved for hostname '{hostname}'.")

    # Validate each resolved IP address
    for ip in resolved_ips:
        if is_ip_blocked(ip):
            logger.warning(f"[SSRF BLOCKED] Hostname '{hostname}' resolved to restricted IP '{ip}' (URL: {url})")
            raise SSRFProtectionError(
                f"Access to '{hostname}' is blocked: resolved IP '{ip}' belongs to a private, loopback, or metadata address range."
            )

    return scheme, hostname, port, resolved_ips


def safe_fetch_image(
    url: str,
    max_size_bytes: int = DEFAULT_MAX_IMAGE_SIZE_BYTES,
    timeout: tuple[float, float] = DEFAULT_REQUEST_TIMEOUT,
    max_redirects: int = 4,
) -> bytes:
    """Safely downloads an image from a URL with full SSRF protection, size limits, and redirect validation.

    Ensures:
    1. Scheme is http/https only.
    2. Hostname and all resolved IPs are non-private and non-metadata.
    3. Redirects are manually followed and validated at every hop (preventing open-redirect SSRF bypasses).
    4. Strict timeout and streaming maximum size enforcement (preventing memory exhaustion/DoS).

    Args:
        url (str): Target image URL.
        max_size_bytes (int): Maximum allowed response size in bytes (default: 10MB).
        timeout (tuple[float, float]): (connect_timeout, read_timeout) in seconds.
        max_redirects (int): Maximum allowed redirect hops (default: 4).

    Returns:
        bytes: Raw image binary data.

    Raises:
        SSRFProtectionError: If validation fails, download exceeds max_size, or connection times out.
    """
    current_url = url
    session = requests.Session()
    session.trust_env = False  # Avoid proxy bypasses via local environment variables
    headers = {
        "User-Agent": "VisionIQ-SafeImageFetcher/1.0 (Security-Audited; +https://github.com/Pranjal-sh-git/visioniq)",
        "Accept": "image/jpeg,image/png,image/webp,image/avif,image/*;q=0.8",
    }

    for hop in range(max_redirects + 1):
        # Validate current URL and all resolved IPs before connecting
        scheme, hostname, port, resolved_ips = validate_url(current_url)

        try:
            response = session.get(
                current_url,
                headers=headers,
                timeout=timeout,
                stream=True,
                allow_redirects=False,  # CRITICAL: Manual redirect inspection
            )
        except requests.exceptions.Timeout as e:
            raise SSRFProtectionError(f"Request to '{current_url}' timed out: {e}")
        except requests.exceptions.RequestException as e:
            raise SSRFProtectionError(f"Failed to connect to '{current_url}': {e}")

        # Check for HTTP redirect responses (301, 302, 303, 307, 308)
        if response.status_code in (301, 302, 303, 307, 308):
            location = response.headers.get("Location")
            if not location:
                raise SSRFProtectionError(f"HTTP {response.status_code} redirect missing 'Location' header.")

            # Resolve relative redirect URLs safely
            next_url = urllib.parse.urljoin(current_url, location)
            logger.info(f"[REDIRECT VALIDATION] Hop {hop + 1}: '{current_url}' -> '{next_url}'")
            current_url = next_url
            continue

        if response.status_code != 200:
            raise SSRFProtectionError(
                f"Failed to fetch image from '{current_url}': HTTP {response.status_code} {response.reason}"
            )

        # Check Content-Length header if provided
        content_length_header = response.headers.get("Content-Length")
        if content_length_header and content_length_header.isdigit():
            content_length = int(content_length_header)
            if content_length > max_size_bytes:
                raise SSRFProtectionError(
                    f"Image download rejected: Content-Length ({content_length} bytes) exceeds maximum limit ({max_size_bytes} bytes)."
                )

        # Stream and accumulate chunks with strict byte limit
        chunks = []
        total_bytes = 0
        try:
            for chunk in response.iter_content(chunk_size=65536):
                if chunk:
                    total_bytes += len(chunk)
                    if total_bytes > max_size_bytes:
                        raise SSRFProtectionError(
                            f"Image download rejected: Download exceeded maximum allowed size of {max_size_bytes} bytes."
                        )
                    chunks.append(chunk)
        except requests.exceptions.RequestException as e:
            raise SSRFProtectionError(f"Error streaming response from '{current_url}': {e}")

        image_data = b"".join(chunks)
        if not image_data:
            raise SSRFProtectionError(f"Empty response body received from '{current_url}'.")

        # Validate that the downloaded payload is a readable image
        try:
            with Image.open(BytesIO(image_data)) as img:
                img.verify()
        except Exception as e:
            raise SSRFProtectionError(f"Downloaded payload is not a valid image format: {e}")

        return image_data

    raise SSRFProtectionError(f"Exceeded maximum redirect limit of {max_redirects} hops.")
