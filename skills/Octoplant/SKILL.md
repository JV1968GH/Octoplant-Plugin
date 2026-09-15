---
name: Octoplant
version: 3.0.3
description: "Eenvoudige OctoPlant/versiondog-handoff voor een veilige lokale projectkopie zonder versiecreatie."
---

# Octoplant MCP

De plugin voert de veilige lifecycle voor één component uit: read-only
navigatie, gerichte checkout, lokale artifactmirror en een gecontroleerde
vrijgave van de onveranderde native checkout. De vrijgave gebruikt altijd
`Enabled=N`, `WithoutComparison=Y` en `ReleaseAfterCheckIn=Y`. Implementeer nooit maintenance mode, checkout-all
of andere schrijfbewerkingen.

## Gedeelde serverarchive: strikt read-only

De gedeelde RWZI-serverarchive is hardgecodeerd als uitsluitend een bron voor
padresolutie. Maak, wijzig, verwijder, kopieer of spiegel nooit bestanden of
mappen op deze share. Gebruik voor check-outs en bewerkingen uitsluitend de
lokale clientarchive en de door de handoff aangewezen initiële promptworkspace.

## Gedeelde handoff

Een gebruiker of orchestrator geeft één zichtbaar blok aan Octoplant.
Een installatie of kostenplaats is vereist; voeg het PLC-nummer
toe als het bekend is. Een lokale projectkopie vereist bovendien een absolute
workspace.

```text
⬇️✋ HANDOFF naar Octoplant
Actie: project lokaal beschikbaar maken
Installatie: {installatienaam}
Kostenplaats: {kostenplaats}
PLC: {PLC-naam of nummer}
Workspace: C:\pad\naar\de\hoofdworkspace
Extra guardrails: {optioneel}
Verwachte resultaten: {optioneel}
```

Octoplant resolveert altijd eerst de actuele serverarchive en behandelt
daarna precies één component. Hij gebruikt voor een lokale kopie de
gecombineerde checkout-, mirror- en versieloze-vrijgaveflow. Er zijn geen
downstream APG- of Control Expert-stappen.

## Resultaat

Octoplant logt de volledige ontvangen handoff ongewijzigd in zijn eigen
delegate-sessie en sluit af met één zichtbaar, beknopt JVAI-bericht:

`↩️<terminal state> van Octoplant`

Gebruik uitsluitend:

| State | Betekenis |
| --- | --- |
| ✅ COMPLETED | Lokale projectkopie is beschikbaar en de onveranderde native checkout is versieloos vrijgegeven. |
| ❓ NEEDS_INPUT | Details of een eenduidig doel ontbreken. |
| ❌ FAILED | De actie kon niet worden voltooid. |
| 🛑 UNSAFE | De handoff vraagt een verboden actie. |

Bij ✅ COMPLETED bevat het bericht uitsluitend een niet-sensitieve samenvatting
en `Lokaal project: <pad>`, gevolgd door één JSON-payload met uitsluitend die
veilige resultaten. Andere uitkomsten bevatten eveneens een korte,
niet-sensitieve toelichting en een minimale JSON-payload. Geef nooit
credentials, configuratiegegevens, archiefdetails, binaire uitvoer of interne
lifecyclegegevens weer.

## Referenties

| Onderwerp | Bestand |
|---|---|
| Archiefscan en rangschikking | [navigation.md](./references/navigation.md) |
| MCP-tools | [mcp-tools.md](./references/mcp-tools.md) |
| Gerichte checkoutbestemming | [checkout.md](./references/checkout.md) |
| Configuratie | [project-structure.md](./references/project-structure.md) |
