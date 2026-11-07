import json
import logging
import urllib.parse
from typing import Any, Dict, List, Optional
import httpx

logger = logging.getLogger("frappe_client")

class FrappeClient:
    """
    Robust REST API client for ERPNext / Frappe Framework v15/v16.
    Handles Token-based authentication, standardized error parsing,
    and automatic draft (docstatus=0) protection.
    """

    def __init__(
        self,
        base_url: str,
        api_key: str,
        api_secret: str,
        verify_ssl: bool = True,
        timeout: float = 30.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.api_secret = api_secret
        self.verify_ssl = verify_ssl
        self.timeout = timeout
        self.headers = {
            "Authorization": f"token {self.api_key}:{self.api_secret}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def _parse_error(self, response: httpx.Response) -> str:
        try:
            data = response.json()
            if "_server_messages" in data:
                messages = json.loads(data["_server_messages"])
                clean_messages = []
                for msg in messages:
                    try:
                        parsed = json.loads(msg)
                        clean_messages.append(parsed.get("message", str(parsed)))
                    except Exception:
                        clean_messages.append(str(msg))
                return "; ".join(clean_messages)
            if "exception" in data:
                return data["exception"].split("\n")[-2] if "\n" in data["exception"] else data["exception"]
            if "message" in data:
                return str(data["message"])
            return response.text
        except Exception:
            return f"HTTP {response.status_code}: {response.text}"

    async def get_doc(self, doctype: str, name: str) -> Dict[str, Any]:
        """Fetch a single document by DocType and Name."""
        encoded_name = urllib.parse.quote(name, safe="")
        url = f"{self.base_url}/api/resource/{doctype}/{encoded_name}"
        async with httpx.AsyncClient(verify=self.verify_ssl, timeout=self.timeout) as client:
            res = await client.get(url, headers=self.headers)
            if res.status_code != 200:
                raise RuntimeError(f"Failed to fetch {doctype} '{name}': {self._parse_error(res)}")
            return res.json().get("data", {})

    async def list_docs(
        self,
        doctype: str,
        fields: Optional[List[str]] = None,
        filters: Optional[List[Any]] = None,
        limit_page_length: int = 20,
        order_by: str = "creation desc",
    ) -> List[Dict[str, Any]]:
        """List documents for a DocType with optional filters and field projections."""
        url = f"{self.base_url}/api/resource/{doctype}"
        params: Dict[str, Any] = {
            "limit_page_length": limit_page_length,
            "order_by": order_by,
        }
        if fields:
            params["fields"] = json.dumps(fields)
        if filters:
            params["filters"] = json.dumps(filters)

        async with httpx.AsyncClient(verify=self.verify_ssl, timeout=self.timeout) as client:
            res = await client.get(url, headers=self.headers, params=params)
            if res.status_code != 200:
                raise RuntimeError(f"Failed to list {doctype}: {self._parse_error(res)}")
            return res.json().get("data", [])

    async def create_doc(self, doctype: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new document in ERPNext. Enforces Draft mode (docstatus=0) for safety."""
        url = f"{self.base_url}/api/resource/{doctype}"
        # Ensure transactional documents are created in Draft status
        data["docstatus"] = 0
        async with httpx.AsyncClient(verify=self.verify_ssl, timeout=self.timeout) as client:
            res = await client.post(url, headers=self.headers, json=data)
            if res.status_code not in (200, 201):
                raise RuntimeError(f"Failed to create {doctype}: {self._parse_error(res)}")
            return res.json().get("data", {})

    async def update_doc(self, doctype: str, name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update fields on an existing document."""
        encoded_name = urllib.parse.quote(name, safe="")
        url = f"{self.base_url}/api/resource/{doctype}/{encoded_name}"
        async with httpx.AsyncClient(verify=self.verify_ssl, timeout=self.timeout) as client:
            res = await client.put(url, headers=self.headers, json=data)
            if res.status_code != 200:
                raise RuntimeError(f"Failed to update {doctype} '{name}': {self._parse_error(res)}")
            return res.json().get("data", {})

    async def get_stock_balance(self, item_code: str, warehouse: Optional[str] = None) -> List[Dict[str, Any]]:
        """Query real-time stock balances across warehouses from the Bin doctype."""
        filters = [["item_code", "=", item_code]]
        if warehouse:
            filters.append(["warehouse", "=", warehouse])

        fields = ["warehouse", "actual_qty", "reserved_qty", "ordered_qty", "projected_qty", "valuation_rate"]
        return await self.list_docs("Bin", fields=fields, filters=filters, limit_page_length=50)

    async def call_method(self, method: str, data: Optional[Dict[str, Any]] = None) -> Any:
        """Call a whitelisted Frappe API method."""
        url = f"{self.base_url}/api/method/{method}"
        async with httpx.AsyncClient(verify=self.verify_ssl, timeout=self.timeout) as client:
            if data:
                res = await client.post(url, headers=self.headers, json=data)
            else:
                res = await client.get(url, headers=self.headers)
            if res.status_code != 200:
                raise RuntimeError(f"API method '{method}' failed: {self._parse_error(res)}")
            return res.json().get("message", res.json())
