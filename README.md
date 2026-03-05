# Taegis Case Manager (v1.0.1)

A production-ready, single-file Tkinter GUI application for managing Taegis Investigations (V2).  
Supports pagination, multi-select with reliable checkboxes, investigation status updates,  
and posting investigation comments using a tenant‑specific explicit GraphQL mutation.

This is the stable **v1.0.1 production release**.

---

## Features
- Investigation listing (V2) with pagination
- Robust checkbox selection model (per‑row + global Select All / Clear All)
- Status updates via `updateInvestigationV2(input: { id, status })`
- Optional comment posting via explicit mutation: `createInvestigationComment(investigation_id: ID!, body: String!)`
- Automatic label→enum mapping (“Open” → “OPEN”)
- Scrollable error details dialog + persistent logging
- Region picker (Charlie / Delta / Foxtrot / Echo)
- Version displayed in title, Help dialog, and footer

---

## Requirements
- Python 3.9+
- Tkinter (standard library)
- `taegis_sdk_python`
- Environment variables:
- `CLIENT_ID`
- `CLIENT_SECRET`
- `BASE_URL` (from region picker)

---

## Installation

```bash
git clone https://github.com/<your-user>/taegis-case-manager.git
cd taegis-case-manager
pip install -r requirements.txt

