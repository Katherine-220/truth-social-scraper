from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

def generate_mock_posts(base_username: str, num_posts: int = 3) -> List[Dict[str, Any]]:
    """
    Generate a deterministic list of mock posts for a given username.

    The IDs, timestamps, and engagement stats are derived from the username hash
    to make the output stable but varied across different profiles.
    """
    posts: List[Dict[str, Any]] = []
    base_hash = abs(hash(base_username)) % 10_000_000_000

    for index in range(num_posts):
        post_hash = (base_hash + index * 97) % 10_000_000_000
        post_id = f"{post_hash:010d}"

        created_at_dt = datetime.now(timezone.utc) - timedelta(hours=index * 3)
        created_at = created_at_dt.isoformat().replace("+00:00", "Z")

        engagement_seed = (base_hash // (index + 5)) % 1_000 if index + 5 != 0 else base_hash % 1_000
        replies_count = 20 + engagement_seed % 500
        reblogs_count = 40 + (engagement_seed * 2) % 1500
        favourites_count = 100 + (engagement_seed * 3) % 5000

        post_url = f"https://truthsocial.com/@{base_username}/{post_id}"
        media_url = f"https://static-assets.truthsocial.local/{base_username}/{post_id}.jpg"

        content = (
            f"<p>Automated update from <strong>@{base_username}</strong> "
            f"with post id <code>{post_id}</code>.</p>"
        )

        media_attachments = [
            {
                "id": f"media-{post_id}",
                "type": "image",
                "url": media_url,
            }
        ]

        posts.append(
            {
                "id": post_id,
                "created_at": created_at,
                "url": post_url,
                "content": content,
                "replies_count": replies_count,
                "reblogs_count": reblogs_count,
                "favourites_count": favourites_count,
                "media_attachments": media_attachments,
            }
        )

    return posts