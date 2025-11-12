import logging
from datetime import datetime, timezone
from typing import Dict

from .truth_posts_parser import generate_mock_posts

logger = logging.getLogger(__name__)

def _extract_username_from_url(url: str) -> str:
    """
    Extract the Truth Social username from a profile URL.

    Examples:
        https://truthsocial.com/@realDonaldTrump  -> realDonaldTrump
        https://truthsocial.com/@user/posts       -> user
    """
    try:
        cleaned = url.strip()
        if not cleaned:
            return "unknown"

        at_index = cleaned.rfind("@")
        if at_index != -1:
            segment = cleaned[at_index + 1 :]
            username = segment.split("/")[0]
        else:
            # Fallback: last path segment
            username = cleaned.rstrip("/").split("/")[-1]

        return username or "unknown"
    except Exception:
        logger.exception("Failed to parse username from URL '%s'", url)
        return "unknown"

def build_profile(identifier: str, id_type: str = "username") -> Dict[str, object]:
    """
    Build a structured profile payload with embedded posts.

    This implementation generates deterministic, realistic-looking data for
    demonstration and testing purposes without relying on external services.
    """
    scraped_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    if id_type == "url":
        username = _extract_username_from_url(identifier)
        profile_url = identifier
    elif id_type == "tag":
        tag_name = identifier.lstrip("#")
        username = f"{tag_name}_stream"
        profile_url = f"https://truthsocial.com/tags/{tag_name}"
    else:
        username = identifier.lstrip("@")
        profile_url = f"https://truthsocial.com/@{username}"

    base_hash = abs(hash(username))
    followers_count = 1_000 + (base_hash % 9_000_000)
    following_count = 10 + (base_hash % 10_000)
    statuses_count = 100 + (base_hash % 50_000)

    display_name = username.replace(".", " ").replace("_", " ").title() or username
    profile_id = f"profile-{username}"
    avatar_url = f"https://cdn.truthsocial.local/avatars/{username}.jpg"
    header_url = f"https://cdn.truthsocial.local/headers/{username}.jpg"

    posts = generate_mock_posts(username, num_posts=3)

    profile: Dict[str, object] = {
        "id": profile_id,
        "username": username,
        "display_name": display_name,
        "followers_count": followers_count,
        "following_count": following_count,
        "statuses_count": statuses_count,
        "avatar": avatar_url,
        "header": header_url,
        "url": profile_url,
        "scraped_at": scraped_at,
        "posts": posts,
    }

    logger.debug("Built profile payload for '%s' (type=%s)", identifier, id_type)
    return profile