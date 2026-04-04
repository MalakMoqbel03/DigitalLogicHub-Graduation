def normalize_style(style: str | None) -> str | None:
    """Normalise VARK style strings to a consistent lowercase form."""
    if not style:
        return None
    s = style.strip().lower()
    if s in ("aural", "audio"):
        return "auditory"
    if s in ("read/write", "read", "write", "reading"):
        return "reading"
    return s


def normalize_level(level: str | None) -> str | None:
    """Normalise difficulty/level strings to lowercase."""
    if not level:
        return None
    return level.strip().lower()