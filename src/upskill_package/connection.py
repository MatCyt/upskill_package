"""SharePoint site connection and file operations via Microsoft Graph API."""

import io
import logging

import requests

logger = logging.getLogger(__name__)

HTTP_OK = 200
HTTP_CREATED = 201
HTTP_NO_CONTENT = 204
DEFAULT_TIMEOUT = 30


class SharePointSiteConn:
    """Client for interacting with a SharePoint site through the Microsoft Graph API."""

    def __init__(self, site_url: str, client_id: str, client_secret: str, tenant_id: str, drive_name: str) -> None:
        """Initialize connection to a SharePoint site.

        Args:
            site_url: Full URL of the SharePoint site.
            client_id: Azure AD application (client) ID.
            client_secret: Azure AD client secret.
            tenant_id: Azure AD tenant ID.
            drive_name: Name of the document library (drive) to use.

        Raises:
            ConnectionError: If authentication, site lookup, or drive lookup fails.
        """
        self.site_url = site_url
        self.client_id = client_id
        self.client_secret = client_secret
        self.tenant_id = tenant_id
        self.drive_name = drive_name
        self.access_token = self._get_token()
        self.site_id = self._get_site_id()
        self.drive_id = self._get_drive_id()

    def _get_token(self) -> str:
        """Obtain an OAuth2 access token using client credentials flow.

        Returns:
            The access token string.

        Raises:
            ConnectionError: If the token cannot be obtained.
        """
        auth_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
        token_data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": "https://graph.microsoft.com/.default",
        }

        try:
            token_response = requests.post(auth_url, data=token_data, timeout=DEFAULT_TIMEOUT)

            if token_response.status_code == HTTP_OK:
                access_token = token_response.json().get("access_token")
                if access_token:
                    return access_token
                msg = "Response did not contain an access token"
                raise ConnectionError(msg)
            msg = f"Failed to obtain access token. Status: {token_response.status_code}, Error: {token_response.text}"
            raise ConnectionError(msg)
        except requests.RequestException as e:
            msg = f"Token request failed: {e}"
            raise ConnectionError(msg) from e

    def _get_site_id(self) -> str:
        """Retrieve the SharePoint site ID using the site URL.

        Returns:
            The site ID string.

        Raises:
            ConnectionError: If the site ID cannot be retrieved.
        """
        url_parts = self.site_url.replace("https://", "").split("/", 1)
        hostname = url_parts[0]
        site_path = "/" + url_parts[1] if len(url_parts) > 1 else ""

        headers = {"Authorization": f"Bearer {self.access_token}", "Content-Type": "application/json"}

        endpoint = f"https://graph.microsoft.com/v1.0/sites/{hostname}:{site_path}"
        try:
            response = requests.get(endpoint, headers=headers, timeout=DEFAULT_TIMEOUT)
            response.raise_for_status()
            site_id = response.json().get("id")
        except requests.RequestException as e:
            msg = f"Failed to retrieve site ID: {e}"
            raise ConnectionError(msg) from e

        if not site_id:
            msg = f"Site ID not found for URL: {self.site_url}"
            raise ConnectionError(msg)
        return site_id

    def _get_drive_id(self) -> str:
        """Retrieve the ID of a specific document library (drive) by its name.

        Returns:
            The drive ID string.

        Raises:
            ConnectionError: If the drive cannot be found or retrieved.
        """
        drives_endpoint = f"https://graph.microsoft.com/v1.0/sites/{self.site_id}/drives"
        headers = {"Authorization": f"Bearer {self.access_token}", "Content-Type": "application/json"}

        try:
            response = requests.get(drives_endpoint, headers=headers, timeout=DEFAULT_TIMEOUT)
            response.raise_for_status()
            drives = response.json().get("value", [])
        except requests.RequestException as e:
            msg = f"Failed to retrieve drives: {e}"
            raise ConnectionError(msg) from e

        for drive in drives:
            if drive.get("name") == self.drive_name:
                return drive.get("id")

        msg = f"Drive named '{self.drive_name}' not found"
        raise ConnectionError(msg)

    def download_file(self, file_path: str) -> io.BytesIO | None:
        """Download a file from the SharePoint site given its path.

        Args:
            file_path: Path to the file within the SharePoint site
                (e.g., "drive/root:/folder/filename.xlsx").

        Returns:
            The file content as a BytesIO object, or None on failure.
        """
        file_endpoint = f"https://graph.microsoft.com/v1.0/sites/{self.site_id}/{file_path}"

        headers = {"Authorization": f"Bearer {self.access_token}", "Content-Type": "application/json"}
        try:
            response = requests.get(file_endpoint, headers=headers, timeout=DEFAULT_TIMEOUT)
            download_url = response.json().get("@microsoft.graph.downloadUrl")
            download_response = requests.get(download_url, timeout=DEFAULT_TIMEOUT)
            return io.BytesIO(download_response.content)
        except requests.RequestException:
            logger.exception("File download failed")
            return None

    def upload_file(self, file_path: str, file_content: bytes) -> None:
        """Upload a file to the SharePoint site at the specified path.

        Args:
            file_path: Destination path within SharePoint (e.g., "folder/filename.xlsx").
            file_content: The file content as bytes (e.g., buffer.getvalue()).
        """
        upload_endpoint = f"https://graph.microsoft.com/v1.0/drives/{self.drive_id}/root:/{file_path}:/content"

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/octet-stream",
        }

        try:
            response = requests.put(upload_endpoint, headers=headers, data=file_content, timeout=DEFAULT_TIMEOUT)
            if response.status_code in (HTTP_OK, HTTP_CREATED):
                logger.info("File uploaded successfully to '%s'.", file_path)
            else:
                logger.error(
                    "File upload failed with status code %s: %s",
                    response.status_code,
                    response.text,
                )
        except requests.RequestException:
            logger.exception("File upload failed")

    def delete_file(self, file_path: str) -> None:
        """Delete a file from the SharePoint site.

        Args:
            file_path: Path to the file to delete within the drive.
        """
        delete_endpoint = f"https://graph.microsoft.com/v1.0/drives/{self.drive_id}/root:/{file_path}"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        try:
            response = requests.delete(delete_endpoint, headers=headers, timeout=DEFAULT_TIMEOUT)
            if response.status_code == HTTP_NO_CONTENT:
                logger.info("File deleted successfully from '%s'.", file_path)
            else:
                logger.error(
                    "File deletion failed with status code %s: %s",
                    response.status_code,
                    response.text,
                )
        except requests.RequestException:
            logger.exception("File deletion failed")

    def copy_file(self, source_file_path: str, target_folder_path: str) -> None:
        """Copy a file to a different folder within the SharePoint site.

        Args:
            source_file_path: Path to the source file.
            target_folder_path: Path to the target folder.
        """
        file_endpoint = f"https://graph.microsoft.com/v1.0/sites/{self.site_id}/drive/root:/{source_file_path}"
        move_data = {"parentReference": {"path": f"/drive/root:{target_folder_path}"}}
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        try:
            response = requests.patch(file_endpoint, json=move_data, headers=headers, timeout=DEFAULT_TIMEOUT)
            if response.status_code == HTTP_OK:
                logger.info("File moved successfully.")
            else:
                logger.error("File move failed: %s - %s", response.status_code, response.text)
        except requests.RequestException:
            logger.exception("Moving file failed")

    def list_files_in_folder(self, folder_path: str) -> list[str]:
        """List all file names in a SharePoint folder.

        Args:
            folder_path: Path to the folder within the drive.

        Returns:
            A list of file names, or an empty list on failure.
        """
        list_endpoint = f"https://graph.microsoft.com/v1.0/drives/{self.drive_id}/root:/{folder_path}:/children"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        try:
            response = requests.get(list_endpoint, headers=headers, timeout=DEFAULT_TIMEOUT)
            response.raise_for_status()
            items = response.json().get("value", [])
        except requests.RequestException:
            logger.exception("Listing files failed")
            return []
        else:
            return [i["name"] for i in items if "file" in i]
