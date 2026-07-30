# Configuratie

| Variabele | Betekenis |
|---|---|
| `OCTOPLANT_SERVER` | Lokale OAuth2-eindpuntconfiguratie voor de wrapper. |
| `OCTOPLANT_CLIENT_ARCHIVE_PATH` | Lokale clientarchive voor `VDogAutoCheckOut.exe`. |

De gedeelde archive is vast ingebouwd en wordt nooit beschreven door de plugin.
Check-out gebruikt uitsluitend de lokale `OCTOPLANT_CLIENT_ARCHIVE_PATH`;
mirroracties schrijven uitsluitend naar `octoPlantCheckouts` onder de
runtime-workspace.

De versiondog-client staat vast op
`C:\Program Files (x86)\vdogClient`; de wrapper gebruikt geen alternatieve
clientpaden of auto-discovery.

Gebruikersnaam, domein en wachtwoord staan nooit in `.env`. De wrapper leest
uitsluitend de Windows Generic Credential met vaste targetnaam `Octoplant` via
de meegeleverde `CredentialsManager.exe`. Credentials, tokens en details van
onderliggende binaries komen nooit in MCP-responses terecht.
