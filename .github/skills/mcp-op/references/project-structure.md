# Projectstructuur & Configuratie

## Mapstructuur

```
Octoplant-Plugin/
├── server.py                   # MCP-server entry point
├── assets/
│   └── Octoplant.png           # Icoon voor MCP-servermetadata
├── scripts/
│   ├── start-mcp.cmd           # Portable launcher (zoekt Python in conda mcp-op)
│   └── install.ps1             # Eenmalig installatiescript voor nieuwe machines
├── pyproject.toml              # Python-dependencies (pip install -e .)
├── .env.example                # Voorbeeld omgevingsvariabelen (kopieer naar .env)
├── .env                        # Lokale config (niet in git)
├── .gitignore
├── AGENTS.md                   # Projectscope (globaal)
├── .vscode/
│   └── mcp.json                # VS Code MCP-serverregistratie (portabel via ${workspaceFolder})
├── .github/
│   └── skills/
│       └── mcp-op/
│           ├── SKILL.md        # Skill index
│           └── references/     # Detaildocumentatie per functionaliteit
├── src/
│   ├── client.py               # OctoplantClient (REST + CLI subprocess, geen credentials)
│   ├── tools/
│   │   ├── checkout.py         # MCP-tools: checkout_component, checkout_all
│   │   └── export.py           # MCP-tools: start_export, get_export_status,
│   │                           #            download_export, cancel_export, export_via_cli
│   └── models/                 # Pydantic-modellen voor API-responses
├── binaryTools/
│   └── VDogCheckOut/
│       ├── publish/
│       │   └── VDogCheckOut.exe  # Self-contained CLI-wrapper (credentials intern)
│       ├── Program.cs
│       ├── Config.cs
│       ├── Authenticator.cs
│       ├── Checkout.cs
│       └── VDogCheckOut.csproj
└── tests/
    ├── test_checkout.py
    └── test_export.py
```

## Deployment op een nieuw toestel

```powershell
# 1. Clone het repo
git clone https://github.com/JV1968GH/Octoplant-Plugin.git
cd Octoplant-Plugin

# 2. Eenmalig installeren (conda env + dependencies + exe bouwen)
.\scripts\install.ps1

# 3. .env aanpassen voor dit toestel
notepad .env

# 4. Credentials voorzien volgens interne procedure

# 5. Login testen
.\binaryTools\VDogCheckOut\publish\VDogCheckOut.exe login

# 6. Workspace openen in VS Code — MCP-server start automatisch
code .
```

## Omgevingsvariabelen (.env)

```ini
OCTOPLANT_SERVER=https://your-server:64023
OCTOPLANT_DOMAIN=AD-domein
OCTOPLANT_ARCHIVE_PATH=D:\vdClientArchive
OCTOPLANT_VDOG_CLIENT_PATH=C:\Program Files\vdogClient
OCTOPLANT_SSL_VERIFY=false
```

| Variabele | Gebruik |
|-----------|---------|
| `OCTOPLANT_SERVER` | Basis-URL voor REST API-aanroepen (export) |
| `OCTOPLANT_DOMAIN` | AD-domein (optioneel — ook per user in GUI) |
| `OCTOPLANT_ARCHIVE_PATH` | `/rd:` parameter voor CLI-tools |
| `OCTOPLANT_CHECKOUT_PATH` | Workspace mirror-bestemming (standaard `{projectroot}\octoPlantCheckouts`) |
| `OCTOPLANT_VDOG_CLIENT_PATH` | Map met `VDogAutoCheckOut.exe` en `VDogAutoExport.exe` |
| `OCTOPLANT_SSL_VERIFY` | `true`/`false` voor SSL-certificaatvalidatie |

> Gebruikersnaam en wachtwoord zijn **niet** aanwezig in `.env` en worden nooit
> blootgesteld aan het MCP-protocol of de AI. Ze worden intern beheerd door
> `VDogCheckOut.exe`.

## Python-omgeving

```bash
# Aanmaken (of via scripts\install.ps1)
conda create -n mcp-op python=3.12
conda activate mcp-op
pip install -e .
```

## VDogCheckOut.exe bouwen

```powershell
cd binaryTools\VDogCheckOut
dotnet publish VDogCheckOut.csproj --configuration Release --runtime win-x64 `
    --self-contained true -p:PublishSingleFile=true --output publish
```

De exe staat in `binaryTools\VDogCheckOut\publish\VDogCheckOut.exe` (self-contained,
geen .NET runtime vereist op het doelsysteem).