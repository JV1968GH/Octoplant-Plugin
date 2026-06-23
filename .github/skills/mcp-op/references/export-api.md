# Export via REST API

De Export API werkt **asynchroon**: start → poll → download.

## Endpoints

| Stap | Methode | Endpoint |
|------|---------|----------|
| Start export | `POST` | `/v1/order` |
| Poll status | `GET` | `/v1/order/{name}` |
| Download ZIP | `GET` | `/v1/order/{name}/download` |
| Annuleer | `POST` | `/v1/order/{name}/cancel` |

## Export starten — JSON body

```json
POST /v1/order
Authorization: Bearer {token}
Content-Type: application/json

{
  "projectTree": true,
  "jobList": true,
  "jobResults": true,
  "usersAndGroups": false,
  "componentTypes": false,
  "componentLog": false,
  "eventLog": false,
  "adminLog": false,
  "linkedLibraries": false,
  "usageInfo": false
}
```

### Exportbare inhoudstypen

| Sleutel | Beschrijving |
|---------|-------------|
| `projectTree` | Projectboom |
| `jobList` | Takenlijst |
| `jobResults` | Taakresultaten (met/zonder diffs) |
| `usersAndGroups` | Gebruikers en groepen |
| `componentTypes` | Componenttypes |
| `componentLog` | Componentlog |
| `eventLog` | Eventlog |
| `adminLog` | Adminlog |
| `linkedLibraries` | Gekoppelde standaardbibliotheken |
| `usageInfo` | Gebruiksinformatie |

## Polling-logica

Poll elke **~1 seconde** tot `done=true` in de GET-response:

```python
while not status["done"]:
    time.sleep(1)
    status = client.get_export_status(order_name)
```

## MCP-tools

| Tool | Endpoint |
|------|----------|
| `start_export` | `POST /v1/order` |
| `get_export_status` | `GET /v1/order/{name}` |
| `download_export` | `GET /v1/order/{name}/download` |
| `cancel_export` | `POST /v1/order/{name}/cancel` |

## Implementatie

- `src/tools/export.py` — MCP-tool definities
- `OctoplantClient.start_export()`, `.get_export_status()`, `.download_export()`, `.cancel_export()` in `src/client.py`
