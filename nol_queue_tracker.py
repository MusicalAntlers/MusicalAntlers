#!/usr/bin/env python3
"""
NOL World Queue Tracker
━━━━━━━━━━━━━━━━━━━━━━
Polls you on a timer to enter your current queue position,
estimates your wait time, and fires a loud macOS alert
the moment you're ≤ 20 people away from the front.

Requirements: pip install rich
"""

import sys, time, math, threading, subprocess
from datetime import datetime, timedelta

# ── Auto-install rich ───────────────────────────────────────────────────────
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.prompt import Prompt, IntPrompt
    from rich import box
except ImportError:
    print("Installing 'rich' for a nicer UI…")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "rich", "-q"])
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.prompt import Prompt, IntPrompt
    from rich import box

console = Console()

ALERT_THRESHOLD = 20        # fire alarm when people_ahead <= this
DEFAULT_POLL_MINUTES = 5    # how often to ask for a new reading


# ── macOS helpers ───────────────────────────────────────────────────────────
def mac_notify(title: str, message: str, sound: str = "Glass"):
    try:
        subprocess.run(
            ["osascript", "-e",
             f'display notification "{message}" with title "{title}" sound name "{sound}"'],
            capture_output=True,
        )
    except Exception:
        pass


def mac_speak(text: str):
    try:
        subprocess.Popen(["say", text])
    except Exception:
        pass


def mac_alarm():
    mac_speak("Alert! You are almost at the front of the queue. Only 20 people left!")
    for _ in range(5):
        subprocess.run(["afplay", "/System/Library/Sounds/Glass.aiff"], capture_output=True)
        time.sleep(0.6)
    mac_notify("🎟 NOL World Queue", "⚡ ALMOST THERE — ≤20 people ahead! GO GO GO!", "Blow")


# ── Data model ──────────────────────────────────────────────────────────────
class QueueSession:
    def __init__(self, event_name: str, poll_minutes: int):
        self.event_name   = event_name
        self.poll_minutes = poll_minutes
        self.start_time   = datetime.now()
        self.snapshots: list[dict] = []
        self.alerted      = False
        self._stop        = threading.Event()
        self._poll_thread = None

    def add(self, people_ahead: int):
        self.snapshots.append({"time": datetime.now(), "people_ahead": people_ahead})

    def latest(self):
        return self.snapshots[-1] if self.snapshots else None

    def estimate(self):
        if len(self.snapshots) < 2:
            return None
        first, last = self.snapshots[0], self.snapshots[-1]
        elapsed   = (last["time"] - first["time"]).total_seconds()
        processed = first["people_ahead"] - last["people_ahead"]
        if processed <= 0 or elapsed <= 0:
            return None
        rate   = processed / elapsed
        remain = last["people_ahead"]
        eta_s  = remain / rate
        start  = first["people_ahead"]
        pct    = max(0.0, min(100.0, (1 - remain / start) * 100)) if start else 0.0
        return {
            "minutes":   eta_s / 60,
            "eta":       datetime.now() + timedelta(seconds=eta_s),
            "rate_min":  rate * 60,
            "pct":       pct,
            "remaining": remain,
        }

    def start_poll_timer(self):
        def _tick():
            while not self._stop.wait(timeout=self.poll_minutes * 60):
                console.print()
                console.print(Panel(
                    "[bold yellow]⏰  Time to check your NOL queue![/bold yellow]\n"
                    "[dim]Open world.nol.com, note people ahead, then log option [bold white]1[/bold white].[/dim]",
                    border_style="yellow",
                ))
                mac_notify("NOL Queue Tracker", "⏰ Time to check your queue position!")
        self._poll_thread = threading.Thread(target=_tick, daemon=True)
        self._poll_thread.start()

    def stop(self):
        self._stop.set()


# ── Display ──────────────────────────────────────────────────────────────────
def print_header():
    console.print(Panel.fit(
        "[bold magenta]🎟  NOL World Queue Tracker[/bold magenta]\n"
        "[dim]Auto-reminders  ·  Wait estimate  ·  ≤20-person alarm[/dim]",
        border_style="magenta",
    ))


def format_wait(minutes: float) -> str:
    if minutes < 1:
        return "[bold green]< 1 minute — almost there![/bold green]"
    if minutes < 60:
        return f"[bold yellow]~{math.ceil(minutes)} min[/bold yellow]"
    h, m = int(minutes // 60), int(minutes % 60)
    return f"[bold red]~{h}h {m}m[/bold red]"


def print_status(session: QueueSession):
    if not session.snapshots:
        console.print("[dim]No snapshots yet.[/dim]")
        return

    t = Table(title=f"📋  {session.event_name}", box=box.ROUNDED, border_style="cyan")
    t.add_column("#",            style="dim",   width=4)
    t.add_column("Time",         style="white", width=10)
    t.add_column("People Ahead", style="red",   width=14)
    t.add_column("Change",       style="green", width=10)

    prev = None
    for i, s in enumerate(session.snapshots, 1):
        change = ""
        if prev is not None:
            d = prev - s["people_ahead"]
            change = (f"[green]▼ {d:,}[/green]" if d > 0
                      else f"[red]▲ {abs(d):,}[/red]" if d < 0
                      else "[dim]—[/dim]")
        t.add_row(str(i), s["time"].strftime("%H:%M:%S"),
                  f"{s['people_ahead']:,}", change)
        prev = s["people_ahead"]
    console.print(t)

    est = session.estimate()
    if est:
        bar_n = int(est["pct"] / 5)
        bar   = "█" * bar_n + "░" * (20 - bar_n)
        console.print(Panel(
            f"  [cyan]Progress:[/cyan]  {bar}  [bold]{est['pct']:.1f}%[/bold]\n"
            f"  [cyan]Est. wait:[/cyan] {format_wait(est['minutes'])}\n"
            f"  [cyan]ETA:[/cyan]       [white]{est['eta'].strftime('%I:%M %p')}[/white]\n"
            f"  [cyan]Rate:[/cyan]      [white]~{est['rate_min']:,.0f} people/min[/white]\n"
            f"  [cyan]Remaining:[/cyan] [white]{est['remaining']:,} people ahead[/white]",
            title="⏱  Wait Estimate",
            border_style="yellow",
        ))
    elif len(session.snapshots) == 1:
        console.print(Panel(
            "[dim]Log one more snapshot to unlock wait estimates.[/dim]",
            title="⏱  Wait Estimate", border_style="dim",
        ))


# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    print_header()

    console.print("\n[bold]Set up your queue session.[/bold]")
    event_name   = Prompt.ask("Event name (e.g. BTS ARIRANG Goyang)")
    poll_minutes = IntPrompt.ask("Remind me to check every N minutes", default=DEFAULT_POLL_MINUTES)

    session = QueueSession(event_name, poll_minutes)
    session.start_poll_timer()

    console.print(f"\n[green]✅ Tracking:[/green]          [bold]{event_name}[/bold]")
    console.print(f"[green]✅ Poll reminder every:[/green] [bold]{poll_minutes} min[/bold]")
    console.print(f"[green]✅ Alarm fires when:[/green]    [bold]≤ {ALERT_THRESHOLD} people ahead[/bold]\n")
    console.print("[dim]Tip: NOL queues often show 100k+ — those are mostly bots. "
                  "Focus on the rate of change, not the raw number.[/dim]\n")

    while True:
        console.print("\n[bold cyan]─── Menu ───[/bold cyan]")
        console.print("  [bold]1[/bold] – Log queue update  (enter people ahead right now)")
        console.print("  [bold]2[/bold] – View status & estimate")
        console.print("  [bold]3[/bold] – Change poll interval")
        console.print("  [bold]q[/bold] – Quit")

        choice = Prompt.ask("Choice", default="1")

        if choice == "1":
            people_ahead = IntPrompt.ask("People ahead of you right now")
            session.add(people_ahead)
            console.print(
                f"[green]✅ Logged {people_ahead:,} at {datetime.now().strftime('%H:%M:%S')}[/green]"
            )

            est = session.estimate()
            if est:
                console.print(
                    f"   ⏱  {format_wait(est['minutes'])} remaining  "
                    f"[dim]({est['pct']:.0f}% through)[/dim]"
                )

            # ── THRESHOLD ALARM ──────────────────────────────────────
            if people_ahead <= ALERT_THRESHOLD and not session.alerted:
                session.alerted = True
                console.print()
                console.print(Panel(
                    f"[bold red]🚨  ALARM — ONLY {people_ahead} PEOPLE AHEAD! 🚨[/bold red]\n\n"
                    "[bold white]➡  Open NOL World NOW and get ready to select seats![/bold white]\n"
                    "[dim]You'll have ~10 minutes once you reach the ticketing page.[/dim]",
                    border_style="red",
                    title="⚡  THRESHOLD REACHED",
                ))
                threading.Thread(target=mac_alarm, daemon=True).start()

            elif people_ahead <= ALERT_THRESHOLD and session.alerted:
                console.print(
                    f"[bold red]⚡  Still ≤{ALERT_THRESHOLD} ahead ({people_ahead:,}). "
                    f"Stay on the page![/bold red]"
                )

        elif choice == "2":
            print_status(session)

        elif choice == "3":
            new_mins = IntPrompt.ask("New poll interval (minutes)", default=session.poll_minutes)
            session.stop()
            session.poll_minutes = new_mins
            session._stop = threading.Event()
            session.start_poll_timer()
            console.print(f"[green]✅ Poll interval updated to {new_mins} min[/green]")

        elif choice.lower() == "q":
            session.stop()
            console.print("\n[bold magenta]Good luck — hope you get those tickets! 🎉[/bold magenta]")
            break
        else:
            console.print("[red]Invalid choice.[/red]")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n\n[dim]Exited. Good luck![/dim]")
