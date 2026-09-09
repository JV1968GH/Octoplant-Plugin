---
name: Octoplant
version: 2.3.1
description: "OctoPlant/versiondog MCP-kennis voor gerichte checkout, artifactmirror en gecontroleerde checkoutvrijgave zonder versiecreatie."
---

# Octoplant MCP

De plugin voert de volledige lifecycle voor één component uit: read-only
navigatie, gerichte componentcheckout, artifactmirror en een gecontroleerde
vrijgave van de onveranderde native checkout. Gebruik hiervoor standaard
`checkout_copy_and_release_component`. Die vrijgave vereist directe
gebruikersbevestiging en gebruikt altijd `Enabled=N`, `WithoutComparison=Y`
en `ReleaseAfterCheckIn=Y`. Implementeer nooit maintenance mode, checkout-all
of andere schrijfbewerkingen.

## Gedeelde serverarchive: strikt read-only

De gedeelde RWZI-serverarchive is hardgecodeerd als uitsluitend een bron voor
padresolutie. Maak, wijzig, verwijder, kopieer of spiegel nooit bestanden of
mappen op deze share. Gebruik voor check-outs en bewerkingen uitsluitend de lokale clientarchive en de
door de handoff aangewezen initiële promptworkspace.

## Verplicht begin van elke OctoPlant-sessie

Roep altijd eerst `resolve_project` aan voordat een PLC-project wordt
uitgecheckt. Geef een installatienaam en/of kostenplaats mee, samen met het
PLC-nummer indien bekend.
De tool leest bij elke oproep de actuele gedeelde serverarchive; gebruik dus
geen hardgecodeerde of eerder onthouden mapnamen.

Gebruik `component_path` voor `checkout_copy_and_release_component`. Gebruik
`checkout_component` alleen wanneer de gebruiker uitdrukkelijk vraagt de
native checkout behouden te laten. Gebruik `archive_relative_path` alleen voor
een bestaand INI-veld dat uitdrukkelijk een pad in de gedeelde
filesystemarchive verwacht.

Geef altijd precies één componentpad of component-ID op. Gebruik nooit
`checkout_all`, `--all`, een leeg componentpad of een andere brede checkout.

## Referenties

| Onderwerp | Bestand |
|---|---|
| Archiefscan en rangschikking | [navigation.md](./references/navigation.md) |
| MCP-tools | [mcp-tools.md](./references/mcp-tools.md) |
| Gerichte checkoutbestemming | [checkout.md](./references/checkout.md) |
| Configuratie | [project-structure.md](./references/project-structure.md) |
