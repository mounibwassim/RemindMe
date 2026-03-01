"""
toast_test.py — Minimal standalone Windows toast notification test.
Run directly: python toast_test.py
Or as frozen EXE: toast_test.exe
Logs results to %USERPROFILE%\\app_debug.log
"""
import os
import sys
import logging
import traceback
import time

LOG_PATH = os.path.join(os.environ.get("USERPROFILE", os.path.expanduser("~")), "app_debug.log")

logging.basicConfig(
    level=logging.DEBUG,
    format="[%(asctime)s][%(levelname)s][toast_test] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(LOG_PATH, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ]
)
log = logging.getLogger("toast_test")

log.info("=" * 60)
log.info("Toast Test Starting")
log.info(f"Python: {sys.version}")
log.info(f"Frozen: {getattr(sys, 'frozen', False)}")
log.info(f"Log path: {LOG_PATH}")
log.info("=" * 60)

# ── Test 1: win10toast ───────────────────────────────────────────────────────
log.info("[Test 1] Importing win10toast ...")
try:
    from win10toast import ToastNotifier
    log.info("win10toast imported OK")
    t = ToastNotifier()
    log.info("ToastNotifier instantiated OK")
    log.info("Calling show_toast() ...")
    result = t.show_toast(
        "RemindMe — Toast Test",
        "If you can read this, win10toast is working correctly!",
        duration=8,
        threaded=True
    )
    log.info(f"show_toast() returned: {result}")
    time.sleep(3)
    log.info("[Test 1] PASSED — win10toast toast fired")
except Exception:
    log.error(f"[Test 1] FAILED:\n{traceback.format_exc()}")

# ── Test 2: plyer notification ───────────────────────────────────────────────
log.info("[Test 2] Importing plyer.notification ...")
try:
    from plyer import notification
    log.info("plyer imported OK")
    notification.notify(
        title="RemindMe — Plyer Test",
        message="If you see this, plyer is working!",
        app_name="RemindMe",
        timeout=8
    )
    log.info("[Test 2] PASSED — plyer notification sent")
except Exception:
    log.error(f"[Test 2] FAILED:\n{traceback.format_exc()}")

log.info("=" * 60)
log.info("Toast Test Complete. Check app_debug.log for results.")
log.info("=" * 60)

# Keep console open if run as EXE
if getattr(sys, 'frozen', False):
    input("\nPress Enter to close...")
