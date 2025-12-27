"""Terminal (tmux) operations for Cactus."""

import subprocess

from models import Status


class TerminalClient:
    """Handles all tmux operations via subprocess."""

    def create_session(self, name: str, path: str, display_name: str) -> None:
        """Create a new tmux session with configuration."""
        subprocess.run(["tmux", "new-session", "-d", "-s", name, "-c", path])
        subprocess.run(["tmux", "set-option", "-t", name, "mouse", "on"])
        subprocess.run(["tmux", "set-option", "-t", name, "status-left", f" {display_name} | "])
        subprocess.run(["tmux", "set-option", "-t", name, "status-right", ""])

    def send_keys(self, session_name: str, keys: str) -> None:
        """Send keys to a tmux session."""
        subprocess.run(["tmux", "send-keys", "-t", session_name, keys, "Enter"])

    def switch_to_session(self, session_name: str) -> bool:
        """Switch all tmux clients to the specified session. Returns True if successful."""
        result = subprocess.run(
            ["tmux", "list-clients", "-F", "#{client_tty}"],
            capture_output=True, text=True
        )
        clients = [c for c in result.stdout.strip().split("\n") if c]

        if not clients:
            return False

        for client in clients:
            subprocess.run(
                ["tmux", "switch-client", "-c", client, "-t", session_name],
                capture_output=True, text=True
            )
        return True

    def rename_session(self, old_name: str, new_name: str) -> None:
        """Rename a tmux session."""
        subprocess.run(["tmux", "rename-session", "-t", old_name, new_name])

    def delete_session(self, session_name: str) -> None:
        """Delete a tmux session."""
        subprocess.run(["tmux", "kill-session", "-t", session_name], capture_output=True)

    def get_pane_map(self) -> dict[str, str]:
        """Get map of session_name -> pane_id for all sessions (first pane only)."""
        result = subprocess.run(
            ["tmux", "list-panes", "-a", "-F", "#{session_name} #{pane_id}"],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            return {}

        pane_map = {}
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            parts = line.split(" ", 1)
            if len(parts) == 2 and parts[0] not in pane_map:
                pane_map[parts[0]] = parts[1]
        return pane_map

    def capture_pane(self, pane_id: str) -> list[str]:
        """Capture pane content as lines."""
        result = subprocess.run(
            ["tmux", "capture-pane", "-p", "-t", pane_id],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            return []
        return result.stdout.split("\n")


def detect_status(content: str, last_content: str, current_status: Status) -> tuple[Status, bool]:
    """
    Detect session status from pane content.
    Returns (new_status, changed).
    """
    if content != last_content:
        return Status.WORKING, True

    if ">" in content:
        # Only set to READY if not already READ
        if current_status != Status.READ:
            return Status.READY, current_status != Status.READY
        return Status.READ, False

    if any(p in content for p in ["Would you like to proceed?", "1. Yes", "Do you want to"]):
        return Status.WAITING, current_status != Status.WAITING

    return Status.WORKING, current_status != Status.WORKING
