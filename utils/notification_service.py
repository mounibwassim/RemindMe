from plyer import notification
from threading import Thread
import time
from datetime import datetime

def send_notification(title, message):
    try:
        notification.notify(
            title=title,
            message=message,
            timeout=10,
            app_name="RemindMe"
        )
    except Exception as e:
        print(f"Plyer notification failed: {e}")

def start_scheduler(get_tasks_function, update_task_callback=None):

    def worker():
        while True:
            now = datetime.now()

            try:
                tasks = get_tasks_function()

                for task in tasks:
                    if not task.get("notified", False) and task.get("datetime") <= now:
                        send_notification("Task Reminder", task.get("title", ""))
                        task["notified"] = True
                        if update_task_callback:
                            update_task_callback(task)
            except Exception as e:
                print(f"Scheduler error: {e}")

            time.sleep(30)

    Thread(target=worker, daemon=True).start()
