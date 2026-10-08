import ipaddress
import socket
from urllib.parse import urlparse

_LOCAL_HOSTS = {"localhost"}


def validate_api_base(value: str) -> str:
    """Valide une URL d'API LLM fournie par l'utilisateur (anti-SSRF)."""
    value = (value or "").strip()
    parsed = urlparse(value)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise ValueError("L'URL de l'API doit commencer par http:// ou https://.")
    host = parsed.hostname
    if host in _LOCAL_HOSTS:
        raise ValueError("Cette adresse n'est pas autorisée.")
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror:
        raise ValueError("Nom d'hôte introuvable.")
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if not ip.is_global:
            raise ValueError("Cette adresse n'est pas autorisée.")
    return value.rstrip("/")
