---
name: Octoplant
description: "Octoplant MCP project kennis: OctoPlant/versiondog API (authenticatie, checkout, export), archiefstructuur & padresolutie (RWZI's, PS, kostplaats, PLC-nummer), MCP-tools scope, ontwikkelrichtlijnen en projectstructuur. Gebruik bij implementeren van authenticate, checkout_component, checkout_all, start_export, get_export_status, download_export, cancel_export, export_via_cli, OctoplantClient, of vragen over de REST API, VDogAutoCheckOut.exe, VDogAutoExport.exe, OAuth2 token endpoint, .env configuratie, mapstructuur of componentpad bepalen."
---

# Octoplant — MCP Server voor OctoPlant / versiondog

MCP-server in Python die AI-assistenten **read-only** toegang geeft tot OctoPlant/versiondog.

> 📖 OctoPlant docs: https://info.octoplant.com/octoplant-info/public/en/main/

## ⛔ Strikte scope — NOOIT implementeren

- `checkin` / `check_in` — schrijft data terug
- `maintenance_mode` — wijzigt serverstatus
- Elke bewerking die data terugschrijft of de server configureert



## Referenties per functionaliteit

| Onderwerp | Bestand |
|-----------|---------|
| OAuth2 authenticatie (token endpoint, headers) | [authentication.md](./references/authentication.md) |
| Check-Out via CLI (`VDogAutoCheckOut.exe`, return codes) | [checkout.md](./references/checkout.md) |
| Archiefstructuur & padresolutie (RWZI's, PS, kostplaats, PLC) | [navigation.md](./references/navigation.md) |
| Export via REST API (asynchroon, poll, download) | [export-api.md](./references/export-api.md) |
| Export via CLI (`VDogAutoExport.exe`) | [export-cli.md](./references/export-cli.md) |
| MCP-tools definitie (alle 8 tools) | [mcp-tools.md](./references/mcp-tools.md) |
| Ontwikkelrichtlijnen & codestandaarden | [dev-guidelines.md](./references/dev-guidelines.md) |
| Projectstructuur & `.env` configuratie | [project-structure.md](./references/project-structure.md) |

## Technische stack (snel overzicht)

| Component | Keuze |
|-----------|-------|
| Taal | Python (Anaconda) |
| Protocol | Model Context Protocol (MCP SDK) |
| API-target | OctoPlant native API op poort `64023` |
| Runtime | Lokaal, Windows |
| Centrale client | `src/client.py` → `OctoplantClient` |
