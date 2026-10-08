"""Shared errors for rejecting unrecognized or malformed source records."""


class IngestionRecordError(ValueError):
    """A source record cannot be normalized safely."""
