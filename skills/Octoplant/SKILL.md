---
name: Octoplant
version: 2.2.1
description: "OctoPlant/versiondog MCP-kennis voor read-only projectnavigatie in de gedeelde serverarchive en CLI-checkout. Gebruik voor installaties, kostenplaatsen, PLC-projecten, ARCHIVE, RWZI's, PS, resolve_project en VDogAutoCheckOut.exe."
---

# Octoplant MCP

De plugin biedt uitsluitend read-only navigatie en gerichte componentcheckout.
Implementeer nooit check-in, maintenance mode, checkout-all of andere
schrijfbewerkingen. Checkout-all kan de lokale schijfruimte uitputten en is
daarom uitdrukkelijk verboden, ook wanneer de native client die optie biedt.

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

Gebruik `component_path` voor `checkout_component`. Gebruik
`archive_relative_path` alleen voor een bestaand INI-veld dat uitdrukkelijk
een pad in de gedeelde filesystemarchive verwacht.

Geef altijd precies één componentpad of component-ID op. Gebruik nooit
`checkout_all`, `--all`, een leeg componentpad of een andere brede checkout.

Roep na `resolve_project` altijd `inspect_checkout_destination` aan met
dezelfde initiële handoff-workspace en installatiegegevens. Als de status
`existing_checkout_detected` is, vraag expliciet om precies één keuze:
`replace` (alleen het gemelde lokale artifactpad verwijderen en vers
uitchecken), `reuse` (de bestaande lokale versie retourneren) of `stop`
(ongewijzigd stoppen). Roep bij een bestaande checkout nooit
`checkout_component` zonder deze expliciete keuze aan.

## Referenties

| Onderwerp | Bestand |
|---|---|
| Archiefscan en rangschikking | [navigation.md](./references/navigation.md) |
| MCP-tools | [mcp-tools.md](./references/mcp-tools.md) |
| Gerichte checkoutbestemming | [checkout.md](./references/checkout.md) |
| Configuratie | [project-structure.md](./references/project-structure.md) |
