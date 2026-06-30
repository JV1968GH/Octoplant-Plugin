# MCP-tools — Definitieve scope

Alle toegestane MCP-tools voor de Octoplant MCP server.

## Overzicht

| Tool | Module | Beschrijving | Details |
|------|--------|-------------|---------|
| `authenticate` | `server.py` | Test verbinding en authenticatie via `VDogCheckOut.exe login` | [authentication.md](./authentication.md) |
| `checkout_component` | `src/tools/checkout.py` | Specifiek component uitchecken via `VDogCheckOut.exe` | [checkout.md](./checkout.md) |
| `checkout_all` | `src/tools/checkout.py` | Alle componenten uitchecken via `VDogCheckOut.exe` | [checkout.md](./checkout.md) |
| `start_export` | `src/tools/export.py` | Export-order aanmaken via REST API | [export-api.md](./export-api.md) |
| `get_export_status` | `src/tools/export.py` | Status van een lopende export opvragen | [export-api.md](./export-api.md) |
| `download_export` | `src/tools/export.py` | Afgewerkte export (ZIP) downloaden | [export-api.md](./export-api.md) |
| `cancel_export` | `src/tools/export.py` | Lopende export annuleren | [export-api.md](./export-api.md) |
| `run_export` | `src/tools/export.py` | Start + poll + download in één stap | [export-api.md](./export-api.md) |
| `export_via_cli` | `src/tools/export.py` | Export uitvoeren via `VDogAutoExport.exe` | [export-cli.md](./export-cli.md) |

## ⛔ Verboden tools — nooit implementeren

| Verboden naam | Reden |
|--------------|-------|
| `checkin` / `check_in` | Schrijft data terug naar OctoPlant |
| `maintenance_mode` | Wijzigt serverstatus |
| Elke `write_*` / `update_*` / `delete_*` | Buiten read-only scope |

## Toegestane bewerkingen

| Bewerking | Mechanisme |
|-----------|------------|
| Verbinding testen | `VDogCheckOut.exe login` |
| Check-Out | `VDogCheckOut.exe checkout <pad>` |
| Exporteren | REST API `/v1/order` of `VDogAutoExport.exe` |