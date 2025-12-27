"""UI widgets for Cactus."""

from textual.widgets import Static, ListItem, ListView

from models import Session, format_time_ago


class SessionItem(ListItem):
    """List item displaying a session with status indicator."""

    def __init__(self, session: Session):
        super().__init__()
        self.session = session
        self._cached_label = None
        self._cached_highlighted = None

    def compose(self):
        yield Static(id="session-label")

    def on_mount(self):
        self._update_label()

    def watch_highlighted(self, highlighted: bool):
        if self._cached_highlighted != highlighted:
            self._cached_highlighted = highlighted
            self._update_label()

    def _update_label(self):
        if not self.is_attached:
            return

        try:
            label = self.query_one("#session-label", Static)
        except Exception:
            return

        # Indicator: highlighted > active > normal
        if self.highlighted:
            indicator = "→"
        elif self.session.is_active:
            indicator = "*"
        else:
            indicator = " "

        left_side = f"{indicator} [{self.session.status.value}]●[/] {self.session.name}"

        time_ago = "-" if self.session.is_active else format_time_ago(self.session.last_visited)
        right_side = f"[dim]{time_ago}[/dim]"

        # Calculate padding
        left_plain = f"{indicator} ● {self.session.name}"
        try:
            width = self.parent.size.width if self.parent else 80
        except:
            width = 80
        padding = max(1, width - len(left_plain) - len(time_ago) - 2)

        final_label = f"{left_side}{' ' * padding}{right_side}"

        if self._cached_label != final_label:
            self._cached_label = final_label
            label.update(final_label)


class WrappingListView(ListView):
    """ListView with circular/wrapping navigation."""

    def action_cursor_up(self) -> None:
        if not self.children:
            return
        idx = self.index if self.index is not None else 0
        if idx == 0:
            self.index = len(self.children) - 1
        else:
            super().action_cursor_up()

    def action_cursor_down(self) -> None:
        if not self.children:
            return
        idx = self.index if self.index is not None else 0
        if idx >= len(self.children) - 1:
            self.index = 0
        else:
            super().action_cursor_down()
