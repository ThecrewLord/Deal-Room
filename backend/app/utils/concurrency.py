from datetime import datetime


class ConcurrencyManager:
    """
    Simple optimistic concurrency checker.
    """

    @staticmethod
    def has_conflict(client_timestamp, server_timestamp):
        """
        Returns True if another user modified the record.
        """

        if client_timestamp is None or server_timestamp is None:
            return False

        if isinstance(client_timestamp, str):
            client_timestamp = datetime.fromisoformat(client_timestamp)

        return client_timestamp < server_timestamp