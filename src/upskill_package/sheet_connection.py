"""Simple connector for reading public Google Sheets as CSV."""

from __future__ import annotations

import csv
import io

import httpx

_EXPORT_BASE_URL = "https://docs.google.com/spreadsheets/d/{sheet_id}/export"


class GoogleSheetsConnector:
    """Read-only connector for public Google Sheets exported as CSV."""

    def __init__(self, sheet_id: str, sheet_name: str | None = None) -> None:
        """Initialize the connector.

        Args:
            sheet_id: The unique identifier from the Google Sheets URL.
            sheet_name: Optional worksheet name. Defaults to the first sheet.
        """
        self.sheet_id = sheet_id
        self.sheet_name = sheet_name

    def _build_url(self) -> str:
        """Build the CSV export URL for the configured sheet.

        Returns:
            The fully-formed export URL.
        """
        url = f"{_EXPORT_BASE_URL.format(sheet_id=self.sheet_id)}?format=csv"
        if self.sheet_name:
            url += f"&sheet={self.sheet_name}"
        return url

    def fetch_raw(self) -> str:
        """Fetch the sheet contents as a raw CSV string.

        Returns:
            The CSV text.

        Raises:
            httpx.HTTPStatusError: If the HTTP request fails.
        """
        response = httpx.get(self._build_url(), follow_redirects=True)
        response.raise_for_status()
        return response.text

    def fetch_as_dicts(self) -> list[dict[str, str]]:
        """Fetch the sheet contents as a list of row dictionaries.

        The first row is used as column headers.

        Returns:
            A list of dictionaries mapping column names to cell values.
        """
        reader = csv.DictReader(io.StringIO(self.fetch_raw()))
        return list(reader)

    def fetch_as_rows(self) -> list[list[str]]:
        """Fetch the sheet contents as a list of rows.

        Returns:
            A list of lists, where each inner list is a row of cell values.
        """
        reader = csv.reader(io.StringIO(self.fetch_raw()))
        return list(reader)
