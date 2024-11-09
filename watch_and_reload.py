import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time

class ChangeHandler(FileSystemEventHandler):
    def __init__(self, command):
        self.command = command
        self.process = None
        self.start_process()

    def start_process(self):
        if self.process:
            self.process.terminate()
        self.process = subprocess.Popen(self.command, shell=True)

    def on_any_event(self, event):
        if '.git' not in event.src_path:
            print(f"Detected change in {event.src_path}. Restarting Daphne...")
            self.start_process()

if __name__ == "__main__":
    path = "."
    command = "daphne -b 0.0.0.0 -p 8000 server.asgi:application" 
    event_handler = ChangeHandler(command)
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()