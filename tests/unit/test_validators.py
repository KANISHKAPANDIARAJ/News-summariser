"""Unit tests for URL validation and anti-SSRF protections."""

from app.utils.validators import is_safe_url


def test_localhost_blocked():
    safe, err = is_safe_url("http://localhost:5000/admin")
    assert not safe
    assert "localhost" in err.lower()


def test_loopback_ip_blocked():
    safe, err = is_safe_url("http://127.0.0.1:8080")
    assert not safe
    assert "forbidden" in err.lower() or "blocked" in err.lower()


def test_cloud_metadata_blocked():
    safe, err = is_safe_url("http://169.254.169.254/latest/meta-data")
    assert not safe
    assert "forbidden" in err.lower() or "blocked" in err.lower()


def test_private_subnets_blocked():
    for ip in ["http://10.0.0.1", "http://172.16.0.1", "http://192.168.1.1"]:
        safe, err = is_safe_url(ip)
        assert not safe
        assert "forbidden" in err.lower() or "blocked" in err.lower()


def test_unsupported_scheme():
    safe, err = is_safe_url("ftp://ftp.example.com/file.txt")
    assert not safe
    assert "scheme" in err.lower()


def test_valid_public_domain():
    safe, err = is_safe_url("https://www.bbc.com/news")
    assert safe
    assert err is None
