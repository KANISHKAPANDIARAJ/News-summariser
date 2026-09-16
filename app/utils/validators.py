"""Security and input validation utilities, including robust SSRF protection."""

import ipaddress
import socket
from urllib.parse import urlparse
from typing import Tuple, Optional

# Denied IP networks (Private, loopback, link-local, cloud metadata)
BLOCKED_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),  # Loopback
    ipaddress.ip_network("10.0.0.0/8"),  # Private RFC1918
    ipaddress.ip_network("172.16.0.0/12"),  # Private RFC1918
    ipaddress.ip_network("192.168.0.0/16"),  # Private RFC1918
    ipaddress.ip_network(
        "169.254.0.0/16"
    ),  # Link-local / Cloud Metadata (AWS/GCP/Azure)
    ipaddress.ip_network("0.0.0.0/8"),  # Current network
    ipaddress.ip_network("100.64.0.0/10"),  # Shared address space (Carrier-grade NAT)
    ipaddress.ip_network("192.0.0.0/24"),  # IETF Protocol Assignments
    ipaddress.ip_network("192.0.2.0/24"),  # TEST-NET-1
    ipaddress.ip_network("198.18.0.0/15"),  # Network benchmark tests
    ipaddress.ip_network("198.51.100.0/24"),  # TEST-NET-2
    ipaddress.ip_network("203.0.113.0/24"),  # TEST-NET-3
    ipaddress.ip_network("224.0.0.0/4"),  # Multicast
    ipaddress.ip_network("240.0.0.0/4"),  # Reserved for future use
    ipaddress.ip_network("::1/128"),  # IPv6 Loopback
    ipaddress.ip_network("fc00::/7"),  # IPv6 Unique Local Address
    ipaddress.ip_network("fe80::/10"),  # IPv6 Link-local
]


def is_safe_url(url: str) -> Tuple[bool, Optional[str]]:
    """Validates URL against SSRF attacks by checking scheme, hostname, and resolving IP address.

    Returns:
        (is_safe, error_message)
    """
    if not url or not isinstance(url, str):
        return False, "URL cannot be empty."

    url = url.strip()
    try:
        parsed = urlparse(url)
    except Exception as e:
        return False, f"Malformed URL: {e}"

    if parsed.scheme.lower() not in ("http", "https"):
        return (
            False,
            f"Unsupported URL scheme '{parsed.scheme}'. Only http and https are allowed.",
        )

    hostname = parsed.hostname
    if not hostname:
        return False, "URL does not contain a valid hostname."

    # Check for localhost literals
    if hostname.lower() in ("localhost", "localhost.localdomain", "broadcasthost"):
        return False, "Access to localhost is blocked (SSRF Protection)."

    # Resolve DNS to check resolved IP address
    try:
        # Getaddrinfo to resolve IPv4 and IPv6
        addr_info = socket.getaddrinfo(hostname, None)
    except socket.gaierror:
        return False, f"Unable to resolve DNS for host '{hostname}'."
    except Exception as e:
        return False, f"DNS resolution error: {e}"

    if not addr_info:
        return False, f"No IP address found for host '{hostname}'."

    # Check each resolved IP address against blocked networks
    for family, _, _, _, sockaddr in addr_info:
        ip_str = sockaddr[0]
        try:
            ip_obj = ipaddress.ip_address(ip_str)
            for blocked_net in BLOCKED_NETWORKS:
                if ip_obj in blocked_net:
                    return (
                        False,
                        f"Access to private/internal IP {ip_str} is forbidden (SSRF Protection).",
                    )
        except ValueError:
            return False, f"Invalid IP address format: {ip_str}"

    return True, None
