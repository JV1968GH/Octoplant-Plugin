# Octoplant — MCP Plugin voor OctoPlant/versiondog

MCP-server die AI-assistenten (GitHub Copilot, Claude Desktop, …) **read-only** toegang geeft tot
OctoPlant/versiondog: componenten uitchecken en projectdata exporteren.

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
git clone <repo-url> Octoplant
cd Octoplant
```

### Stap 2 — Eenmalig installatiescript uitvoeren

```powershell
.\scripts\install.ps1
```

Dit script:
- Maakt de conda-omgeving `mcp-op` aan (Python 3.12)
- Installeert alle Python-dependencies
- Bouwt `VDogCheckOut.exe` (.NET, self-contained)
- Maakt `.env` aan vanuit `.env.example`

### Stap 3 — `.env` aanpassen

Open `.env` en vul de waarden in voor dit toestel:

```ini
OCTOPLANT_SERVER=https://jouw-server:64023
OCTOPLANT_ARCHIVE_PATH=D:\vdClientArchive
OCTOPLANT_VDOG_CLIENT_PATH=C:\Program Files\vdogClient
OCTOPLANT_SSL_VERIFY=false
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
    component_path = "\RWZI's\100026 - Dendermonde\100026 - Dendermonde, PLC08_CE"
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

### `start_export`
Start een asynchrone export-order op de OctoPlant server.

```
start_export(export_types=["projectTree", "componentLog"])
→ { name: "order-xyz", ... }
```

Beschikbare exporttypen: `projectTree`, `jobList`, `jobResults`, `usersAndGroups`,
`componentTypes`, `componentLog`, `eventLog`, `adminLog`, `linkedLibraries`, `usageInfo`

### `get_export_status`
Vraag de status op van een lopende export.

```
get_export_status(order_name="order-xyz")
→ { done: false, metadata: { state: "STATE_RUNNING" } }
```

### `download_export`
Download een afgeronde export als ZIP-bestand.

```
download_export(order_name="order-xyz")
download_export(order_name="order-xyz", output_path="C:\exports\mijn_export.zip")
→ "C:\exports\octoplant_export_order-xyz.zip"
```

### `run_export`
Start + poll + download in één stap (meest praktisch voor dagelijks gebruik).

```
run_export(export_types=["projectTree"])
run_export(export_types=["projectTree", "eventLog"], timeout_seconds=120)
→ "C:\exports\octoplant_export_order-xyz.zip"
```

| Parameter | Standaard | Beschrijving |
|-----------|-----------|-------------|
| `export_types` | — | Lijst exporttypen (verplicht) |
| `output_path` | automatisch | Doelpad ZIP-bestand |
| `poll_interval_seconds` | 2.0 | Wachttijd tussen statuscontroles |
| `timeout_seconds` | 300.0 | Maximale wachttijd |

### `cancel_export`
Annuleer een wachtende of lopende export.

```
cancel_export(order_name="order-xyz")
```

### `export_via_cli`
Export uitvoeren via `VDogAutoExport.exe` met een bestaand INI-parameterbestand.

```
export_via_cli(ini_file_path="C:\exports\mijn_export.ini")
→ { success: true, returncode: 0 }
```

---

## Archiefstructuur — padopbouw

```
\RWZI's\{kostplaats} - {naam}\{kostplaats} - {naam}, PLC{##}_CE
\PS\{kostplaats} - {naam}\{kostplaats} - {naam}, PLC{##}_CE
```

Bekende installaties:

| Kostplaats | Naam | Type |
|------------|------|------|
| 100020 | Gent | RWZI |
| 100026 | Dendermonde | RWZI |
| 100078 | Dessel | RWZI |
| 100114 | Overpelt | RWZI |
| 100138 | Achel | RWZI |

Voorbeeldpaden:

| Gewenst | Pad |
|---------|-----|
| Dendermonde PLC08 | `\RWZI's\100026 - Dendermonde\100026 - Dendermonde, PLC08_CE` |
| Gent PLC01 | `\RWZI's\100020 - Gent\100020 - Gent, PLC01_CE` |
| Achel PLC02 (PS) | `\PS\100138 - Achel\100138 - Achel, PLC02_CE` |

---

## Checkout-bestemming

Uitgecheckte bestanden worden gespiegeld naar:

```
{projectroot}\octoPlantCheckouts\{componentpad}
```

Configureerbaar via `OCTOPLANT_CHECKOUT_PATH` in `.env`.

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
Octoplant/
├── server.py                    # MCP-server entry point
├── .env.example                 # Configuratiesjabloon (kopieer naar .env)
├── pyproject.toml               # Python-dependencies
├── scripts/
│   ├── install.ps1              # Eenmalig installatiescript
│   └── start-mcp.cmd            # Portable launcher (gebruikt door VS Code)
├── src/
│   ├── client.py                # OctoplantClient (REST + CLI, geen credentials)
│   ├── tools/
│   │   ├── checkout.py          # checkout_component, checkout_all
│   │   └── export.py            # start_export, get_export_status, download_export,
│   │                            # cancel_export, run_export, export_via_cli
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
