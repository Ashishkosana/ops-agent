ENDPOINT = "/status"


def url(base: str) -> str:
    """Build the probe URL for a service base address."""
    return base.rstrip("/") + ENDPOINT
