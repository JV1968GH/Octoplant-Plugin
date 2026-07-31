---
name: Octoplant
version: 0.6.2
description: "OctoPlant/versiondog MCP-kennis voor read-only projectnavigatie in de gedeelde serverarchive en CLI-checkout. Gebruik voor installaties, kostenplaatsen, PLC-projecten, ARCHIVE, RWZI's, PS, resolve_project en VDogAutoCheckOut.exe."
---

# Octoplant MCP

De plugin biedt uitsluitend read-only navigatie en check-out.
Implementeer nooit check-in, maintenance mode of andere schrijfbewerkingen.

## Gedeelde serverarchive: strikt read-only

De gedeelde RWZI-serverarchive is hardgecodeerd als uitsluitend een bron voor
padresolutie. Maak, wijzig, verwijder, kopieer of spiegel nooit bestanden of
mappen op deze share. Gebruik voor check-outs en bewerkingen uitsluitend de
lokale clientarchive en `octoPlantCheckouts` in de sessieworkspace.

## Verplicht begin van elke OctoPlant-sessie

Roep altijd eerst `resolve_project` aan voordat een PLC-project wordt
uitgecheckt. Geef een installatienaam en/of kostenplaats mee, samen met het
PLC-nummer indien bekend.
De tool leest bij elke oproep de actuele gedeelde serverarchive; gebruik dus
geen hardgecodeerde of eerder onthouden mapnamen.

Gebruik `component_path` voor `checkout_component`. Gebruik
`archive_relative_path` alleen voor een bestaand INI-veld dat uitdrukkelijk
een pad in de gedeelde filesystemarchive verwacht.

## Referenties

| Onderwerp | Bestand |
|---|---|
| Archiefscan en rangschikking | [navigation.md](./references/navigation.md) |
| MCP-tools | [mcp-tools.md](./references/mcp-tools.md) |
| Checkout en workspacemirror | [checkout.md](./references/checkout.md) |
| Configuratie | [project-structure.md](./references/project-structure.md) |
