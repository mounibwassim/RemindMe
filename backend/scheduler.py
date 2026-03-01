import threading
import time
import logging
import sys
import traceback
from datetime import datetime, timezone
from kivy.utils import platform

# Guard plyer import
try:
    from plyer import notification
except ImportError:
    notification = None

# Cross-platform sound handling
from kivy.core.audio import SoundLoader
import os
from utils.helpers import get_asset_path

# Safe TTS import
try:
    import pyttsx3
except ImportError:
    pyttsx3 = None

from .storage import list_tasks, mark_notified
from .audit import write_audit
from .crypto import decrypt_bytes

POLL_INTERVAL = 10  # seconds (dev). Increase for production.

def _setup_scheduler_logger(log_dir: str):
    """Configure the scheduler logger to write to a known writable path."""
    log_path = os.path.join(log_dir, 'scheduler.log')
    handler = logging.FileHandler(log_path, encoding='utf-8')
    handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    log = logging.getLogger("Scheduler")
    log.setLevel(logging.DEBUG)
    # Avoid adding duplicate handlers on re-import
    if not any(isinstance(h, logging.FileHandler) for h in log.handlers):
        log.addHandler(handler)
    return log

logger = logging.getLogger("Scheduler")  # default; overridden in __init__

class Scheduler(threading.Thread):
    def __init__(self, db_path: str, key: bytes, on_notify_callback=None, tts_enabled=False):
        super().__init__(daemon=True)
        self.db_path = db_path
        self.key = key
        self.on_notify = on_notify_callback
        self.tts_enabled = tts_enabled
        self._stop = threading.Event()
        
        # Redirect log to the same directory as the DB (always writable)
        global logger
        log_dir = os.path.dirname(db_path) or os.path.expanduser('~')
        logger = _setup_scheduler_logger(log_dir)
        logger.info(f"Scheduler initialized. DB: {db_path}, TTS: {tts_enabled}, LogDir: {log_dir}")
        
        # Init TTS engine - Only if enabled to avoid COM threading issues
        self.engine = None
        if self.tts_enabled and pyttsx3:
            try:
                self.engine = pyttsx3.init()
                logger.info("TTS engine initialized")
            except Exception as e:
                logger.error(f"Failed to init TTS: {e}")
                self.engine = None
        elif pyttsx3:
             logger.info("TTS disabled in settings, engine not initialized.")
        else:
            logger.warning("pyttsx3 not installed or failed to import.")

    def run(self):
        logger.info("=== Scheduler thread STARTED ===")
        while not self._stop.is_set():
            try:
                logger.debug("Polling for due tasks...")
                rows = list_tasks(self.db_path)
                now = datetime.now() # Local time
                logger.debug(f"Current time (Local): {now}. Checking {len(rows)} tasks.")
                
                for row in rows:
                    # Safely extract array items up to max columns
                    task_id = row[0]
                    ct = row[1]
                    nonce = row[2]
                    due_iso = row[3]
                    priority = row[4]
                    notified = row[5]
                    created_iso = row[6] if len(row) > 6 else ""
                    completed_iso = row[7] if len(row) > 7 else ""
                    category = row[8] if len(row) > 8 else ""
                    sound = row[9] if len(row) > 9 else "Default"
                    desc = row[10] if len(row) > 10 else ""
                    is_overdue = row[11] if len(row) > 11 else 0
                        
                    if notified == 1 or notified == 2 or completed_iso:
                        continue
                        
                    # parse due date
                    try:
                        due = datetime.fromisoformat(due_iso)
                        # Assume stored time is local naive, so no conversion needed
                    except Exception as e:
                        logger.warning(f"Failed to parse due date for task {task_id}: {e}")
                        continue
                        
                    if due <= now:
                        logger.info(f"Task {task_id} is due! (Due: {due}, Now: {now})")
                        
                        # decrypt title
                        try:
                            title_bytes = decrypt_bytes(ct, nonce, self.key)
                            title = title_bytes.decode('utf-8').split("\n", 1)[0]
                        except Exception as e:
                            logger.error(f"Failed to decrypt task {task_id}: {e}")
                            title = "Reminder"
                            
                        logger.info(f"Triggering notification for task {task_id}: {title}")
                        
                        # Play Sound (Backend fallback / Cross-platform)
                        try:
                            sound_file = "assets/sounds/notification.wav"
                            sound_abs_path = get_asset_path(sound_file)
                            if os.path.exists(sound_abs_path):
                                sound_obj = SoundLoader.load(sound_abs_path)
                                if sound_obj:
                                    sound_obj.play()
                                    logger.info(f"Playing sound: {sound_abs_path}")
                                else:
                                    logger.error("SoundLoader returned None")
                            else:
                                logger.warning(f"Sound file not found: {sound_abs_path}")
                        except Exception as e:
                            logger.error(f"Sound playback failed: {e}")
                        
                        # Mark notified BEFORE firing callback to prevent double-trigger
                        mark_notified(self.db_path, task_id)
                        logger.info(f"Task {task_id} marked as notified")
                        
                        # Trigger UI Callback via MAIN THREAD (critical in frozen EXE:
                        # win10toast/COM requires main thread or COM-initialized thread).
                        if self.on_notify:
                            logger.info(f"Scheduling on_notify for task {task_id} on main thread via Clock")
                            try:
                                from kivy.clock import Clock
                                # Capture values in closure, don't hold scheduler-thread references
                                _tid = task_id
                                _title = title
                                Clock.schedule_once(
                                    lambda dt, tid=_tid, t=_title: self.on_notify(tid, t),
                                    0
                                )
                            except Exception as e:
                                logger.error(f"Clock.schedule_once for on_notify failed: {e}\n{traceback.format_exc()}")
                        else:
                            logger.warning("No on_notify callback registered — notification not delivered!")
                            
            except Exception as e:
                logger.error(f"Scheduler loop error: {e}\n{traceback.format_exc()}")
            
            self._stop.wait(POLL_INTERVAL)
        logger.info("=== Scheduler thread STOPPED ===")

    def stop_scheduler(self):
        logger.info("Stopping scheduler...")
        self._stop.set()

