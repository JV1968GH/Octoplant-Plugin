# Check-Out — VDogCheckOut.exe

Check-Out van componenten via de `VDogCheckOut.exe` wrapper. Authenticatie en credentials
zijn **intern afgehandeld** door de executable — de AI geeft enkel het componentpad mee.

## Gebruik

```
VDogCheckOut.exe checkout <component_path>
VDogCheckOut.exe checkout --id <component_id>
VDogCheckOut.exe checkout --all
VDogCheckOut.exe <component_path>           ← checkout is het standaard subcommand
```

## Opties

| Optie | Beschrijving |
|-------|-------------|
| `<component_path>` | Relatief componentpad **met leading backslash** (bijv. `\RWZI's\100026 - Dendermonde\...`) |
| `--id <id>` | Component-ID als alternatief voor pad |
| `--all` | Alle beschikbare componenten uitchecken |
| `--backups` | Backups meenemen |
| `--version <n>` | Specifiek versienummer uitchecken |
| `--comment <text>` | Opmerking in het CheckIn-CheckOut-Log |
| `--skip-mirror` | Geen robocopy-stap na checkout |

## Return codes

| Code | Betekenis |
|------|-----------|
| `0` | Succes |
| `1` | Algemene fout |
| `2` | Geen componenten gevonden |
| `10` | Configuratiefout |
| `1000` | Authenticatiefout |

## Executable locatie

```
binaryTools\VDogCheckOut\publish\VDogCheckOut.exe
```

## ⚠️ Verplichte leading backslash

Het componentpad **moet** beginnen met een backslash, anders geeft `VDogAutoCheckOut.exe`
foutcode 20043:

```
✅  \RWZI's\100026 - Dendermonde\100026 - Dendermonde, PLC08_CE
❌  RWZI's\100026 - Dendermonde\100026 - Dendermonde, PLC08_CE
```

## ⚠️ Bekende beperking: archive-pad

`VDogAutoCheckOut.exe` (intern gebruikt) verbindt automatisch met de lokale
checkout-service op poort 64002, geconfigureerd tijdens de versiondog client-installatie.
Het archive-pad (`OCTOPLANT_ARCHIVE_PATH` in `.env`) moet overeenkomen met die installatie.

## ⛔ Beschermingsregel: geen hercheck-out als component al in archive staat

| Situatie | Actie |
|----------|-------|
| Component bestaat **niet** in archive | Checkout uitvoeren + mirror |
| Component bestaat **wel** in archive, maar **niet** in checkout | Alleen mirror (geen checkout) |
| Component bestaat **in beide** | Niets doen — al beschikbaar |

## Post-checkout mirror (robocopy)

Na checkout wordt de subtree gespiegeld naar `OCTOPLANT_CHECKOUT_PATH`:

```
robocopy "<OCTOPLANT_ARCHIVE_PATH>\<component_path>"
         "<OCTOPLANT_CHECKOUT_PATH>\<component_path>"
         /MIR /R:1 /W:1 /NFL /NDL /NP
```

## MCP-tools

| Tool | Beschrijving |
|------|-------------|
| `checkout_component` | Specifiek component uitchecken |
| `checkout_all` | Alle beschikbare componenten uitchecken |

## Navigatie archiefstructuur

Zie [navigation.md](./navigation.md) voor het bepalen van het juiste componentpad.