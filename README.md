# Octoplant — MCP Plugin voor OctoPlant/versiondog

MCP-server die AI-assistenten (GitHub Copilot, Claude Desktop, …) **read-only** toegang geeft tot
OctoPlant/versiondog: projectpaden read-only oplossen en componenten uitchecken.

**Release:** 0.8.0

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
4. Installeer **octoplant-plugin** en schakel de plugin in.

### Stap 2 — Lokale Python-omgeving voorbereiden

Installeer Python 3.11 of hoger. Zorg dat `py -3` of `python` in je huidige
sessie beschikbaar is. Open daarna PowerShell in de geïnstalleerde pluginmap
en voer uit:

```powershell
.\scripts\install.ps1
```

Dit script:
- Valideert het meegeleverde runtimepakket met `VDogCheckOut.exe` en `CredentialsManager.exe`
- Bouwt beide exe's vanuit de gepinde `CredentialsManager`-submodule wanneer artifacts in een broncheckout ontbreken
- Maakt een plugin-lokale `.venv` aan met de gevonden Python-runtime
- Installeert alle Python-dependencies
- Maakt een lokale `.env` op basis van `.env.example` als die nog niet bestaat

Een .NET SDK is niet nodig op een clienttoestel: de wrapper is als
self-contained release-build met de plugin meegeleverd. De submodule is een
buildafhankelijkheid; de runtime gebruikt de meegeleverde executable naast de
wrapper.

### Stap 3 — `.env` aanpassen

Kopieer geen credentials naar `.env`. Vul alleen de lokale verbindings- en
padinstellingen in volgens de interne procedure:

```ini
OCTOPLANT_SERVER=
OCTOPLANT_CLIENT_ARCHIVE_PATH=
OCTOPLANT_PYTHON_PATH=
```

De wrapper leest gebruikersnaam, domein en wachtwoord uitsluitend uit de
Windows Generic Credential met vaste targetnaam `Octoplant`. De meegeleverde
`CredentialsManager.exe` draagt die gegevens uitsluitend via een private
named pipe in het geheugen over; geen van deze gegevens wordt gelogd of via
MCP doorgegeven.

`OCTOPLANT_PYTHON_PATH` is optioneel en accepteert alleen een bestaand Python
3.11+-pad waarin de server-dependencies geladen kunnen worden. Zonder deze override
selecteert de launcher achtereenvolgens de plugin-lokale `.venv`, `py -3` en
`python` op `PATH`. De launcher wijzigt geen user- of systeem-`PATH` en slaat
geen interpreterpad op.

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

Open een nieuwe Copilot-chat. De plugin registreert **MCP_OP** via `.mcp.json`;
de server start automatisch wanneer de plugin is ingeschakeld.

Bij problemen:
1. Voer `.\scripts\install.ps1` opnieuw uit om de plugin-lokale `.venv` te herstellen.
2. Controleer of zowel `VDogCheckOut.exe` als `CredentialsManager.exe` aanwezig zijn in `binaryTools\VDogCheckOut\publish\`.
3. Test de verbinding éénmaal met `VDogCheckOut.exe login`.

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

Deze bestemming is vast en wordt afgeleid van de workspace waarin de
MCP-server draait.

---

## Beveiliging

- Gebruikersnaam, domein en wachtwoord staan **nooit** in `.env` of de MCP-communicatie
- Credentials worden uitsluitend opgehaald uit Windows Credential Manager met vaste targetnaam `Octoplant` en zijn nooit zichtbaar voor de AI
- `CredentialsManager.exe` geeft credentials alleen via een per aanvraag gemaakte private named pipe door; stdout, stderr, logs en MCP-responses bevatten nooit credentials
- Authenticatie- en configuratiefouten geven uitsluitend gestandaardiseerde exitcodes; credentials, tokens en ruwe uitvoer van onderliggende binaries komen niet in logging of tool-responses
- Bearer-tokens worden nooit gelogd of in tool-responses opgenomen
- De plugin biedt uitsluitend **leesbewerkingen** — terugschrijven naar OctoPlant is geblokkeerd

---

## Projectstructuur

```
Octoplant-Plugin/
├── server.py                    # MCP-server entry point
├── .env                         # Lokale, niet-geversioneerde configuratie
├── .env.example                 # Sjabloon zonder concrete waarden
├── pyproject.toml               # Python-dependencies
├── scripts/
│   ├── install.ps1              # Eenmalig installatiescript
│   └── start-mcp.cmd            # Launcher voor GitHub Copilot Desktop
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
