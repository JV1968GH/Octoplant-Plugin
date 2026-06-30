# Ontwikkelrichtlijnen

Codestandaarden en -richtlijnen voor de Octoplant MCP server.

## Architectuur

- Alle OctoPlant-aanroepen (REST én CLI-subprocess) verlopen via `OctoplantClient` in `src/client.py`
- MCP-tools zijn dunne wrappers in `src/tools/checkout.py` en `src/tools/export.py`
- Gebruik de **MCP Python SDK** (`mcp` package) als basis voor de server
- Credentials worden **nooit** doorgegeven aan of zichtbaar gemaakt voor het MCP-protocol

## Configuratie

- Configuratie via `.env`-bestand (zie [project-structure.md](./project-structure.md))
- Geen gebruikersnamen, wachtwoorden of credential-paden in skill-documentatie of tool-responses

## Foutafhandeling

- Return codes `VDogCheckOut.exe` en `VDogAutoCheckOut.exe`: `0`=OK, `1`=fout, `2`=geen componenten, `10`=config-fout, `1000`=authenticatiefout
- Gooi duidelijke Python-exceptions per return code
- REST API: gebruik **nooit** `raise_for_status()` — gebruik `_raise_sanitised(resp)` uit `src/client.py`
  zodat server-URL en response-body niet in exception-messages lekken; enkel HTTP-statuscode wordt doorgegeven

## Security — LLM blootstelling beperken

- De binary is **volledig stil**: alle foutmeldingen (authenticatie, configuratie, subprocess) worden
  weggegooid en resulteren uitsluitend in een exit code
- Ruwe `stdout`/`stderr` van `VDogAutoCheckOut.exe` en `VDogAutoExport.exe` wordt gecaptured maar
  **niet** doorgegeven aan MCP-responses (`binary_output_suppressed: true`)
- Bearer tokens, OAuth payloads en credentials mogen nooit gelogd, geprint of geretourneerd worden
- Retourneer enkel gestructureerde, gesaniteerde velden (`returncode`, `status`, `success`, domeinspecifieke metadata)
- Nooit `os.environ` of `.env`-inhoud in tool-responses opnemen

## Asynchrone export

- Poll elke ~1 seconde tot `done=true`
- Implementeer timeout na configureerbaar aantal seconden
- Annuleer de order bij timeout via `cancel_export`

## Codekwaliteit

- Type-annotaties verplicht voor alle publieke functies
- Docstrings verplicht voor alle publieke functies en klassen
- SSL: `verify`-parameter configureerbaar via `OCTOPLANT_SSL_VERIFY`, standaard `True`

## Testen

- Test met mock-responses; geen live OctoPlant-verbinding nodig voor unit tests
- Testbestanden: `tests/test_checkout.py`, `tests/test_export.py`
- Mock `subprocess.run` voor CLI-aanroepen
- Mock `httpx` of `requests` voor REST API-aanroepen