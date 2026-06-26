import asyncio
import json
import webbrowser
import sys
from pathlib import Path
from textwrap import dedent

from textual.app import App, ComposeResult
from textual.widgets import Static, Input, Footer
from textual.containers import Container

from client.GitLabClient import GitLabClient
from models.MergeRequest import MergeRequest
from ui.MergeRequestRow import MergeRequestRow
from ui.footer import build_footer_label
from ui.layout import build_layout, create_table, add_columns

class MRHelper(App):
    CSS_PATH = str(Path(__file__).parent / 'mrhelper.tcss')
    BINDINGS = [
        ('q', 'quit', 'Quit'),
        ('u', 'update', 'Update MRs'),
        ('v', 'open_link', 'View MR'),
        ('t', 'toggle_title', 'Toggle Full Title'),
        ('r', 'mark_seen', 'Mark as reviewed'),
        ('s', 'focus_search', 'Search MRs'),
    ]
    SEMAPHORE = asyncio.Semaphore(20)
    IGNORED_TARGET_BRANCH_PREFIXES = ("release/",)
    
    if getattr(sys, 'frozen', False):
        BIN_DIR = Path(sys.executable).parent
    else:
        BIN_DIR = Path(__file__).resolve().parent

    CACHE_FILE = BIN_DIR / '.mr_seen_cache.json'

    def __init__(self, GITLAB_URL=None, GITLAB_TOKEN=None, GITLAB_USERS=None, GITLAB_MY_USERNAME=None):
        super().__init__()
        self.client = GitLabClient(GITLAB_URL, GITLAB_TOKEN)
        self.table = create_table()
        self.status = Static('Press [b]U[/b] to update', id='status')
        self.filtered_user = None
        self.show_full_title = False
        self.mr_data = []
        self.GITLAB_USERS = GITLAB_USERS if GITLAB_USERS else []
        self.GITLAB_MY_USERNAME = GITLAB_MY_USERNAME
        self._search_task = None

    def compose(self) -> ComposeResult:
        yield Static(r"""
             __  __ ____  _   _      _                 
            |  \/  |  _ \| | | | ___| |_ __   ___ _ __ 
            | |\/| | |_) | |_| |/ _ \ | '_ \ / _ \ '__|
            | |  | |  _ <|  _  |  __/ | |_) |  __/ |   
            |_|  |_|_| \_\_| |_|\___|_| .__/ \___|_|   
                                      |_|                                                      
        """, id="logo")
        yield Footer()
        yield self.status
        yield Input(placeholder="Search MRs (title, author)... (Press Enter to search)", id="search-input")
        yield Container(self.table, id="table-container", classes="grow")
        yield Static(self.footer_label, id="author-label")

    @property
    def footer_label(self) -> str:
        return build_footer_label()

    async def on_mount(self) -> None:
        self.set_focus(self.table)
        self.seen_cache = self.load_seen_cache()
        self.mr_data = await self.fetch_all_mrs()
        await self.update_table_data()
        self.run_worker(self.poll_updates(), name="poll_updates", exclusive=False)

    async def poll_updates(self) -> None:
        while True:
            await asyncio.sleep(30 * 60)
            new_data = await self.fetch_all_mrs()
            self.mr_data = new_data
            await self.update_table_data()

    async def on_shutdown(self) -> None:
        await self.client.close()

    async def action_update(self) -> None:
        self.status.update('🔄 Updating merge requests...')
        await self.refresh_data()
        self.status.update('✅ Updated — press [b]U[/b] to update')

    async def action_open_link(self) -> None:
        mr = self.get_selected_mr()
        if mr is not None:
            webbrowser.open(str(mr.web_url))

    async def action_toggle_title(self) -> None:
        self.show_full_title = not self.show_full_title
        self.table.clear(columns=True)
        add_columns(self.table)

        for mr in self.mr_data:
            key = self.get_mr_key(mr)
            seen = mr.iid in self.seen_cache.get(str(mr.project_id), [])
            row = MergeRequestRow.from_merge_request(mr, self.show_full_title, seen)
            self.table.add_row(*row, key=key)
        self.table.columns['title'].width = None
        self.table.refresh()
        self.set_focus(self.table)

    async def action_focus_search(self) -> None:
        self.query_one("#search-input", Input).focus()

    async def action_mark_seen(self) -> None:
        mr = self.get_selected_mr()
        if mr is None:
            return

        pid = str(mr.project_id)
        self.seen_cache.setdefault(pid, [])
        if mr.iid not in self.seen_cache[pid]:
            self.seen_cache[pid].append(mr.iid)
            self.save_seen_cache(self.seen_cache)
            self.status.update(f'✅ Marked MR !{mr.iid} as reviewed.')
            await self.update_table_data()
        else:
            self.seen_cache[pid].remove(mr.iid)
            self.save_seen_cache(self.seen_cache)
            self.status.update(f'❌ Marked MR !{mr.iid} as not reviewed.')
            await self.update_table_data()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "search-input":
            query = event.value.lower()
            
            all_mr_map = {f"{mr.iid}-{mr.project_id}": mr for mr in self.mr_data}
            should_be_visible = {
                f"{mr.iid}-{mr.project_id}" 
                for mr in self.mr_data
                if query in mr.title.lower() or query in mr.author.lower()
            }
            current_keys = set(self.table.rows.keys())

            for key in current_keys - should_be_visible:
                self.table.remove_row(key)
                
            for key in should_be_visible - current_keys:
                mr = all_mr_map[key]
                seen = mr.iid in self.seen_cache.get(str(mr.project_id), [])
                self.table.add_row(*MergeRequestRow.from_merge_request(mr, self.show_full_title, seen), key=key)
                
            self.set_focus(self.table)

    async def fetch_all_mrs(self) -> list[MergeRequest]:
        users = [self.filtered_user] if self.filtered_user else self.GITLAB_USERS
        all_mrs_lists = await asyncio.gather(*(self.client.fetch_merge_requests(user) for user in users))
        all_mrs = [
            mr
            for sublist in all_mrs_lists
            for mr in sublist
            if not self.should_ignore_mr(mr)
        ]

        async def enrich_mr(mr) -> MergeRequest:
            async with self.SEMAPHORE:
                project_id = mr['project_id']
                iid = mr['iid']
                try:
                    approvals, comments, details, pipelines, project = await asyncio.gather(
                        self.client.fetch_approvals(project_id, iid),
                        self.client.fetch_comments(project_id, iid),
                        self.client.fetch_details(project_id, iid),
                        self.client.fetch_pipelines(project_id, iid),
                        self.client.fetch_project(project_id)
                    )
                    pipeline_status = pipelines[0]['status'] if pipelines else 'unknown'
                    project_name = project.get('name', '-')
                except Exception as e:
                    approvals = comments = details = {}
                    pipeline_status = 'unknown'
                    project_name = '-'

                return MergeRequest.from_gitlab_data(
                    mr=mr,
                    approvals=approvals,
                    comments=list(filter(lambda c: c.get('system') == False, comments)),
                    details=details,
                    pipeline_status=pipeline_status,
                    project_name=project_name
                )

        detailed_mrs = await asyncio.gather(*(enrich_mr(mr) for mr in all_mrs))
        detailed_mrs.sort(key=lambda mr: mr.created_at, reverse=True)
        return detailed_mrs

    def should_ignore_mr(self, mr: dict) -> bool:
        target_branch = mr.get("target_branch", "")
        return target_branch.startswith(self.IGNORED_TARGET_BRANCH_PREFIXES)

    def get_mr_key(self, mr: MergeRequest) -> str:
        return f"{mr.iid}-{mr.project_id}"

    def get_selected_mr(self) -> MergeRequest | None:
        if not self.table.row_count:
            return None

        selected_key = None
        try:
            cell_key = self.table.coordinate_to_cell_key(self.table.cursor_coordinate)
            selected_key = self.normalize_row_key(cell_key.row_key)
        except Exception:
            cursor_row = self.table.cursor_row
            row_keys = list(self.table.rows.keys())
            if cursor_row is not None and cursor_row < len(row_keys):
                selected_key = self.normalize_row_key(row_keys[cursor_row])

        if selected_key is None:
            return None

        for mr in self.mr_data:
            if self.get_mr_key(mr) == selected_key:
                return mr

        return None

    @staticmethod
    def normalize_row_key(row_key) -> str:
        return str(getattr(row_key, "value", row_key))

    async def refresh_data(self):
        self.mr_data = await self.fetch_all_mrs()
        await self.update_table_data()

    async def update_table_data(self) -> None:
        self.table.clear()
        for mr in self.mr_data:
            key = self.get_mr_key(mr)
            seen = mr.iid in self.seen_cache.get(str(mr.project_id), [])
            self.table.add_row(*MergeRequestRow.from_merge_request(mr, self.show_full_title, seen), key=key)
        self.set_focus(self.table)

    def load_seen_cache(self) -> dict[int, list[int]]:
        if self.CACHE_FILE.exists():
            return json.loads(self.CACHE_FILE.read_text())
        return {}

    def save_seen_cache(self, data: dict[int, list[int]]):
        self.CACHE_FILE.write_text(json.dumps(data, indent=2))
