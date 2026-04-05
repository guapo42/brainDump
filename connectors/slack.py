"""Slack Connector — fetches channel messages via Slack Web API."""

from datetime import datetime

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from models.schemas import Platform


class SlackConnector:
    """Fetches messages from Slack channels and processes through pipeline.

    Usage:
        connector = SlackConnector(pipeline, bot_token="xoxb-...")
        count = connector.fetch_channel_history("C01234567")
        # or fetch all joined channels:
        count = connector.fetch_all_channels()
    """

    def __init__(self, pipeline, bot_token: str):
        self.pipeline = pipeline
        self.client = WebClient(token=bot_token)
        self._user_cache: dict[str, dict] = {}

    def fetch_channel_history(
        self, channel_id: str, oldest: str | None = None, max_pages: int = 10,
    ) -> int:
        """Fetch messages from a single channel with cursor pagination.

        Args:
            channel_id: Slack channel ID (e.g., C01234567).
            oldest: Unix timestamp string. Only fetch messages after this.
            max_pages: Maximum pagination pages (200 messages per page).

        Returns:
            Number of messages processed.
        """
        total = 0
        cursor = None

        for page in range(max_pages):
            kwargs = {"channel": channel_id, "limit": 200}
            if oldest:
                kwargs["oldest"] = oldest
            if cursor:
                kwargs["cursor"] = cursor

            try:
                resp = self.client.conversations_history(**kwargs)
            except SlackApiError as e:
                print(f"Slack API error: {e.response['error']}")
                break

            messages = resp.get("messages", [])
            for msg in messages:
                if msg.get("subtype"):  # skip join/leave/etc
                    continue
                self._process_message(msg, channel_id)
                total += 1

            # Pagination
            if resp.get("has_more"):
                cursor = resp.get("response_metadata", {}).get("next_cursor")
                if not cursor:
                    break
            else:
                break

        return total

    def fetch_all_channels(self, oldest: str | None = None) -> int:
        """Fetch messages from all channels the bot is in.

        Returns:
            Total messages processed across all channels.
        """
        total = 0
        cursor = None

        while True:
            kwargs = {"types": "public_channel,private_channel", "limit": 200}
            if cursor:
                kwargs["cursor"] = cursor

            try:
                resp = self.client.conversations_list(**kwargs)
            except SlackApiError as e:
                print(f"Slack API error listing channels: {e.response['error']}")
                break

            for channel in resp.get("channels", []):
                if channel.get("is_member"):
                    count = self.fetch_channel_history(channel["id"], oldest=oldest)
                    print(f"  #{channel.get('name', channel['id'])}: {count} messages")
                    total += count

            if resp.get("response_metadata", {}).get("next_cursor"):
                cursor = resp["response_metadata"]["next_cursor"]
            else:
                break

        return total

    def _process_message(self, msg: dict, channel_id: str):
        """Convert a Slack message to pipeline input."""
        user_id = msg.get("user", "")
        user_info = self._resolve_user(user_id)

        # Thread awareness: use thread_ts if message is in a thread
        thread_id = msg.get("thread_ts")

        # Parse timestamp
        try:
            ts = float(msg.get("ts", "0"))
            received_dt = datetime.fromtimestamp(ts)
        except (ValueError, OSError):
            received_dt = datetime.now()

        self.pipeline.process_text(
            text=msg.get("text", ""),
            source_id=f"slack_{channel_id}_{msg.get('ts', '')}",
            platform=Platform.SLACK,
            sender_name=user_info.get("name", user_id),
            sender_email=user_info.get("email", f"{user_id}@slack"),
            received_at=received_dt,
        )

    def _resolve_user(self, user_id: str) -> dict:
        """Look up user info from Slack, with caching."""
        if user_id in self._user_cache:
            return self._user_cache[user_id]

        try:
            resp = self.client.users_info(user=user_id)
            user = resp.get("user", {})
            profile = user.get("profile", {})
            info = {
                "name": user.get("real_name", user.get("name", user_id)),
                "email": profile.get("email", f"{user_id}@slack"),
            }
        except SlackApiError:
            info = {"name": user_id, "email": f"{user_id}@slack"}

        self._user_cache[user_id] = info
        return info
