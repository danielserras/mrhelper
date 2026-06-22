from typing import Any, Dict, List, Optional

import httpx


class GitLabClient:

    def __init__(self, url: str, token: str) -> None:
        self.base_url = url.rstrip("/") + "/api/v4"
        self.headers = {"PRIVATE-TOKEN": token}
        self.client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self.client is None:
            self.client = httpx.AsyncClient(headers=self.headers, follow_redirects=True)
        return self.client

    async def close(self) -> None:
        if self.client:
            await self.client.aclose()
            self.client = None

    async def get(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        client = await self._get_client()
        r = await client.get(f"{self.base_url}/{endpoint.lstrip('/')}", params=params)
        r.raise_for_status()
        return r.json()

    async def get_paginated(self, endpoint: str, params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        if params is None:
            params = {}
        results = []
        page = 1

        while True:
            params.update({"page": page, "per_page": 100})
            client = await self._get_client()
            r = await client.get(f"{self.base_url}/{endpoint.lstrip('/')}", params=params)
            r.raise_for_status()
            data = r.json()

            if not isinstance(data, list):
                break

            results.extend(data)

            if len(data) < 100:
                break  # última página

            page += 1

        return results

    async def fetch_merge_requests(self, user: str) -> List[dict]:
        all_mrs = []
        page = 1
        client = await self._get_client()

        while True:
            params = {
                "author_username": user,
                "scope": "all",
                "state": "opened",
                "per_page": 50,
                "page": page,
            }
            r = await client.get(f"{self.base_url}/merge_requests", params=params)
            r.raise_for_status()
            resp = r.json()
            if not resp:
                break
            all_mrs.extend(resp)

            next_page = r.headers.get("X-Next-Page")
            if not next_page or next_page == "":
                break
            page = int(next_page)
        return all_mrs

    async def fetch_approvals(self, project_id: int, mr_iid: int) -> dict:
        return await self.get(f"projects/{project_id}/merge_requests/{mr_iid}/approvals")

    async def fetch_comments(self, project_id: int, mr_iid: int) -> list:
        return await self.get_paginated(f"projects/{project_id}/merge_requests/{mr_iid}/notes")

    async def fetch_details(self, project_id: int, mr_iid: int) -> dict:
        return await self.get(f"projects/{project_id}/merge_requests/{mr_iid}")

    async def fetch_pipelines(self, project_id: int, mr_iid: int) -> dict[str, Any]:
        return await self.get(f"projects/{project_id}/merge_requests/{mr_iid}/pipelines")

    async def fetch_project(self, project_id: int) -> dict:
        return await self.get(f"projects/{project_id}")
