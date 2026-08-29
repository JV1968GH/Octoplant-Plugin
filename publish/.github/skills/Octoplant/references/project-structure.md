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
mirroracties schrijven uitsluitend naar `octoPlantCheckouts` onder de
runtime-workspace.

De versiondog-client staat vast op
`C:\Program Files (x86)\vdogClient`; de wrapper gebruikt geen alternatieve
clientpaden of auto-discovery.

Gebruikersnaam, domein en wachtwoord worden uitsluitend uit de Windows Generic
Credential met vaste targetnaam `Octoplant` gelezen. De wrapper leest zowel
credentials als instellingen via de meegeleverde `CredentialsManager.exe`.
Credentials, tokens, instellingen en details van onderliggende binaries komen
nooit in MCP-responses terecht.
