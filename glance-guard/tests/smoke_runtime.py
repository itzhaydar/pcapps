import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from glance_guard.diagnostics import run
run()
