"""Claude Cactus - Terminal session manager for Claude Code."""

import os
from datetime import datetime

import libtmux
from textual.app import App
from textual.binding import Binding
from textual.containers import Vertical
from textual.widgets import Static, Footer
from textual import work

from models import (
    NUM_LINES_CAPTURE, CHECK_INTERVAL, EXPORT_CAPTURED,
    Status, Session, save_path
)
from terminal import TerminalClient, detect_status
from screens import NewSessionScreen, RenameSessionScreen
from widgets import SessionItem, WrappingListView


class CactusApp(App):
    """Main Cactus dashboard application."""

    CSS = """
    #header-bar {
        height: auto;
        padding: 1 0 0 0;
    }
    #app-title {
        text-style: bold;
        color: $text;
        text-align: center;
    }
    #app-subtitle {
        text-align: center;
        color: $text-disabled;
        text-style: italic;
    }
    #hint { text-align: center; color: $text-muted; padding: 1; }
    """

    BINDINGS = [
        Binding("n", "new_session", "New"),
        Binding("e", "rename_session", "Rename"),
        Binding("s", "switch_session", "Switch"),
        Binding("d", "delete_session", "Delete"),
        Binding("q", "quit", "Quit"),
    ]

    STATUS_PRIORITY = {
        Status.WAITING: 1,
        Status.WORKING: 2,
        Status.READY: 3,
        Status.READ: 4,
    }

    def __init__(self):
        super().__init__()
        self.sessions: list[Session] = []
        self.server = libtmux.Server()
        self.terminal = TerminalClient()

    def compose(self):
        yield Vertical(
            Static("🌵 Cactus", id="app-title"),
            Static("claude-code session manager", id="app-subtitle"),
            id="header-bar",
        )
        yield WrappingListView(id="list")
        yield Static("In another terminal: tmux attach -t <session-name>", id="hint")
        yield Footer()

    def on_mount(self):
        self.set_interval(CHECK_INTERVAL, self._update_status)
        self._load_existing_sessions()

    def _load_existing_sessions(self):
        """Load any existing claude-* sessions."""
        for tmux_session in self.server.sessions:
            if tmux_session.name.startswith("claude-"):
                self.sessions.append(Session(
                    name=tmux_session.name[7:],
                    path="",
                    tmux_session_name=tmux_session.name,
                ))
        self._refresh_list()

    def _update_status(self):
        """Update status for all sessions."""
        changed = False
        pane_map = self.terminal.get_pane_map()

        for s in self.sessions:
            pane_id = pane_map.get(s.tmux_session_name)
            if not pane_id:
                continue

            lines = self.terminal.capture_pane(pane_id)
            if not lines:
                continue

            if EXPORT_CAPTURED:
                with open(f"{s.name}_output.txt", "w", encoding="utf-8") as f:
                    f.write("\n".join(lines))

            content = "\n".join(lines[-NUM_LINES_CAPTURE:])
            new_status, status_changed = detect_status(content, s.last_content, s.status)

            if content != s.last_content:
                s.last_content = content

            if status_changed:
                s.status = new_status
                changed = True

        if changed:
            self._refresh_list()

    def _sort_sessions(self):
        """Sort sessions by status priority and last_visited time."""
        self.sessions.sort(key=lambda s: (
            self.STATUS_PRIORITY.get(s.status, 99),
            -s.last_visited.timestamp()
        ))

    def _refresh_list(self):
        self._sort_sessions()
        lst = self.query_one("#list", WrappingListView)
        idx = lst.index
        lst.clear()
        for s in self.sessions:
            lst.append(SessionItem(s))
        if idx is not None and idx < len(self.sessions):
            lst.index = idx

    @work
    async def action_new_session(self):
        result = await self.push_screen_wait(NewSessionScreen())
        if not result:
            return

        tmux_name = f"claude-{result['name']}"
        expanded_path = os.path.expanduser(result["path"])

        save_path(result["path"])
        self.terminal.create_session(tmux_name, expanded_path, result["name"])
        self.terminal.send_keys(tmux_name, "claude")

        for s in self.sessions:
            s.is_active = False

        self.sessions.append(Session(
            name=result["name"],
            path=expanded_path,
            tmux_session_name=tmux_name,
            is_active=True,
        ))
        self._refresh_list()

        if self.terminal.switch_to_session(tmux_name):
            self.query_one("#hint").update(f"Switched to: {tmux_name}")
        else:
            self.query_one("#hint").update(f"Attach: tmux attach -t {tmux_name}")

    @work
    async def action_rename_session(self):
        lst = self.query_one("#list", WrappingListView)
        if not lst.highlighted_child or not isinstance(lst.highlighted_child, SessionItem):
            return

        session = lst.highlighted_child.session
        new_name = await self.push_screen_wait(RenameSessionScreen(session.name))

        if not new_name or new_name == session.name:
            return

        new_tmux_name = f"claude-{new_name}"
        self.terminal.rename_session(session.tmux_session_name, new_tmux_name)
        session.name = new_name
        session.tmux_session_name = new_tmux_name
        self._refresh_list()
        self.query_one("#hint").update(f"Renamed to: {new_name}")

    def action_switch_session(self):
        lst = self.query_one("#list", WrappingListView)
        if not lst.highlighted_child or not isinstance(lst.highlighted_child, SessionItem):
            return

        session = lst.highlighted_child.session

        if self.terminal.switch_to_session(session.tmux_session_name):
            for s in self.sessions:
                s.is_active = (s == session)
            session.last_visited = datetime.now()

            if session.status == Status.READY:
                session.status = Status.READ

            self._refresh_list()
            self.query_one("#hint").update(f"Switched to: {session.tmux_session_name}")
        else:
            self.query_one("#hint").update(f"No tmux client! Run: tmux attach -t {session.tmux_session_name}")

    def action_delete_session(self):
        lst = self.query_one("#list", WrappingListView)
        if not lst.highlighted_child or not isinstance(lst.highlighted_child, SessionItem):
            return

        session = lst.highlighted_child.session

        # Switch to another session before deleting to avoid tmux detach
        if len(self.sessions) > 1:
            idx = self.sessions.index(session)
            target = self.sessions[1 if idx == 0 else 0]

            if self.terminal.switch_to_session(target.tmux_session_name):
                for s in self.sessions:
                    s.is_active = False
                target.is_active = True
                self.query_one("#hint").update(f"Switched to: {target.tmux_session_name}")

        self.terminal.delete_session(session.tmux_session_name)
        self.sessions.remove(session)
        self._refresh_list()


def main():
    CactusApp().run()


if __name__ == "__main__":
    main()
