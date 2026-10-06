"""Stub: pymoo imports alive_bar at module level but only uses it when progress=True,
which the diet-optimization code never sets. The real package is a terminal progress bar."""


def alive_bar(*args, **kwargs):
    raise RuntimeError("alive_progress is not available in the browser build")
