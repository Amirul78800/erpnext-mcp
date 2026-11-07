# 🚀 ERPNext Autonomous AI Operator (MCP Server)

[![Build and Publish Docker Image](https://github.com/Amirul78800/erpnext-mcp/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/Amirul78800/erpnext-mcp/actions)
[![Docker Hub](https://img.shields.io/badge/dockerhub-erpnext--mcp-blue?logo=docker&style=flat-square)](https://hub.docker.com/r/amirul123/erpnext-mcp)
[![Docker Pulls](https://img.shields.io/docker/pulls/amirul123/erpnext-mcp?style=flat-square)](https://hub.docker.com/r/amirul123/erpnext-mcp)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)

An enterprise-ready **Model Context Protocol (MCP)** server built for **ERPNext v15/v16**. Designed to run as a multi-arch Docker container on **TrueNAS SCALE** and connect directly to **Antigravity AI**, **Claude**, or any MCP client over HTTP/SSE.

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

## 🛠️ Step 1: Create the Bot User in ERPNext Desk

To maintain a clean audit log and adhere to least-privilege security:

1. Log into your ERPNext instance: `https://erpnext.my-edu.my`.
2. Go to: **Settings ➔ Users ➔ New User**.
   * **Email:** `ai.agent@my-edu.my`
   * **First Name:** `AI Agent`
   * **Role Profile:** Check `System Manager` (or customize granular roles: *Stock Manager*, *Sales Manager*, *HR User*, etc.).
   * Save the user.
3. Scroll down to the **API Access** section on the user page:
   * Click **Generate Keys**.
   * Copy the **API Secret** immediately (it will only be shown once!).
   * Note down both the **API Key** and **API Secret**.

---

## 🚢 Step 2: Deploy to TrueNAS SCALE (via Arcane or Compose)

In **Arcane** or your TrueNAS compose editor, add the `mcp-server` service defined in `compose.fragment.yaml`:

```yaml
services:
  mcp-server:
    image: amirul123/erpnext-mcp:latest
    container_name: erpnext-mcp-server
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      ERPNEXT_URL: "https://erpnext.my-edu.my" # or "http://frontend:8080"
      ERPNEXT_API_KEY: "your_generated_api_key"
      ERPNEXT_API_SECRET: "your_generated_api_secret"
      ERPNEXT_VERIFY_SSL: "true"
      MCP_HOST: "0.0.0.0"
      MCP_PORT: "8000"
```

Save and deploy the stack. The MCP SSE endpoint will now be live at:
```
http://<TRUENAS_IP>:8000/sse
```

---

## ⚡ Step 3: Connect Antigravity to the MCP Server

In Antigravity, add the MCP server configuration to your MCP config:

```json
{
  "mcpServers": {
    "erpnext": {
      "url": "http://<TRUENAS_IP>:8000/sse",
      "transport": "sse"
    }
  }
}
```
*(Replace `<TRUENAS_IP>` with your TrueNAS SCALE local LAN IP address or your Tailscale IP).*

---

## 💬 Step 4: Test Autonomous Operations in Chat

Once connected, you can instruct Antigravity naturally:

### 1. Registering New Items
> *"Register a new Item: Stainless Steel Socket Head Cap Screw M4x16mm. Item code: `FAST-M4-16`, standard rate RM 0.45, stock UOM Nos, item group Hardware."*

### 2. Checking Stock Balance
> *"Check the stock balance for item `FAST-M4-16` across all our warehouses."*

### 3. Creating a Sales Quote
> *"Create a draft quotation for customer 'Pentamaster' with 100 units of `FAST-M4-16` at RM 0.45 each."*

### 4. CRM & Customer Support
> *"Add a new lead: Ahmad Albab, phone 019-8765432, email ahmad@test.com, interested in our equipment design services."*

### 5. HRMS Self-Service
> *"Submit a draft casual leave application for employee 'EMP-001' from 2026-12-01 to 2026-12-03."*

---

## 📄 License

This project is open-source under the [MIT License](LICENSE).
