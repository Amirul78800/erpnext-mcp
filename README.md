# 🚀 ERPNext Autonomous AI Operator (MCP Server)

[![Build and Publish Docker Image](https://github.com/Amirul78800/erpnext-mcp/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/Amirul78800/erpnext-mcp/actions)
[![Docker Hub](https://img.shields.io/badge/dockerhub-erpnext--mcp-blue?logo=docker&style=flat-square)](https://hub.docker.com/r/amirul123/erpnext-mcp)
[![Docker Pulls](https://img.shields.io/docker/pulls/amirul123/erpnext-mcp?style=flat-square)](https://hub.docker.com/r/amirul123/erpnext-mcp)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)

An enterprise-ready **Model Context Protocol (MCP)** server built for **ERPNext v15/v16**. Designed to run as a multi-architecture Docker container (`linux/amd64`, `linux/arm64`) on **TrueNAS SCALE**, **Docker Compose**, **Kubernetes**, or any on-premise/cloud host, connecting directly to **Antigravity AI**, **Claude**, **Cursor**, or any MCP client over HTTP/SSE.

---

## 🌟 Capabilities

| Domain | Available Operations | Safety Policy |
| :--- | :--- | :--- |
| **Inventory & Master Data** | Register Items, configure UOM & pricing, query real-time stock balances across warehouses, create Stock Entries | Live creation for items; Draft (`docstatus=0`) for stock movements |
| **Sales & Purchasing** | Generate Quotations, Purchase Orders, and Sales/Purchase Invoices | **Draft-First (`docstatus=0`)** — Requires human review before posting |
| **CRM & Helpdesk** | Create Leads, attach notes, log support tickets & issues | Immediate entry with audit attribution to Bot User |
| **HRMS** | Submit Leave Applications on behalf of employees | Submitted in Draft status |
| **Universal Frappe Engine** | Fetch (`get_doc`), list with filters (`list_docs`), dynamic record creation & updates | Safe reflection over all standard and custom Frappe DocTypes |

---

## ⚙️ Automated CI/CD Pipeline

This repository features an automated GitHub Actions workflow (`.github/workflows/docker-publish.yml`):
* **On Push to `main`:** Automatically builds multi-architecture images (`linux/amd64` and `linux/arm64`) using Docker Buildx and pushes to:
  * **Docker Hub:** `amirul123/erpnext-mcp:latest`
  * **GitHub Packages:** `ghcr.io/amirul78800/erpnext-mcp:latest`
* **On Semantic Release Tags (e.g. `v1.0.0`):** Automatically tags and publishes immutable release versions.

---

## 🛠️ Step 1: Create the Dedicated Bot User in ERPNext

To maintain a clean audit log and adhere to least-privilege security:

1. Log into your ERPNext instance (`https://erp.example.com`).
2. Navigate to: **Settings ➔ Users ➔ New User**.
   * **Email:** `ai.operator@example.com`
   * **First Name:** `AI Operator`
   * **Role Profile:** Check `System Manager` (or customize granular roles: *Stock Manager*, *Sales Manager*, *HR User*, etc.).
   * Save the user.
3. Scroll down to the **API Access** section on the user page:
   * Click **Generate Keys**.
   * Copy the **API Secret** immediately (it will only be shown once!).
   * Note down both the **API Key** and **API Secret**.

---

## 🚢 Step 2: Deploy Container (Docker Compose / TrueNAS SCALE)

In **Arcane**, **Portainer**, or your Docker Compose file, add the `mcp-server` service:

```yaml
services:
  mcp-server:
    image: amirul123/erpnext-mcp:latest
    container_name: erpnext-mcp-server
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      # If on the same docker network as ERPNext, you can point to http://frontend:8080
      # Or your public/internal HTTPS URL:
      ERPNEXT_URL: "https://erp.example.com"
      ERPNEXT_API_KEY: "your_generated_api_key"
      ERPNEXT_API_SECRET: "your_generated_api_secret"
      ERPNEXT_VERIFY_SSL: "true"
      MCP_HOST: "0.0.0.0"
      MCP_PORT: "8000"
```

Start the container. The MCP Server-Sent Events (SSE) endpoint will be live at:
```
http://<HOST_IP>:8000/sse
```

---

## ⚡ Step 3: Connect Your AI Assistant (Antigravity / Claude / Cursor)

Add the MCP server configuration to your AI client's settings:

```json
{
  "mcpServers": {
    "erpnext": {
      "url": "http://<HOST_IP>:8000/sse",
      "transport": "sse"
    }
  }
}
```
*(Replace `<HOST_IP>` with your host's LAN or Tailscale IP).*

---

## 💬 Step 4: Example Natural Language Prompts

Once connected, your AI assistant can autonomously execute ERP operations:

### 1. Registering New Items
> *"Register a new Item: Stainless Steel Socket Head Cap Screw M4x16mm. Item code: `FAST-M4-16`, standard rate 0.45, stock UOM Nos, item group Hardware."*

### 2. Checking Stock Balance
> *"Check the current stock balance for item `FAST-M4-16` across all warehouses."*

### 3. Creating a Sales Quote
> *"Create a draft quotation for customer 'Acme Corp' with 100 units of `FAST-M4-16` at 0.45 each."*

### 4. CRM & Customer Support
> *"Add a new lead: Alex Wong, phone +60123456789, email alex@example.com, interested in our manufacturing equipment."*

### 5. HRMS Self-Service
> *"Submit a draft casual leave application for employee 'EMP-001' from 2026-12-01 to 2026-12-03."*

---

## 🙏 Acknowledgements & References

This project builds upon the open-source efforts of the Frappe and AI ecosystems:

* **[Model Context Protocol (MCP)](https://modelcontextprotocol.io/)** — Anthropic's open protocol for connecting AI assistants to data sources and tools.
* **[Frappe Framework](https://github.com/frappe/frappe) & [ERPNext](https://github.com/frappe/erpnext)** — The open-source ERP system created and maintained by Frappe Technologies.
* **Community Prior Art & Inspirations:**
  * [frappe/mcp](https://github.com/frappe/mcp) — Frappe's official native MCP implementation.
  * [rakeshgangwar/erpnext-mcp-server](https://github.com/rakeshgangwar/erpnext-mcp-server) — TypeScript-based REST MCP implementation.
  * [Casys-AI/mcp-erpnext](https://github.com/Casys-AI/mcp-erpnext) — Exploration of interactive Deno/TypeScript ERPNext MCP tools.
  * [buildswithpaul/Frappe_Assistant_Core](https://github.com/buildswithpaul/Frappe_Assistant_Core) — ERPNext LLM middleware architecture.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
