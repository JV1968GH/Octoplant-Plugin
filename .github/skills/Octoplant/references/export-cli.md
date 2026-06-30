# Export via CLI — VDogAutoExport.exe

Alternatieve exportmethode via CLI-subprocess, gestuurd door een INI-parameterbestand.
Authenticatie is intern afgehandeld door de MCP-server.

## Command syntax (intern)

```
VDogAutoExport.exe
  /rd:{pad naar client archive}
  /CFile:{pad naar INI-parameterbestand}
  [/token:{access token}]
```

> Authenticatie verloopt intern via een OAuth2-token. Credentials zijn niet zichtbaar
> voor het MCP-protocol.

## Parameters (voor AI relevant)

| Parameter | Verplicht | Beschrijving |
|-----------|-----------|-------------|
| `/rd:` | ✅ | Pad naar client archive (`OCTOPLANT_ARCHIVE_PATH`) |
| `/CFile:` | ✅ | Pad naar INI-configuratiebestand met exportinstellingen |

## Executable locatie

Automatisch gevonden via standaard installatiemap of `PATH`.
Optioneel te overriden via `OCTOPLANT_VDOG_CLIENT_PATH` in `.env`.

## MCP-tool

| Tool | Beschrijving |
|------|-------------|
| `export_via_cli` | Export uitvoeren via `VDogAutoExport.exe` met INI-bestand |

## Implementatie

- `src/tools/export.py` — `export_via_cli` tool definitie
- `OctoplantClient.export_via_cli()` in `src/client.py` — subprocess aanroep