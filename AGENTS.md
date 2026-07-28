# AGENTS.md — Octoplant plugin (MCP + skills + binary integration)


## Plugincontext

Deze repository is een **Octoplant plugin-workspace** met drie lagen:

1. **Runtime-laag (Python)**: MCP-server en tool-implementaties in `server.py` en `src/`.
2. **Kennislaag (skills)**: repo-skills in `.github/skills/Octoplant/`.
3. **Integratielaag (binaries)**: lokale wrappers en externe CLI-koppelingen in `binaryTools/`.

Het doel blijft read-only toegang tot OctoPlant/versiondog (checkout + export) voor AI-workflows.

## Workspace-indeling (canoniek)

- `src/` = kernlogica van de plugin
- `tests/` = unittests/integratietests
- `scripts/` = launcher + installatiescripts
- `assets/` = plugin-assets (o.a. icoon)
- `binaryTools/` = lokale helper binaries en source
- `octoPlantCheckouts/` = lokale outputmap voor uitgecheckte componenten
- `.github/skills/` = skilldefinities en referenties
- `.mcp.json` = MCP-registratie voor de plugin

## Scope en veiligheidsregels

- **Nooit implementeren**: `checkin`, `maintenance_mode`, of enige write/update/delete naar OctoPlant.
- Authenticatie gebeurt via de binarylaag; credentials blijven buiten MCP-tooling.
- Ruwe binaire output (`stdout`/`stderr`) van `VDogCheckOut.exe` en `VDogAutoCheckOut.exe` mag niet naar LLM-responses doorstromen.

## Bron van waarheid

Detailkennis en technische afspraken staan in skill `Octoplant`:

- `.github/skills/Octoplant/SKILL.md`
- `.github/skills/Octoplant/references/*.md`
