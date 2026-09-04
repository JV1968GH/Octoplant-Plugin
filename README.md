# Octoplant — MCP Plugin voor OctoPlant/versiondog

MCP-server die AI-assistenten (GitHub Copilot, Claude Desktop, …) **read-only** toegang geeft tot
OctoPlant/versiondog: projectpaden read-only oplossen en componenten uitchecken.

**Release:** 2.1.8

> **Scope:** uitsluitend read-only navigatie en check-out. Check-in en maintenance mode zijn bewust uitgesloten.

---

## Vereisten

| Component | Versie | Download |
|-----------|--------|----------|
| Python | 3.11 of hoger | [python.org](https://www.python.org/downloads/windows/) |
| versiondog client | geïnstalleerd | via IT / OctoPlant beheerder |

---

## Installatie

### Stap 1 — Marketplace toevoegen

1. Open **GitHub Copilot Desktop**.
2. Open **Settings** en kies **Install**.
3. Kies **Add marketplace** en vul `JV1968GH/OT-MarketPlace` in.
4. Installeer **Octoplant** en schakel de plugin in.

### Stap 2 — Automatische lokale Python-runtime

Bij de eerste start maakt de MCP-launcher automatisch de gebruiker-lokale
runtime aan in `%LOCALAPPDATA%\AI\Plugins\octoplant\runtime\venv` en installeert
hij de gedeclareerde Python-dependencies. Hiervoor moet Python 3.11 of hoger
via `py -3` of `python` beschikbaar zijn. De voortgang en bruikbare fouten gaan
naar stderr, voordat de MCP-stdio-verbinding start.

De MCP-registratie gebruikt een expliciete `timeout` van `600000` milliseconden
(tien minuten). Dat geeft een eerste installatie op een beheerd netwerk genoeg
tijd om de venv en dependencies klaar te zetten voordat Copilot de tools
opvraagt; normale starts gebruiken dezelfde registratie zonder extra wachttijd.

De volgende handmatige installatie blijft beschikbaar om de runtime vooraf te
maken of te herstellen:

```powershell
.\scripts\install.ps1
```

Dit script:
- Valideert het meegeleverde runtimepakket met `VDogCheckOut.exe` en `CredentialsManager.exe`
- Maakt de gebruiker-lokale runtime aan in `%LOCALAPPDATA%\AI\Plugins\octoplant\runtime\venv`
- Installeert alle Python-dependencies
- Verifieert dat de officiële Python MCP SDK (`FastMCP`) beschikbaar is

De installatiemap mag read-only zijn: de launcher en het script schrijven
uitsluitend naar de gebruiker-lokale runtime. Een .NET SDK is niet nodig op een clienttoestel; de
wrapper is als self-contained release-build met de plugin meegeleverd. Ontbreken
de release-artifacts, installeer de plugin dan opnieuw via de marketplace.

Gebruik alleen bij een beheerde Python-installatie een specifieke runtime:

```powershell
.\scripts\install.ps1 -PythonPath "C:\Program Files\Python312\python.exe"
```

De launcher gebruikt optioneel eerst `OCTOPLANT_MCP_PYTHON` en daarna de
gebruiker-lokale runtime. Een override moet Python 3.11+ met `FastMCP` bevatten:

```powershell
$env:OCTOPLANT_MCP_PYTHON = "C:\Tools\Python\python.exe"
```

### Stap 3 — Octoplant-instellingen opslaan

Open `CredentialsManager.exe` en selecteer de kaart **Octoplant**. Sla onder
die hoofdkaart de volgende niet-geheime instellingen op volgens de interne
procedure:

| Subsleutel | Betekenis |
|---|---|
| `URL` | Volledige HTTP(S)-server-URL zonder poortnummer. |
| `Portnumber` | TCP-poort van de Octoplant-server. |
| `OCTOPLANT_CLIENT_ARCHIVE_PATH` | Lokale clientarchive voor `VDogAutoCheckOut.exe`. |

De wrapper leest gebruikersnaam, domein en wachtwoord uitsluitend uit de
Windows Generic Credential met vaste targetnaam `Octoplant`. De meegeleverde
`CredentialsManager.exe` draagt credentials en instellingen uitsluitend via
een private named pipe in het geheugen over; geen van deze gegevens wordt
gelogd of via MCP doorgegeven.

### Stap 4 — Verbinding testen

```powershell
.\binaryTools\VDogCheckOut\publish\VDogCheckOut.exe login
```

| Exit code | Betekenis |
|-----------|-----------|
| `0` | Verbinding en authenticatie geslaagd ✅ |
| `1` | Algemene fout |
| `10` | Lokale configuratie of Windows-referentie ontbreekt |
| `1000` | Authenticatie mislukt |

### Stap 5 — Gebruiken in Copilot Desktop

Open een nieuwe Copilot-chat. De plugin registreert **MCP_Octoplant** via `.mcp.json`;
de server start automatisch wanneer de plugin is ingeschakeld.

Bij problemen:
1. Controleer dat Python 3.11+ voor de huidige gebruiker beschikbaar is; start Copilot opnieuw zodat de launcher de runtime opnieuw kan maken.
2. Voer `.\scripts\install.ps1` uit om `%LOCALAPPDATA%\AI\Plugins\octoplant\runtime\venv` vooraf te herstellen.
3. Controleer of zowel `VDogCheckOut.exe` als `CredentialsManager.exe` aanwezig zijn in `binaryTools\VDogCheckOut\publish\`.
4. Test de verbinding éénmaal met `VDogCheckOut.exe login`.

---

## Beschikbare tools (AI-commando's)

### `authenticate`
Test de verbinding en authenticatie.

```
authenticate()
→ { success: true, returncode: 0 }
```

### `checkout_component`
Check een specifiek PLC-component of project uit vanuit OctoPlant.

```
checkout_component(
    workspace_path = "C:\\pad\\naar\\de\\hoofdchat-workspace",
    component_path = "\RWZI's\{installatiemap}\{PLC-project}"
)
```

> ⚠️ Het pad begint altijd met een backslash.
> Padformaat: `\{rootmap}\{kostplaats} - {naam}\{kostplaats} - {naam}, PLC{##}_CE`

Parameters:

| Parameter | Type | Beschrijving |
|-----------|------|-------------|
| `workspace_path` | string | Verplicht absoluut pad naar de projectmap van de hoofdchat; tijdens een Copilot-sessie bepaalt de runtime deze hoofdchat-workspace automatisch |
| `component_path` | string | Relatief componentpad (met leading `\`) |
| `component_id` | string | Component-ID als alternatief voor pad |
| `with_backups` | bool | Backups meenemen (standaard: false) |
| `number_of_archives` | int | Aantal archives (0 = alle, standaard 1) |
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
Roep deze tool aan bij de start van elke OctoPlant-sessie, vóór een check-out.
Hij leest de gedeelde serverarchive telkens opnieuw, gebruikt
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
`component_path` met `checkout_component`; `archive_relative_path` is de
bijbehorende read-only locatie in de gedeelde archive.

---

## Archiefstructuur — padopbouw

```
\RWZI's\{actuele installatiemap}\ARCHIVE\{actueel PLC-project}
```

De read-only archive voor RWZI-projecten is vast in de plugin ingebouwd en
wordt uitsluitend gebruikt om componentnamen op te lossen. Gebruik daarom nooit
bekende installatie- of voorbeeldpaden als invoer voor een checkout: roep eerst
`resolve_project` aan.

---

## Checkout-bestemming

Uitgecheckte bestanden worden gespiegeld naar:

```
{workspace}\octoPlantCheckouts\{componentpad}
```

De MCP-server start vanuit de plugininstallatiemap. Tijdens een Copilot-sessie
leest hij de hoofdchat-workspace uit de metadata van de actieve sessie en
spiegelt alleen naar die locatie. Daardoor kan een meegegeven artefact- of
uitvoermap de bestemming niet wijzigen. Buiten Copilot blijft de expliciete
absolute `workspace_path` verplicht.

---

## Beveiliging

- Gebruikersnaam, domein, wachtwoord en Octoplant-instellingen staan **nooit** in bestanden in de pluginrepository of de MCP-communicatie
- Credentials worden uitsluitend opgehaald uit Windows Credential Manager met vaste targetnaam `Octoplant` en zijn nooit zichtbaar voor de AI
- `CredentialsManager.exe` geeft credentials en instellingen alleen via een per aanvraag gemaakte private named pipe door; stdout, stderr, logs en MCP-responses bevatten nooit waarden
- Authenticatie- en configuratiefouten geven uitsluitend gestandaardiseerde exitcodes; credentials, tokens en ruwe uitvoer van onderliggende binaries komen niet in logging of tool-responses
- Bearer-tokens worden nooit gelogd of in tool-responses opgenomen
- De plugin biedt uitsluitend **leesbewerkingen** — terugschrijven naar OctoPlant is geblokkeerd

---

## Projectstructuur

```
Octoplant-Plugin/
├── server.py                    # MCP-server entry point
├── pyproject.toml               # Python-dependencies
├── scripts/
│   ├── install.ps1              # Eenmalig installatiescript
│   └── start-mcp.cmd            # Launcher voor GitHub Copilot Desktop
│                                  # gebruikt de user-local runtime, geen .venv in de pluginmap
├── src/
│   ├── client.py                # OctoplantClient (archive-scan + CLI, geen credentials)
│   ├── navigation.py            # Read-only resolver voor de serverarchive
│   └── tools/
│       ├── checkout.py          # checkout_component, checkout_all
│       └── navigation.py        # resolve_project
├── binaryTools/
│   ├── CredentialsManager/     # Gepinde Git-submodule (buildafhankelijkheid)
│   └── VDogCheckOut/
│       ├── publish/
│       │   ├── VDogCheckOut.exe       # Self-contained wrapper
│       │   └── CredentialsManager.exe # Runtime credential helper
│       ├── Program.cs
│       ├── Authenticator.cs
│       ├── Checkout.cs
│       ├── Config.cs
│       └── CredentialsManagerClient.cs
├── octoPlantCheckouts/          # Lokale mirror van uitgecheckte componenten
├── assets/
│   └── Octoplant.png
└── .mcp.json                    # MCP-serverregistratie
```

De registratie gebruikt `${PLUGIN_ROOT}\scripts\start-mcp.cmd` met een
stdio-timeout van tien minuten; er zijn geen gebruikersspecifieke absolute
paden in het pluginpakket.
