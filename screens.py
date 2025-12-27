"""Modal screens for Cactus."""

from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Static, ListItem, ListView, Input
from textual import work

from models import ACCENT_COLOR, generate_random_name, load_paths, delete_path


# Shared modal CSS
MODAL_CSS = f"""
.modal-container {{
    width: 50%;
    min-width: 40;
    max-width: 60;
    height: auto;
    background: $surface;
    border: tall {ACCENT_COLOR} 50%;
    padding: 1 2;
}}

.modal-header {{
    text-align: center;
    color: $text;
    padding: 0 0 1 0;
}}

.modal-title {{
    text-style: bold;
    color: {ACCENT_COLOR};
}}

.modal-subtitle {{
    color: $text-muted;
    text-style: italic;
}}

.input-group {{
    height: auto;
    padding: 0;
}}

.input-label {{
    color: $text-muted;
    padding: 0 0 0 1;
}}

.modal-container Input {{
    margin: 0 0 1 0;
    border: tall {ACCENT_COLOR} 30%;
}}

.modal-container Input:focus {{
    border: tall {ACCENT_COLOR};
}}
"""


class PathPickerScreen(ModalScreen[str | None]):
    """Modal screen for selecting a path from paths.txt."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("d", "delete_path", "Delete"),
    ]

    CSS = f"""
    PathPickerScreen {{
        align: center middle;
    }}

    PathPickerScreen > Vertical {{
        width: 50%;
        min-width: 40;
        max-width: 70;
        height: auto;
        background: $surface;
        border: solid {ACCENT_COLOR};
    }}

    PathPickerScreen > Vertical > ListView {{
        width: 100%;
        height: auto;
        max-height: 12;
        background: $surface;
        padding: 0;
        border: none;
    }}

    PathPickerScreen > Vertical > ListView > ListItem {{
        padding: 0 2;
        background: $surface;
        color: $text-muted;
    }}

    PathPickerScreen > Vertical > ListView > ListItem:hover {{
        color: $text;
    }}

    PathPickerScreen > Vertical > #hint {{
        width: 100%;
        text-align: center;
        padding: 0 1;
        background: $surface;
        color: $text-disabled;
        text-style: italic;
    }}
    """

    def __init__(self, paths: list[str]):
        super().__init__()
        self.paths = paths

    def compose(self):
        with Vertical():
            yield ListView(
                *[ListItem(Static(path)) for path in self.paths],
                id="path-list"
            )
            yield Static("press d to remove a path", id="hint")

    def on_list_view_selected(self, event: ListView.Selected):
        idx = event.list_view.index
        if idx is not None and idx < len(self.paths):
            self.dismiss(self.paths[idx])

    def action_delete_path(self):
        lst = self.query_one("#path-list", ListView)
        if lst.index is not None and lst.index < len(self.paths):
            delete_path(self.paths[lst.index])
            self.paths.pop(lst.index)

            if not self.paths:
                self.dismiss(None)
                return

            lst.clear()
            for path in self.paths:
                lst.append(ListItem(Static(path)))

            if lst.index >= len(self.paths):
                lst.index = len(self.paths) - 1

    def action_cancel(self):
        self.dismiss(None)


class NewSessionScreen(ModalScreen[dict | None]):
    """Modal screen for creating a new session."""

    BINDINGS = [Binding("escape", "cancel", "Cancel")]

    CSS = f"""
    NewSessionScreen {{
        align: center middle;
    }}

    {MODAL_CSS}

    .modal-container {{
        height: 60%;
        min-height: 16;
        max-height: 18;
    }}
    """

    def __init__(self):
        super().__init__()
        self.paths = load_paths()

    def compose(self):
        placeholder = "~/code/my-project" + (" (or @)" if self.paths else "")

        yield Vertical(
            Vertical(
                Static("+ NEW SESSION", classes="modal-title"),
                classes="modal-header",
            ),
            Vertical(
                Static("name", classes="input-label"),
                Input(placeholder="leave blank for random", id="name"),
                Static("directory", classes="input-label"),
                Input(placeholder=placeholder, id="path"),
                classes="input-group",
            ),
            classes="modal-container",
        )

    def on_mount(self):
        self.query_one("#name").focus()

    def on_input_changed(self, event: Input.Changed):
        if event.input.id == "path" and self.paths and "@" in event.value:
            event.input.value = event.value.replace("@", "")
            self._show_path_picker()

    @work
    async def _show_path_picker(self):
        selected = await self.app.push_screen_wait(PathPickerScreen(self.paths))
        if selected:
            name = self.query_one("#name").value.strip() or generate_random_name()
            self.dismiss({"name": name, "path": selected})

    def on_input_submitted(self, event):
        if event.input.id == "name":
            self.query_one("#path").focus()
            return
        name = self.query_one("#name").value.strip() or generate_random_name()
        path = self.query_one("#path").value.strip() or "~"
        self.dismiss({"name": name, "path": path})

    def action_cancel(self):
        self.dismiss(None)


class RenameSessionScreen(ModalScreen[str | None]):
    """Modal screen for renaming a session."""

    BINDINGS = [Binding("escape", "cancel", "Cancel")]

    CSS = f"""
    RenameSessionScreen {{
        align: center middle;
    }}

    {MODAL_CSS}

    .modal-container {{
        min-height: 10;
    }}
    """

    def __init__(self, current_name: str):
        super().__init__()
        self.current_name = current_name

    def compose(self):
        yield Vertical(
            Vertical(
                Static("RENAME SESSION", classes="modal-title"),
                Static("change display name", classes="modal-subtitle"),
                classes="modal-header",
            ),
            Vertical(
                Static("new name", classes="input-label"),
                Input(value=self.current_name, id="name"),
                classes="input-group",
            ),
            classes="modal-container",
        )

    def on_mount(self):
        inp = self.query_one("#name", Input)
        inp.focus()
        inp.action_end()

    def on_input_submitted(self, event):
        new_name = self.query_one("#name").value.strip()
        self.dismiss(new_name if new_name else None)

    def action_cancel(self):
        self.dismiss(None)
