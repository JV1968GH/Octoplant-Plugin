# Configuratie

`CredentialsManager.exe` levert niet-geheime instellingen via een private
named pipe. Ze staan onder hoofdkaart `Octoplant`:

| Subsleutel | Betekenis |
|---|---|
| `URL` | HTTP(S)-server-URL voor de wrapper, zonder poortnummer. |
| `Portnumber` | TCP-poort voor de Octoplant-server. |
| `OCTOPLANT_CLIENT_ARCHIVE_PATH` | Lokale clientarchive voor `VDogAutoCheckOut.exe`. |

De gedeelde archive is vast ingebouwd en wordt nooit beschreven door de plugin.
Check-out gebruikt uitsluitend de lokale `OCTOPLANT_CLIENT_ARCHIVE_PATH`;
mirroracties schrijven uitsluitend naar `octoPlantCheckouts` onder de actieve
client-workspace, niet onder de plugininstallatiemap. De
`OCTOPLANT_WORKSPACE_ROOT`-omgevingvariabele draagt dit pad van de MCP-client
naar de runtime over.

De versiondog-client staat vast op
`C:\Program Files (x86)\vdogClient`; de wrapper gebruikt geen alternatieve
clientpaden of auto-discovery.

Gebruikersnaam, domein en wachtwoord worden uitsluitend uit de Windows Generic
Credential met vaste targetnaam `Octoplant` gelezen. De wrapper leest zowel
credentials als instellingen via de meegeleverde `CredentialsManager.exe`.
Credentials, tokens, instellingen en details van onderliggende binaries komen
nooit in MCP-responses terecht.

## Python MCP-runtime

De plugin gebruikt de officiële Python MCP SDK met `FastMCP`. De runtime wordt
per Windows-gebruiker geinstalleerd in:

```text
%LOCALAPPDATA%\AI\Plugins\octoplant\runtime\venv
```

De plugininstallatiemap blijft read-only. `scripts\start-mcp.cmd` gebruikt
eerst de optionele `OCTOPLANT_MCP_PYTHON` override en daarna deze
gebruiker-lokale runtime. Ontbreekt die runtime, dan maakt de launcher hem
automatisch met een beschikbare Python 3.11+-basisruntime en installeert de
gedeclareerde dependencies voordat de MCP-stdio-server start. Alle
bootstrap-uitvoer gaat naar stderr. De handmatige `scripts\install.ps1` is
alleen nodig om de runtime vooraf te maken of te herstellen.

De portable `.mcp.json`-registratie gebruikt `timeout: 600000` (tien minuten)
voor de stdio-start. Dit voorkomt dat Copilot de toolregistratie afbreekt
tijdens de eerste venv- en dependencyinstallatie; normale starts zijn direct
beschikbaar.
