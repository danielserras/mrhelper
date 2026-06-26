from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import Header, Footer, Static, DataTable, Input

from ui.footer import build_footer_label


def create_table() -> DataTable:
    table = DataTable()
    table.cursor_type = "row"
    add_columns(table)
    return table


def add_columns(table: DataTable) -> None:
    table.add_column("Author", key="author")
    table.add_column("Project", key="project")
    table.add_column("Title", key="title")
    table.add_column("Approves", key="approves")
    table.add_column("Approved", key="approved")
    table.add_column("Reviewed", key="reviewed")
    table.add_column("Comments", key="comments")
    table.add_column("Created at", key="created")
    table.add_column("Conflicts", key="conflicts")
    table.add_column("Compile", key="compile")


def build_layout(table: DataTable, status: Static, gitlab_username: str | None = None) -> ComposeResult:
    yield Header()
    yield Footer()
    yield status
    yield Input(placeholder="Search MRs (title, author)... (Press Enter to search)", id="search-input")
    yield Container(table, id="table-container", classes="grow")
    yield Static(build_footer_label(), id="author-label")
