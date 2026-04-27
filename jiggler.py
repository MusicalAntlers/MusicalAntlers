#!/usr/bin/env python3
"""
Mouse Jiggler — keeps your Mac awake using caffeinate + tiny invisible mouse moves.
No dependencies. Works with lid open or closed.
Usage:  python3 jiggler.py
Stop:   Ctrl+C
"""

import subprocess
import time
import sys
import signal

# === CONFIGURATION ============================================================
JIGGLE_INTERVAL = 60  # seconds between jiggle moves
MOVE_AMOUNT = 1  # pixels to move (sub-visible — you won't see it)
# ==============================================================================

caffeinate_proc = None


def start_caffeinate():
    """
    caffeinate -dims prevents:
      -d  display sleep
      -i  system idle sleep
      -m  disk sleep
      -s  system sleep (when on AC power)
    This alone keeps the Mac awake. The mouse jiggle is a belt-and-suspenders
    backup for apps that watch for user activity specifically.
    """
    proc = subprocess.Popen(
        ["caffeinate", "-dims"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    print(f"  caffeinate started (PID {proc.pid})")
    return proc


def jiggle():
    """Move the mouse 1px right then 1px back using AppleScript. Invisible."""
    script = f"""
    tell application "System Events"
        set p to get the position of the mouse
        set x to item 1 of p
        set y to item 2 of p
        set the position of the mouse to {{x + {MOVE_AMOUNT}, y}}
        set the position of the mouse to {{x, y}}
    end tell
    """
    subprocess.run(["osascript", "-e", script], capture_output=True, timeout=5)


def cleanup(sig=None, frame=None):
    print("\n\nStopping jiggler...")
    if caffeinate_proc and caffeinate_proc.poll() is None:
        caffeinate_proc.terminate()
        print("  caffeinate stopped")
    print("  Your Mac will now sleep normally.")
    sys.exit(0)


def main():
    global caffeinate_proc

    print("=" * 46)
    print("  Mouse Jiggler — Mac Stay-Awake Utility")
    print("=" * 46)
    print(f"  Jiggle interval : every {JIGGLE_INTERVAL}s")
    print(f"  Move amount     : {MOVE_AMOUNT}px (invisible)")
    print(f"  Press Ctrl+C to stop\n")

    # Graceful shutdown on Ctrl+C or kill
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    caffeinate_proc = start_caffeinate()
    print("  Jiggling...\n")

    count = 0
    while True:
        jiggle()
        count += 1
        ts = time.strftime("%H:%M:%S")
        print(f"  [{ts}]  Jiggle #{count}", end="\r", flush=True)
        time.sleep(JIGGLE_INTERVAL)


if __name__ == "__main__":
    main()
