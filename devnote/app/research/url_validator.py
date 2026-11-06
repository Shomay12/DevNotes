"""
DevNote Research Reader — Safe URL Validation & SSRF Protection.
Strictly blocks access to loopback, private RFC1918 networks, cloud metadata endpoints,
and non-HTTP(S) schemes to ensure the server cannot be used as an internal proxy.
"""

import re
import socket
import ipaddress
from urllib.parse import urlparse
from typing import Tuple, Optional

# Prohibited hostnames
DISALLOWED_HOSTNAMES = {
    "localhost",
    "metadata.google.internal",
    "instance-data",
}

# Cloud metadata addresses to explicitly block
CLOUD_METADATA_IPS = {
    "169.254.169.254",  # AWS, GCP, Azure, OpenStack
    "fd00:ec2::254",    # AWS IPv6 metadata
}

# Regex for valid public domain labels
DOMAIN_PATTERN = re.compile(r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-_]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$")


def validate_url_safety(url: str) -> Tuple[bool, Optional[str]]:
    """
    Validates a URL against Server-Side Request Forgery (SSRF) and protocol risks.
    Returns (is_safe, error_message).
    """
    if not url or not isinstance(url, str):
        return False, "URL must be a non-empty string."

    url = url.strip()
    if not url:
        return False, "URL cannot be empty."

    try:
        parsed = urlparse(url)
    except Exception as e:
        return False, f"Failed to parse URL: {e}"

    # 1. Scheme check: only allow http and https
    if parsed.scheme.lower() not in ("http", "https"):
        return False, f"Unsupported protocol '{parsed.scheme}'. Only HTTP and HTTPS are permitted."

    hostname = parsed.hostname
    if not hostname:
        return False, "URL must contain a valid hostname."

    hostname_lower = hostname.lower()

    # 2. Check disallowed hostnames
    if (
        hostname_lower in DISALLOWED_HOSTNAMES
        or hostname_lower.endswith(".localhost")
        or hostname_lower.endswith(".local")
        or hostname_lower.endswith(".internal")
        or hostname_lower == "0.0.0.0"
    ):
        return False, f"Access to '{hostname}' is prohibited for security."

    # 3. Prevent credentials in URL
    if parsed.username or parsed.password:
        return False, "URLs with embedded credentials are not allowed."

    # 4. Check if hostname itself is directly an IP literal
    try:
        direct_ip = ipaddress.ip_address(hostname_lower)
        if (
            direct_ip.is_loopback
            or direct_ip.is_private
            or direct_ip.is_link_local
            or direct_ip.is_reserved
            or direct_ip.is_multicast
            or direct_ip.is_unspecified
        ):
            return False, f"Direct access to private or internal IP '{hostname}' is prohibited."
        if str(direct_ip) in CLOUD_METADATA_IPS:
            return False, "Access to cloud metadata endpoints is prohibited."
        return True, None
    except ValueError:
        # Not an IP literal
        pass

    # 5. Resolve hostname via DNS and verify all resolved addresses against private/loopback
    try:
        addr_info = socket.getaddrinfo(hostname, None, proto=socket.IPPROTO_TCP)
        if addr_info:
            for item in addr_info:
                sockaddr = item[4]
                ip_str = sockaddr[0]
                ip_obj = ipaddress.ip_address(ip_str)

                if str(ip_obj) in CLOUD_METADATA_IPS:
                    return False, "Access to cloud metadata service is prohibited."

                if ip_obj.is_loopback:
                    return False, f"Host '{hostname}' resolves to loopback address ({ip_str}), which is prohibited."

                if ip_obj.is_private:
                    return False, f"Host '{hostname}' resolves to private network address ({ip_str}), which is prohibited."

                if ip_obj.is_link_local:
                    return False, f"Host '{hostname}' resolves to link-local address ({ip_str}), which is prohibited."

                if ip_obj.is_unspecified:
                    return False, f"Host '{hostname}' resolves to unspecified address ({ip_str}), which is prohibited."

                if ip_obj.is_reserved or ip_obj.is_multicast:
                    return False, f"Host '{hostname}' resolves to reserved address ({ip_str}), which is prohibited."

    except socket.gaierror:
        # In offline mode or sandbox without external DNS, check if hostname is a valid public domain name
        if not DOMAIN_PATTERN.match(hostname_lower):
            return False, f"Invalid domain name or could not resolve '{hostname}'."
    except Exception as e:
        return False, f"Security validation failed for '{hostname}'."

    return True, None
