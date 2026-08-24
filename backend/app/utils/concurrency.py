from datetime import datetime, timezone


class ConcurrencyManager:
    """Simple optimistic concurrency checker."""

    @staticmethod
    def _normalize(value):
        if value is None:
            return None
        if isinstance(value, str):
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if value.tzinfo is not None:
            value = value.astimezone(timezone.utc).replace(tzinfo=None)
        return value

    @staticmethod
    def has_conflict(client_timestamp, server_timestamp):
        if client_timestamp is None or server_timestamp is None:
            return False
        return ConcurrencyManager._normalize(client_timestamp) < ConcurrencyManager._normalize(server_timestamp)
