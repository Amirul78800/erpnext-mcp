import os
import json
import logging
from typing import Any, Dict, List, Optional
from mcp.server.fastmcp import FastMCP
from frappe_client import FrappeClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("erpnext-mcp")

# Environment configuration
ERPNEXT_URL = os.getenv("ERPNEXT_URL", "https://erpnext.my-edu.my")
ERPNEXT_API_KEY = os.getenv("ERPNEXT_API_KEY", "")
ERPNEXT_API_SECRET = os.getenv("ERPNEXT_API_SECRET", "")
VERIFY_SSL = os.getenv("ERPNEXT_VERIFY_SSL", "true").lower() in ("true", "1", "yes")
HOST = os.getenv("MCP_HOST", "0.0.0.0")
PORT = int(os.getenv("MCP_PORT", "8000"))

# Initialize Frappe client
client = FrappeClient(
    base_url=ERPNEXT_URL,
    api_key=ERPNEXT_API_KEY,
    api_secret=ERPNEXT_API_SECRET,
    verify_ssl=VERIFY_SSL,
)

# Initialize FastMCP Server
mcp = FastMCP("ERPNext-Operator", host=HOST, port=PORT)

# ---------------------------------------------------------------------------
# Master Data & Inventory Management
# ---------------------------------------------------------------------------

@mcp.tool()
async def erpnext_register_item(
    item_code: str,
    item_name: str,
    item_group: str = "All Item Groups",
    stock_uom: str = "Nos",
    standard_rate: float = 0.0,
    valuation_rate: float = 0.0,
    is_stock_item: int = 1,
    description: Optional[str] = None,
) -> str:
    """Register a new Item record in ERPNext with pricing, UOM, and stock parameters."""
    data = {
        "doctype": "Item",
        "item_code": item_code,
        "item_name": item_name,
        "item_group": item_group,
        "stock_uom": stock_uom,
        "standard_rate": standard_rate,
        "valuation_rate": valuation_rate,
        "is_stock_item": is_stock_item,
        "description": description or item_name,
    }
    doc = await client.create_doc("Item", data)
    return f"Successfully registered Item '{doc.get('name')}' (Code: {doc.get('item_code')}). Standard Rate: RM {standard_rate:.2f}."

@mcp.tool()
async def erpnext_get_stock_balance(item_code: str, warehouse: Optional[str] = None) -> str:
    """Query real-time inventory quantity on hand for an Item across all or specific warehouses."""
    bins = await client.get_stock_balance(item_code, warehouse)
    if not bins:
        return f"No stock records found for Item '{item_code}'."
    
    summary = [f"Stock report for '{item_code}':"]
    total_qty = 0.0
    for b in bins:
        actual = b.get("actual_qty", 0.0)
        total_qty += actual
        summary.append(
            f"- Warehouse: {b.get('warehouse')} | Actual Qty: {actual} | Reserved: {b.get('reserved_qty', 0.0)} | Projected: {b.get('projected_qty', 0.0)}"
        )
    summary.append(f"Total Available Quantity: {total_qty}")
    return "\n".join(summary)

@mcp.tool()
async def erpnext_create_stock_entry(
    purpose: str,
    items: List[Dict[str, Any]],
    from_warehouse: Optional[str] = None,
    to_warehouse: Optional[str] = None,
) -> str:
    """
    Create a Stock Entry in Draft status (docstatus=0).
    Purpose options: 'Material Receipt', 'Material Issue', 'Material Transfer'.
    Each item in items must be a dict: {'item_code': str, 'qty': float, 'basic_rate': float (optional)}.
    """
    stock_items = []
    for itm in items:
        entry = {
            "item_code": itm["item_code"],
            "qty": float(itm["qty"]),
            "basic_rate": float(itm.get("basic_rate", 0.0)),
        }
        if from_warehouse:
            entry["s_warehouse"] = from_warehouse
        if to_warehouse:
            entry["t_warehouse"] = to_warehouse
        stock_items.append(entry)

    data = {
        "doctype": "Stock Entry",
        "purpose": purpose,
        "from_warehouse": from_warehouse,
        "to_warehouse": to_warehouse,
        "items": stock_items,
    }
    doc = await client.create_doc("Stock Entry", data)
    return f"Draft Stock Entry '{doc.get('name')}' created successfully for purpose '{purpose}'. Please review and submit in ERPNext Desk."

# ---------------------------------------------------------------------------
# Sales & Purchasing Management (Draft-First Safety)
# ---------------------------------------------------------------------------

@mcp.tool()
async def erpnext_create_sales_quotation(
    customer: str,
    items: List[Dict[str, Any]],
    valid_till: Optional[str] = None,
) -> str:
    """
    Draft a Sales Quotation for a customer (docstatus=0).
    Items format: [{'item_code': str, 'qty': float, 'rate': float}].
    """
    quotation_items = [
        {"item_code": i["item_code"], "qty": float(i["qty"]), "rate": float(i["rate"])}
        for i in items
    ]
    data = {
        "doctype": "Quotation",
        "quotation_to": "Customer",
        "party_name": customer,
        "valid_till": valid_till,
        "items": quotation_items,
    }
    doc = await client.create_doc("Quotation", data)
    return f"Draft Quotation '{doc.get('name')}' created for Customer '{customer}'. Total: RM {doc.get('grand_total', 0.0):.2f}."

@mcp.tool()
async def erpnext_create_purchase_order(
    supplier: str,
    items: List[Dict[str, Any]],
    schedule_date: Optional[str] = None,
) -> str:
    """
    Draft a Purchase Order for a supplier (docstatus=0).
    Items format: [{'item_code': str, 'qty': float, 'rate': float}].
    """
    po_items = [
        {
            "item_code": i["item_code"],
            "qty": float(i["qty"]),
            "rate": float(i["rate"]),
            "schedule_date": schedule_date,
        }
        for i in items
    ]
    data = {
        "doctype": "Purchase Order",
        "supplier": supplier,
        "schedule_date": schedule_date,
        "items": po_items,
    }
    doc = await client.create_doc("Purchase Order", data)
    return f"Draft Purchase Order '{doc.get('name')}' created for Supplier '{supplier}'. Total: RM {doc.get('grand_total', 0.0):.2f}."

@mcp.tool()
async def erpnext_create_invoice(
    invoice_type: str,
    party: str,
    items: List[Dict[str, Any]],
    due_date: Optional[str] = None,
) -> str:
    """
    Draft an Invoice (docstatus=0).
    invoice_type must be either 'Sales Invoice' or 'Purchase Invoice'.
    party: Customer name (for Sales) or Supplier name (for Purchase).
    """
    if invoice_type not in ("Sales Invoice", "Purchase Invoice"):
        raise ValueError("invoice_type must be either 'Sales Invoice' or 'Purchase Invoice'")

    doctype = invoice_type
    doc_items = [
        {"item_code": i["item_code"], "qty": float(i["qty"]), "rate": float(i["rate"])}
        for i in items
    ]
    data: Dict[str, Any] = {
        "doctype": doctype,
        "due_date": due_date,
        "items": doc_items,
    }
    if doctype == "Sales Invoice":
        data["customer"] = party
    else:
        data["supplier"] = party

    doc = await client.create_doc(doctype, data)
    return f"Draft {doctype} '{doc.get('name')}' generated for '{party}'. Grand Total: RM {doc.get('grand_total', 0.0):.2f}."

# ---------------------------------------------------------------------------
# CRM & Helpdesk Support
# ---------------------------------------------------------------------------

@mcp.tool()
async def erpnext_create_lead(
    lead_name: str,
    email_id: Optional[str] = None,
    mobile_no: Optional[str] = None,
    source: Optional[str] = None,
    notes: Optional[str] = None,
) -> str:
    """Create a new prospective Lead in Frappe CRM."""
    data = {
        "doctype": "Lead",
        "lead_name": lead_name,
        "email_id": email_id,
        "mobile_no": mobile_no,
        "source": source or "AI Agent",
    }
    doc = await client.create_doc("Lead", data)
    if notes:
        await client.create_doc("Note", {"title": f"Notes for {lead_name}", "content": notes})
    return f"Lead '{doc.get('name')}' ({lead_name}) created successfully in CRM."

@mcp.tool()
async def erpnext_create_ticket(
    subject: str,
    raised_by: str,
    priority: str = "Medium",
    description: Optional[str] = None,
) -> str:
    """Create a customer support ticket in Frappe Helpdesk / Issue tracker."""
    data = {
        "doctype": "Issue",
        "subject": subject,
        "raised_by": raised_by,
        "priority": priority,
        "description": description or subject,
    }
    doc = await client.create_doc("Issue", data)
    return f"Support Ticket '{doc.get('name')}' created. Priority: {priority}."

# ---------------------------------------------------------------------------
# HRMS & Employee Management
# ---------------------------------------------------------------------------

@mcp.tool()
async def erpnext_create_leave_application(
    employee: str,
    leave_type: str,
    from_date: str,
    to_date: str,
    description: Optional[str] = None,
) -> str:
    """Submit a Leave Application on behalf of an Employee in Frappe HRMS (Draft status)."""
    data = {
        "doctype": "Leave Application",
        "employee": employee,
        "leave_type": leave_type,
        "from_date": from_date,
        "to_date": to_date,
        "description": description or "Submitted via AI Operator",
    }
    doc = await client.create_doc("Leave Application", data)
    return f"Leave Application '{doc.get('name')}' submitted in Draft for Employee '{employee}' ({from_date} to {to_date})."

# ---------------------------------------------------------------------------
# Universal Frappe DocType Engine
# ---------------------------------------------------------------------------

@mcp.tool()
async def frappe_get_doc(doctype: str, name: str) -> str:
    """Fetch the full JSON content of any Frappe document by its DocType and Name."""
    doc = await client.get_doc(doctype, name)
    return json.dumps(doc, indent=2, default=str)

@mcp.tool()
async def frappe_list_docs(
    doctype: str,
    fields: Optional[List[str]] = None,
    filters_json: Optional[str] = None,
    limit: int = 20,
) -> str:
    """
    List records for any DocType with optional filters.
    filters_json should be a JSON array of filters, e.g. '[["status", "=", "Open"]]'.
    """
    filters = json.loads(filters_json) if filters_json else None
    docs = await client.list_docs(doctype, fields=fields, filters=filters, limit_page_length=limit)
    return json.dumps(docs, indent=2, default=str)

@mcp.tool()
async def frappe_create_doc(doctype: str, data_json: str) -> str:
    """Create any Frappe document dynamically. Enforces Draft mode (docstatus=0)."""
    data = json.loads(data_json)
    data["doctype"] = doctype
    doc = await client.create_doc(doctype, data)
    return f"Created {doctype} record '{doc.get('name')}'."

@mcp.tool()
async def frappe_update_doc(doctype: str, name: str, data_json: str) -> str:
    """Update fields on any existing Frappe document."""
    data = json.loads(data_json)
    doc = await client.update_doc(doctype, name, data)
    return f"Updated {doctype} record '{doc.get('name')}'."

# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logger.info(f"Starting ERPNext MCP Server on {HOST}:{PORT}/sse...")
    mcp.run(transport="sse")
