---
name: Octoplant
version: 2.3.4
description: "Eenvoudige OctoPlant/versiondog-handoff voor een veilige lokale projectkopie zonder versiecreatie."
---

# Octoplant MCP

De plugin voert de veilige lifecycle voor één component uit: read-only
navigatie, gerichte checkout, lokale artifactmirror en een gecontroleerde
vrijgave van de onveranderde native checkout. De vrijgave vereist directe
gebruikersbevestiging en gebruikt altijd `Enabled=N`, `WithoutComparison=Y`
en `ReleaseAfterCheckIn=Y`. Implementeer nooit maintenance mode, checkout-all
of andere schrijfbewerkingen.

## Gedeelde serverarchive: strikt read-only

De gedeelde RWZI-serverarchive is hardgecodeerd als uitsluitend een bron voor
padresolutie. Maak, wijzig, verwijder, kopieer of spiegel nooit bestanden of
mappen op deze share. Gebruik voor check-outs en bewerkingen uitsluitend de
lokale clientarchive en de door de handoff aangewezen initiële promptworkspace.

## Gedeelde handoff

Een gebruiker of orchestrator geeft één zichtbaar blok aan de Octoplant
Specialist. Een installatie of kostenplaats is vereist; voeg het PLC-nummer
toe als het bekend is. Een lokale projectkopie vereist bovendien een absolute
workspace en directe bevestiging.

```text
⬇️✋ HANDOFF — OctoPlant
Actie: project lokaal beschikbaar maken
Installatie: {installatienaam}
Kostenplaats: {kostenplaats}
PLC: {PLC-naam of nummer}
Workspace: C:\pad\naar\de\hoofdworkspace
Bevestiging: ja
```

De specialist resolveert altijd eerst de actuele serverarchive en behandelt
daarna precies één component. Hij gebruikt voor een bevestigde lokale kopie de
gecombineerde checkout-, mirror- en versieloze-vrijgaveflow. Er zijn geen
downstream APG- of Control Expert-stappen.

## Resultaat

De specialist sluit af met één zichtbaar, beknopt bericht:

`↩️ RESULTAAT — <terminal state>`

Gebruik uitsluitend:

| State | Betekenis |
| --- | --- |
| ✅ COMPLETED | Lokale projectkopie is beschikbaar en de onveranderde native checkout is versieloos vrijgegeven. |
| 🔎 NOT_FOUND | Geen overeenkomstig project gevonden. |
| ❓ NEEDS_INPUT | Details, bevestiging of een eenduidig doel ontbreken. |
| ⚠️ BLOCKED | Lokale configuratie blokkeert de actie. |
| ❌ FAILED | De actie kon niet worden voltooid. |
| 🛑 UNSAFE | De handoff vraagt een verboden actie. |

Bij ✅ COMPLETED bevat het bericht uitsluitend een niet-sensitieve samenvatting
en `Lokaal project: <pad>`. Andere uitkomsten bevatten alleen een korte,
niet-sensitieve toelichting. Geef nooit JSON, toolpayloads, credentials,
configuratiegegevens, archiefdetails, binaire uitvoer of interne
lifecyclegegevens weer.

## Referenties

| Onderwerp | Bestand |
|---|---|
| Archiefscan en rangschikking | [navigation.md](./references/navigation.md) |
| MCP-tools | [mcp-tools.md](./references/mcp-tools.md) |
| Gerichte checkoutbestemming | [checkout.md](./references/checkout.md) |
| Configuratie | [project-structure.md](./references/project-structure.md) |
