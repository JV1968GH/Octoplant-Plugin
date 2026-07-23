# Octoplant — MCP Plugin voor OctoPlant/versiondog

MCP-server die AI-assistenten (GitHub Copilot, Claude Desktop, …) **read-only** toegang geeft tot
OctoPlant/versiondog: componenten uitchecken en projectdata exporteren.

**Release:** 0.4.0

> **Scope:** uitsluitend check-out en export. Check-in en maintenance mode zijn bewust uitgesloten.

---

## Vereisten

| Component | Versie | Download |
|-----------|--------|----------|
| Git | recent | https://git-scm.com |
| Anaconda of Miniconda | recent | https://www.anaconda.com |
| .NET SDK | 10+ | https://dotnet.microsoft.com/download |
| versiondog client | geïnstalleerd | via IT / OctoPlant beheerder |

---

## Installatie

### Stap 1 — Repository klonen

```powershell
git clone https://github.com/JV1968GH/Octoplant-Plugin.git
cd Octoplant-Plugin
```

### Stap 2 — Eenmalig installatiescript uitvoeren

```powershell
.\scripts\install.ps1
```

Dit script:
- Maakt de conda-omgeving `mcp-op` aan (Python 3.12)
- Installeert alle Python-dependencies
- Bouwt `VDogCheckOut.exe` (.NET, self-contained)
- Maakt een leeg `.env`-bestand aan als dat nog niet bestaat

### Stap 3 — `.env` aanpassen

Open `.env` en vul de waarden in voor dit toestel:

```ini
OCTOPLANT_SERVER=https://jouw-server:64023
OCTOPLANT_ARCHIVE_PATH=D:\vdClientArchive
OCTOPLANT_SERVER_ARCHIVE_PATH=\\pOctoplan1\poctoplan1_D\vdServerArchive
# Optioneel; leeg laten gebruikt auto-discover
OCTOPLANT_VDOG_CLIENT_PATH=
OCTOPLANT_SSL_VERIFY=false
# Configureerbaar pad naar credentials-database (default)
ACCESS_RIGHTS_DB_PATH=%LOCALAPPDATA%\Programs\AccessRightsManager\access-rights.db
```

> Gebruikersnaam en wachtwoord staan **niet** in `.env`.

### Stap 4 — Verbinding testen

```powershell
.\binaryTools\VDogCheckOut\publish\VDogCheckOut.exe login
```

| Exit code | Betekenis |
|-----------|-----------|
| `0` | Verbinding en authenticatie geslaagd ✅ |
| `1` | Verbindingsfout |
| `10` | Configuratiefout (.env of vereiste variabele ontbreekt) |
| `1000` | Authenticatie mislukt (controleer credentials) |

### Stap 5 — VS Code openen

```powershell
code .
```

De MCP-server start automatisch via `.vscode/mcp.json`.

---

## Activeren in VS Code

De server is geconfigureerd in `.vscode/mcp.json` en start automatisch wanneer je de
workspace opent. Je ziet de server als **MCP_OP** verschijnen in de Copilot-chat.

Bij problemen:
1. Controleer of de conda-omgeving `mcp-op` bestaat: `conda env list`
2. Controleer of `VDogCheckOut.exe` aanwezig is in `binaryTools\VDogCheckOut\publish\`
3. Test de verbinding: `VDogCheckOut.exe login`
4. Controleer de VS Code Output → "MCP" voor serverlogboeken

---

## Beschikbare tools (AI-commando's)

### `authenticate`
Test de verbinding en authenticatie met de OctoPlant server.

```
authenticate()
→ { success: true, returncode: 0 }
```

### `checkout_component`
Check een specifiek PLC-component of project uit vanuit OctoPlant.

```
checkout_component(
    component_path = "\RWZI's\{installatiemap}\{PLC-project}"
)
```

> ⚠️ Het pad begint altijd met een backslash.
> Padformaat: `\{rootmap}\{kostplaats} - {naam}\{kostplaats} - {naam}, PLC{##}_CE`

Parameters:

| Parameter | Type | Beschrijving |
|-----------|------|-------------|
| `component_path` | string | Relatief componentpad (met leading `\`) |
| `component_id` | string | Component-ID als alternatief voor pad |
| `with_backups` | bool | Backups meenemen (standaard: false) |
| `number_of_archives` | int | Aantal archives (0 = alle) |
| `version` | int | Specifiek versienummer (standaard: huidig) |
| `with_std_libs` | bool | Standaardbibliotheken meenemen |
| `comment` | string | Opmerking in het CheckIn-CheckOut-Log |

### `checkout_all`
Check alle toegankelijke componenten uit.

```
checkout_all()
checkout_all(with_backups=true)
```

### `resolve_project`
Roep deze tool aan bij de start van elke OctoPlant-sessie, vóór een CLI-export
of check-out. Hij leest de gedeelde serverarchive telkens opnieuw, gebruikt
standaard `RWZI's`, en zoekt in `ARCHIVE` naar het beste PLC-project.

```
resolve_project(cost_center="100026", plc_name="PLC08")
→ {
    component_path: "\RWZI's\{installatiemap}\{PLC-project}",
    archive_relative_path: "\RWZI's\{installatiemap}\ARCHIVE\{PLC-project}"
}
```

Een installatienaam en/of kostenplaats volstaat. Bij meerdere kandidaten heeft
`_CE` voorrang; daarna wordt de recentste versie geselecteerd. Gebruik
`component_path` met `checkout_component`; `archive_relative_path` is alleen
voor een INI-veld dat expliciet een filesystempad verwacht.

### `export_via_cli`
Export uitvoeren via `VDogAutoExport.exe` met een bestaand INI-parameterbestand.

```
export_via_cli(ini_file_path="C:\exports\mijn_export.ini")
→ { success: true, returncode: 0 }
```

De REST-projectboomexport is niet beschikbaar wegens licentiebeperkingen.
Gebruik altijd eerst `resolve_project` en gebruik enkel het padtype dat bij
het betreffende veld van de bestaande INI-configuratie hoort.

---

## Archiefstructuur — padopbouw

```
\RWZI's\{actuele installatiemap}\ARCHIVE\{actueel PLC-project}
\PS\{actuele installatiemap}\ARCHIVE\{actueel PLC-project}
```

De gedeelde archive is de bron van waarheid. Gebruik daarom nooit bekende
installatie- of voorbeeldpaden als invoer voor een export: roep eerst
`resolve_project` aan.

---

## Checkout-bestemming

Uitgecheckte bestanden worden gespiegeld naar:

```
{projectroot}\octoPlantCheckouts\{componentpad}
```

Configureerbaar via `OCTOPLANT_CHECKOUT_PATH` in `.env`.
Laat deze variabele leeg om de dedicatede workspace-map
`octoPlantCheckouts` te gebruiken.

---

## Beveiliging

- Gebruikersnaam en wachtwoord staan **nooit** in `.env` of in de MCP-communicatie
- Credentials zijn nooit zichtbaar voor de AI
- De binary is volledig stil: foutmeldingen verlaten de processen nooit als tekst
- Bearer-tokens worden nooit gelogd of in tool-responses opgenomen
- De plugin biedt uitsluitend **leesbewerkingen** — terugschrijven naar OctoPlant is geblokkeerd

---

## Projectstructuur

```
Octoplant-Plugin/
├── server.py                    # MCP-server entry point
├── .env                         # Lokale, niet-geversioneerde configuratie
├── pyproject.toml               # Python-dependencies
├── scripts/
│   ├── install.ps1              # Eenmalig installatiescript
│   └── start-mcp.cmd            # Portable launcher (gebruikt door VS Code)
├── src/
│   ├── client.py                # OctoplantClient (archive-scan + CLI, geen credentials)
│   ├── navigation.py            # Read-only resolver voor de serverarchive
│   ├── tools/
│   │   ├── checkout.py          # checkout_component, checkout_all
│   │   └── export.py            # resolve_project, export_via_cli
│   └── models/
│       └── octoplant.py         # Pydantic-modellen
├── binaryTools/
│   └── VDogCheckOut/
│       ├── publish/
│       │   └── VDogCheckOut.exe # Self-contained wrapper (credentials intern)
│       ├── Program.cs
│       ├── Authenticator.cs
│       ├── Checkout.cs
│       └── Config.cs
├── octoPlantCheckouts/          # Lokale mirror van uitgecheckte componenten
├── assets/
│   └── Octoplant.png
└── .vscode/
    └── mcp.json                 # VS Code MCP-serverregistratie
```
