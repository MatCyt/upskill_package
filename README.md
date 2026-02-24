# upskill-package

Simple connector for reading public Google Sheets as CSV.

## Features

- No authentication required — works with any publicly shared Google Sheet
- Fetch data as raw CSV, list of rows, or list of dictionaries
- Lightweight — only depends on `httpx`

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
from upskill_package import GoogleSheetsConnector

connector = GoogleSheetsConnector(sheet_id="your-sheet-id")

# Fetch as a list of dictionaries (first row = headers)
rows = connector.fetch_as_dicts()

# Fetch as a list of lists
rows = connector.fetch_as_rows()

# Fetch raw CSV string
csv_text = connector.fetch_raw()

# Fetch a specific worksheet by name
connector = GoogleSheetsConnector(sheet_id="your-sheet-id", sheet_name="Sheet2")
rows = connector.fetch_as_dicts()
```

## Development

```bash
uv sync
uv run ruff check src/
uv run pytest
```
