import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

logger = logging.getLogger(__name__)

def normalize_identifier(raw: str) -> Tuple[str, str]:
    """
    Normalize a raw identifier into a (value, type) pair.

    Types:
        - "url"      -> value is kept as-is
        - "tag"      -> starts with '#'
        - "username" -> everything else, leading '@' stripped
    """
    value = (raw or "").strip()
    if not value:
        raise ValueError("Identifier cannot be empty")

    if value.startswith("http://") or value.startswith("https://"):
        return value, "url"

    if value.startswith("#"):
        return value, "tag"

    return value.lstrip("@"), "username"

def _strip_html(value: str) -> str:
    """
    Remove very basic HTML tags from a string without external dependencies.

    This is intentionally simple and should not be used as a general-purpose
    HTML sanitizer, but is sufficient for cleaning up small snippets.
    """
    result_chars: List[str] = []
    inside_tag = False

    for char in value:
        if char == "<":
            inside_tag = True
            continue
        if char == ">":
            inside_tag = False
            continue
        if not inside_tag:
            result_chars.append(char)

    return "".join(result_chars).strip()

def flatten_profiles_for_csv(profiles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Flatten a list of profile dictionaries into a row-per-post structure
    suitable for CSV export.

    Each row contains basic profile metadata alongside a single post's data.
    If a profile has no posts, a single row is emitted with post-related
    fields set to None.
    """
    rows: List[Dict[str, Any]] = []

    for profile in profiles:
        posts = profile.get("posts") or [None]

        for post in posts:
            row: Dict[str, Any] = {
                "profile_id": profile.get("id"),
                "username": profile.get("username"),
                "display_name": profile.get("display_name"),
                "followers_count": profile.get("followers_count"),
                "following_count": profile.get("following_count"),
                "statuses_count": profile.get("statuses_count"),
                "profile_url": profile.get("url"),
            }

            if post is not None:
                content_raw = post.get("content", "") or ""
                row.update(
                    {
                        "post_id": post.get("id"),
                        "post_created_at": post.get("created_at"),
                        "post_url": post.get("url"),
                        "post_content": _strip_html(content_raw),
                        "replies_count": post.get("replies_count"),
                        "reblogs_count": post.get("reblogs_count"),
                        "favourites_count": post.get("favourites_count"),
                        "media_attachments_count": len(post.get("media_attachments") or []),
                    }
                )
            else:
                row.update(
                    {
                        "post_id": None,
                        "post_created_at": None,
                        "post_url": None,
                        "post_content": None,
                        "replies_count": None,
                        "reblogs_count": None,
                        "favourites_count": None,
                        "media_attachments_count": 0,
                    }
                )

            rows.append(row)

    return rows

def iso_utc_now() -> str:
    """Return the current UTC time in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")