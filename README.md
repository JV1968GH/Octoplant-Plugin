# Octoplant — MCP Plugin voor OctoPlant/versiondog

MCP-server die AI-assistenten (GitHub Copilot, Claude Desktop, …) veilige
OctoPlant/versiondog-navigatie, gerichte checkout en gecontroleerde
checkoutvrijgave biedt.

**Release:** 2.3.4

> **Scope:** navigatie en gerichte checkout, plus uitsluitend een expliciet
> bevestigde check-in zonder nieuwe versie. Maintenance mode en andere mutaties
> zijn uitgesloten.

---

## Vereisten

| Component | Versie | Download |
|-----------|--------|----------|
| Python | 3.11 of hoger | [python.org](https://www.python.org/downloads/windows/) |
| versiondog client | geïnstalleerd | via IT / OctoPlant beheerder |

---

## Installatie

De marketplace is de ondersteunde installatieprocedure. Installeer de plugin
niet handmatig vanuit een lokale map of via een CLI.

1. Open in de zijbalk **Customize > Plugins**.
2. Selecteer de geconfigureerde marketplace en zoek naar **Octoplant**.
3. Selecteer de plugin en kies **Install** of **Activate**.

### Automatische lokale Python-runtime

Bij de eerste start maakt de MCP-launcher automatisch de gebruiker-lokale
runtime aan in `%LOCALAPPDATA%\AI\Plugins\octoplant\runtime\venv` en installeert
hij de gedeclareerde Python-dependencies. Hiervoor moet Python 3.11 of hoger
via `py -3` of `python` beschikbaar zijn. De voortgang en bruikbare fouten gaan
naar stderr, voordat de MCP-stdio-verbinding start.

De MCP-registratie gebruikt een expliciete `timeout` van `600000` milliseconden
(tien minuten). Dat geeft een eerste installatie op een beheerd netwerk genoeg
tijd om de venv en dependencies klaar te zetten voordat Copilot de tools
opvraagt; normale starts gebruiken dezelfde registratie zonder extra wachttijd.

De installatiemap mag read-only zijn: de launcher en het script schrijven
uitsluitend naar de gebruiker-lokale runtime. Een .NET SDK is niet nodig op een clienttoestel; de
wrapper is als self-contained release-build met de plugin meegeleverd. Ontbreken
de release-artifacts, installeer de plugin dan opnieuw via de marketplace.

De launcher gebruikt optioneel eerst `OCTOPLANT_MCP_PYTHON` en daarna de
gebruiker-lokale runtime. Een override moet Python 3.11+ met `FastMCP` bevatten:

```powershell
$env:OCTOPLANT_MCP_PYTHON = "C:\Tools\Python\python.exe"
```

### Octoplant-instellingen opslaan

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

### Verbinding testen

```powershell
.\binaryTools\VDogCheckOut\publish\VDogCheckOut.exe login
```

| Exit code | Betekenis |
|-----------|-----------|
| `0` | Verbinding en authenticatie geslaagd ✅ |
| `1` | Algemene fout |
| `10` | Lokale configuratie of Windows-referentie ontbreekt |
| `1000` | Authenticatie mislukt |

### Gebruiken in Copilot Desktop

Open een nieuwe Copilot-chat. De plugin registreert **MCP_Octoplant** via `.mcp.json`;
de server start automatisch wanneer de plugin is ingeschakeld.

Stuur voor een lokale projectkopie één zichtbaar handoff-blok naar de
Octoplant Specialist:

```text
⬇️✋ HANDOFF — OctoPlant
Actie: project lokaal beschikbaar maken
Installatie: {installatienaam}
Kostenplaats: {kostenplaats}
PLC: {PLC-naam of nummer}
Workspace: C:\pad\naar\de\hoofdworkspace
Bevestiging: ja
```

De specialist resolveert het doel intern en sluit af met één
`↩️ RESULTAAT — <terminal state>`-bericht. De terminal states zijn:
✅ COMPLETED, 🔎 NOT_FOUND, ❓ NEEDS_INPUT, ⚠️ BLOCKED, ❌ FAILED en 🛑 UNSAFE.
Bij een geslaagde lokale projectkopie bevat het resultaat alleen een
niet-sensitieve samenvatting en `Lokaal project: <pad>`.

Bij problemen:
1. Controleer dat Python 3.11+ voor de huidige gebruiker beschikbaar is; start Copilot opnieuw zodat de launcher de runtime opnieuw kan maken.
2. Installeer de plugin opnieuw via de marketplace als de runtime niet opnieuw kan worden gemaakt.
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
    installation_name = "{installatie-naam}",
    cost_center = "{kostenplaats}",
    component_path = "\RWZI's\{installatiemap}\{PLC-project}"
)
```

> ⚠️ Het pad begint altijd met een backslash.
> Padformaat: `\{rootmap}\{kostplaats} - {naam}\{kostplaats} - {naam}, PLC{##}_CE`

Parameters:

| Parameter | Type | Beschrijving |
|-----------|------|-------------|
| `workspace_path` | string | Verplicht absoluut pad uit de initiële agent-handoff; nooit een child-sessionworkspace of plugininstallatiemap |
| `installation_name` | string | Installatienaam uit de handoff; met kostenplaats vormt dit de artifactmap |
| `cost_center` | string | Kostenplaats uit de handoff; met installatienaam vormt dit de artifactmap |
| `component_path` | string | Relatief componentpad (met leading `\`) |
| `with_backups` | bool | Backups meenemen (standaard: false) |
| `number_of_archives` | int | Aantal archives (0 = alle, standaard 1) |
| `version` | int | Specifiek versienummer (standaard: huidig) |
| `with_std_libs` | bool | Standaardbibliotheken meenemen |
| `comment` | string | Opmerking in het CheckIn-CheckOut-Log |

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

### `checkin_unchanged_component`

Geeft één gerichte, onveranderde native checkout vrij na directe
gebruikersbevestiging:

```
checkin_unchanged_component(
    component_path = "\RWZI's\{installatiemap}\{PLC-project}",
    confirmed = true
)
```

Deze tool gebruikt altijd de lokale clientarchive, maakt nooit een versie
(`Enabled=N`), voert geen vergelijking uit (`WithoutComparison=Y`) en geeft
de checkout vrij (`ReleaseAfterCheckIn=Y`). Maintenance mode en iedere andere
Octoplant-mutatie blijven uitgesloten.

### `checkout_copy_and_release_component`

Voert de volledige lifecycle voor één component in de plugin uit: gerichte
checkout, artifactmirror en daarna de versieloze vrijgave van de native
checkout. De vrijgave gebeurt uitsluitend als checkout én mirror slagen en
vereist directe gebruikersbevestiging:

```
checkout_copy_and_release_component(
    workspace_path = "C:\\pad\\naar\\de\\hoofdchat-workspace",
    installation_name = "{installatie-naam}",
    cost_center = "{kostenplaats}",
    component_path = "\RWZI's\{installatiemap}\{PLC-project}",
    confirmed = true
)
```

Gebruik deze tool wanneer het resultaat lokaal beschikbaar moet zijn maar de
bovenliggende orchestrator geen afzonderlijke Octoplant-stappen hoeft te
plannen. Bij een checkout- of mirrorfout wordt geen vrijgave aangeroepen.

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
{workspace}\PLC-projecten\{installatie-naam} - {kostenplaats}\{componentpad}
```

De MCP-server start vanuit de plugininstallatiemap, maar gebruikt uitsluitend
de initiële handoff-workspace als artifactroot. Wanneer maar een van
installatienaam of kostenplaats beschikbaar is, gebruikt hij alleen die waarde
als mapnaam. Een niet gevonden PLC-project geeft via de specialist
`↩️ RESULTAAT — 🔎 NOT_FOUND` terug; de plugin probeert nooit een bredere
checkout als fallback.

---

## Beveiliging

- Gebruikersnaam, domein, wachtwoord en Octoplant-instellingen staan **nooit** in bestanden in de pluginrepository of de MCP-communicatie
- Credentials worden uitsluitend opgehaald uit Windows Credential Manager met vaste targetnaam `Octoplant` en zijn nooit zichtbaar voor de AI
- `CredentialsManager.exe` geeft credentials en instellingen alleen via een per aanvraag gemaakte private named pipe door; stdout, stderr, logs en MCP-responses bevatten nooit waarden
- Authenticatie- en configuratiefouten geven uitsluitend gestandaardiseerde exitcodes; credentials, tokens en ruwe uitvoer van onderliggende binaries komen niet in logging of tool-responses
- Bearer-tokens worden nooit gelogd of in tool-responses opgenomen
- De plugin staat uitsluitend de expliciet bevestigde, versieloze
  checkoutvrijgave toe; alle andere Octoplant-mutaties zijn geblokkeerd

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
│       ├── checkout.py          # checkout_component
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
├── PLC-projecten/               # Lokale mirror van uitgecheckte componenten, per installatie
├── assets/
│   └── Octoplant.png
└── .mcp.json                    # MCP-serverregistratie
```

De registratie gebruikt `${PLUGIN_ROOT}\scripts\start-mcp.cmd` met een
stdio-timeout van tien minuten; er zijn geen gebruikersspecifieke absolute
paden in het pluginpakket.
