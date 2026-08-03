import sys
if sys.version_info < (3, 10):
    raise SystemExit(1)
try:
    import pytest
    import xdist
    import packaging
except Exception:
    raise SystemExit(1)
raise SystemExit(0)
