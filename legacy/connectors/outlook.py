"""Office 365 Email Connector — fetches emails via Microsoft Graph API."""

import json
import os
from datetime import datetime
from pathlib import Path

import msal
import requests

from models.schemas import Platform, SourceMetadata


GRAPH_BASE = "https://graph.microsoft.com/v1.0"
SCOPES = ["Mail.Read", "User.Read"]
CURSOR_FILE = ".outlook_cursor"
TOKEN_CACHE_FILE = ".msal_token_cache.json"


class OutlookConnector:
    """Fetches emails from Office 365 using delegated (device code) auth.

    Usage:
        connector = OutlookConnector(pipeline, tenant_id, client_id)
        connector.authenticate()  # interactive device code flow (first time)
        count = connector.fetch_emails(since="2026-01-01")
    """

    def __init__(self, pipeline, tenant_id: str, client_id: str):
        self.pipeline = pipeline
        self.tenant_id = tenant_id
        self.client_id = client_id

        # Set up MSAL with token cache
        self._cache = msal.SerializableTokenCache()
        cache_path = Path(TOKEN_CACHE_FILE)
        if cache_path.exists():
            self._cache.deserialize(cache_path.read_text())

        self._app = msal.PublicClientApplication(
            client_id=client_id,
            authority=f"https://login.microsoftonline.com/{tenant_id}",
            token_cache=self._cache,
        )
        self._token: str | None = None

    def authenticate(self) -> bool:
        """Authenticate via device code flow. Returns True on success."""
        # Try cached token first
        accounts = self._app.get_accounts()
        if accounts:
            result = self._app.acquire_token_silent(SCOPES, account=accounts[0])
            if result and "access_token" in result:
                self._token = result["access_token"]
                self._save_cache()
                return True

        # Device code flow — user opens browser and enters code
        flow = self._app.initiate_device_flow(scopes=SCOPES)
        if "user_code" not in flow:
            raise RuntimeError(f"Device flow failed: {flow.get('error_description')}")

        print(flow["message"])  # "To sign in, use a web browser to open..."
        result = self._app.acquire_token_by_device_flow(flow)

        if "access_token" in result:
            self._token = result["access_token"]
            self._save_cache()
            return True

        raise RuntimeError(f"Auth failed: {result.get('error_description')}")

    def fetch_emails(self, since: str | None = None, max_pages: int = 10) -> int:
        """Fetch emails from inbox and process through pipeline.

        Args:
            since: ISO date string (YYYY-MM-DD). Defaults to last cursor.
            max_pages: Maximum pages to fetch (50 emails per page).

        Returns:
            Number of emails processed.
        """
        if not self._token:
            raise RuntimeError("Not authenticated. Call authenticate() first.")

        # Load cursor if no since date provided
        if since is None:
            since = self._load_cursor()

        headers = {"Authorization": f"Bearer {self._token}"}
        params = {
            "$top": 50,
            "$orderby": "receivedDateTime asc",
            "$select": "id,subject,bodyPreview,body,from,receivedDateTime,conversationId",
        }
        if since:
            params["$filter"] = f"receivedDateTime ge {since}T00:00:00Z"

        url = f"{GRAPH_BASE}/me/messages"
        total = 0

        for page in range(max_pages):
            resp = requests.get(url, headers=headers, params=params if page == 0 else None)
            resp.raise_for_status()
            data = resp.json()

            messages = data.get("value", [])
            for msg in messages:
                self._process_message(msg)
                total += 1

            # Follow pagination
            url = data.get("@odata.nextLink")
            if not url:
                break
            params = None  # nextLink includes all params

        # Save cursor
        if total > 0 and messages:
            last_date = messages[-1].get("receivedDateTime", "")[:10]
            self._save_cursor(last_date)

        return total

    def _process_message(self, msg: dict):
        """Extract fields from Graph API message and push to pipeline."""
        sender = msg.get("from", {}).get("emailAddress", {})
        body = msg.get("body", {}).get("content", msg.get("bodyPreview", ""))
        received = msg.get("receivedDateTime", "")

        # Parse datetime
        try:
            received_dt = datetime.fromisoformat(received.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            received_dt = datetime.now()

        self.pipeline.process_text(
            text=body,
            source_id=msg.get("id", ""),
            platform=Platform.OUTLOOK,
            sender_name=sender.get("name", "Unknown"),
            sender_email=sender.get("address", "unknown@unknown.com"),
            received_at=received_dt,
        )

    def _save_cache(self):
        if self._cache.has_state_changed:
            Path(TOKEN_CACHE_FILE).write_text(self._cache.serialize())

    def _load_cursor(self) -> str | None:
        path = Path(CURSOR_FILE)
        if path.exists():
            return path.read_text().strip()
        return None

    def _save_cursor(self, date_str: str):
        Path(CURSOR_FILE).write_text(date_str)
