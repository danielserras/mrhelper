# MrHelper

MrHelper is a terminal UI for monitoring GitLab merge requests. It fetches open
merge requests for configured GitLab users, enriches them with approvals,
comments, pipeline status, project details, and merge conflict information, then
shows everything in a Textual table.

## Features

- Monitor open merge requests authored by one or more GitLab users.
- Show project, author, title, approvals, comments, creation date, conflicts,
  and pipeline status.
- Search merge requests by title or author.
- Open the selected merge request in a browser.
- Toggle between shortened and full merge request titles.
- Mark merge requests as reviewed using a local cache.
- Poll GitLab periodically for updates.

## Requirements

- Python 3.13
- A GitLab personal access token with permission to read merge requests,
  projects, notes, approvals, and pipelines.

Install the Python dependencies from `requirements.txt`:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Configuration

MrHelper reads configuration from a `.env` file in the project directory when run
from source. When packaged as an executable, it reads `.env` from the executable
directory.

Required variables:

```env
GITLAB_URL=https://gitlab.example.com
GITLAB_TOKEN=your-token
GITLAB_USERS=user1,user2,user3
GITLAB_MY_USERNAME=your-username
```

You can create or update the `.env` file interactively:

```powershell
python main.py config
```

Do not commit `.env`; it contains credentials.

## Run From Source

Start the app with:

```powershell
python main.py
```

or:

```powershell
python main.py run
```

Show CLI help:

```powershell
python main.py help
```

## Keyboard Controls

- `U`: Update merge requests.
- `S`: Focus the search input.
- `Enter`: Run the search when the search input is focused.
- `V`: Open the selected merge request in a browser.
- `T`: Toggle full or shortened titles.
- `R`: Mark the selected merge request as reviewed or not reviewed.
- `Q`: Quit.

## Create an Executable

Install PyInstaller in your virtual environment if it is not already installed:

```powershell
pip install pyinstaller
```

Build the executable:

```powershell
pyinstaller mrhelper.spec
```

The generated executable is written to:

```text
dist\mrhelper.exe
```

Place a `.env` file next to `mrhelper.exe` before running it:

```text
dist\.env
dist\mrhelper.exe
```

Then run:

```powershell
.\dist\mrhelper.exe
```

The reviewed merge request cache is stored next to the executable as
`.mr_seen_cache.json`.

## Development Notes

- Source entry point: `main.py`
- Textual app: `app.py`
- GitLab API client: `client/GitLabClient.py`
- Merge request model: `models/MergeRequest.py`
- UI helpers: `ui/`
- Textual CSS: `mrhelper.tcss`

Generated build output, virtual environments, `.env`, local caches, logs, and
editor settings should not be committed.
