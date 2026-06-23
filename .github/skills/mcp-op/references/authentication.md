# Authenticatie

Authenticatie is **volledig intern afgehandeld** door `VDogCheckOut.exe`.

De AI hoeft geen credentials, gebruikersnamen, wachtwoorden of token-endpoints te kennen.
Credentials worden buiten de workspace beheerd en zijn niet zichtbaar voor het MCP-protocol.

## Credential-flow

```
Credential provider (extern)
    ↓  (credentials intern beheerd, buiten de plugin)
VDogCheckOut.exe
    ↓  POST /v1/oauth2/token  (Resource Owner Password flow)
OctoPlant REST API  (HTTPS poort 64023)
    ↓  Bearer-token (in-memory gecacht, proceslevensduur)
VDogAutoCheckOut.exe / VDogAutoExport.exe
```

## Gebruik vanuit AI

Test of de verbinding werkt:
```
VDogCheckOut.exe login
```

## Exit codes

| Exit code | Betekenis |
|-----------|-----------|
| `0` | Succes |
| `1` | Algemene fout |
| `2` | Geen componenten gevonden |
| `10` | Config-fout (ontbrekende .env variabele of misconfiguratie) |
| `1000` | Authenticatie mislukt |

## Securitybeleid binary output

De binary is **volledig stil** — geen stdout/stderr behalve:
- `token` subcommand: schrijft uitsluitend de Bearer-token op stdout (geen label)
- `checkout --json`: structurele statusvelden (returncode, status, pad) — **nooit** ruwe subprocess-output
- `--help`: helptekst

Alle foutmeldingen (authenticatie, configuratie, subprocess) worden **weggegooid** en resulteren
uitsluitend in een exit code. Zo kunnen credentials of infrastructuurdetails nooit via
stdio naar de LLM lekken.

## SSL/TLS

- OctoPlant gebruikt HTTPS op poort `64023`
- SSL-verificatie configureerbaar via `.env` (`OCTOPLANT_SSL_VERIFY=true/false`)

## MCP-tool

| Tool | Beschrijving |
|------|-------------|
| `authenticate` | Test de verbinding via `VDogCheckOut.exe login` — retourneert alleen exit code |