"""Compatibility wrapper for the central system-administration policy."""
from app.auth.authorization import system_admin_required


# Existing routes can keep this import while authorization remains centralized.
admin_required = system_admin_required
