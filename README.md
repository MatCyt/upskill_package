# upskill-package

Data load package for Google Sheets

## Features

- No authentication dependency: working on vetted Google Sheets link
- Load Google Sheets data in different format

## Installation

Install directly from GitHub using [uv](https://docs.astral.sh/uv/):

```bash
uv add git+https://github.com/MatCyt/upskill_package.git
```

Or add it as a dependency in your `pyproject.toml`:

```toml
dependencies = [
    "upskill-package @ git+https://github.com/MatCyt/upskill_package.git",
]
```

## Usage

```python
from upskill_package import SharePointSiteConn

conn = SharePointSiteConn(
    site_url="https://yourorg.sharepoint.com/sites/yoursite",
    client_id="your-client-id",
    client_secret="your-client-secret",
    tenant_id="your-tenant-id",
    drive_name="Documents",
)

# List files in a folder
files = conn.list_files_in_folder("General/Reports")

# Download a file
content = conn.download_file("drive/root:/General/Reports/report.xlsx")

# Upload a file
with open("local_file.xlsx", "rb") as f:
    conn.upload_file("General/Reports/local_file.xlsx", f.read())

# Delete a file
conn.delete_file("General/Reports/old_report.xlsx")

# Copy a file to another folder
conn.copy_file("General/Reports/report.xlsx", "/General/Archive")
```

## Development

```bash
uv sync
uv run ruff check src/
uv run pytest
```
