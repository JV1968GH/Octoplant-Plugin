# AGENTS.md — Octoplant plugin (MCP + skills + binary integration)


## Plugincontext

Deze repository is een **Octoplant plugin-workspace** met drie lagen:

1. **Runtime-laag (Python)**: MCP-server en tool-implementaties in `server.py` en `src/`.
2. **Kennislaag (skills)**: repo-skills in `skills/Octoplant/`.
3. **Integratielaag (binaries)**: lokale wrappers en externe CLI-koppelingen in `binaryTools/`.

Het doel is veilige OctoPlant/versiondog-navigatie, gerichte checkout/export en
uitsluitend gecontroleerde vrijgave van een onveranderde checkout.

## Workspace-indeling (canoniek)

- `src/` = kernlogica van de plugin
- `tests/` = unittests/integratietests
- `scripts/` = launcher + installatiescripts
- `assets/` = plugin-assets (o.a. icoon)
- `binaryTools/` = lokale helper binaries en source
- `PLC-projecten/` = lokale outputmap voor uitgecheckte componenten, per installatie
- `skills/` = skilldefinities en referenties
- `.mcp.json` = MCP-registratie voor de plugin

## Scope en veiligheidsregels

- **Nooit implementeren**: `maintenance_mode`, checkout-all, writes naar de
  gedeelde serverarchive, of andere OctoPlant-mutaties dan de gecontroleerde
  check-in zonder versiecreatie.
- De gecontroleerde check-in  werkt op
  exact één opgelost component en gebruikt altijd `Enabled=N`,
  `WithoutComparison=Y` en `ReleaseAfterCheckIn=Y`.
- Authenticatie gebeurt via de binarylaag; credentials blijven buiten MCP-tooling.
- Ruwe binaire output (`stdout`/`stderr`) van `VDogCheckOut.exe` en `VDogAutoCheckOut.exe` mag niet naar LLM-responses doorstromen.

## Bron van waarheid

Detailkennis en technische afspraken staan in skill `Octoplant`:

- `skills/Octoplant/SKILL.md`
- `skills/Octoplant/references/*.md`
