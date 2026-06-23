# OctoPlant Archiefstructuur & Navigatie

Hoe je het juiste componentpad bepaalt op basis van installatienaam, kostplaats of PLC-nummer.

## Mapstructuur

De versiondog client archive volgt een vaste hiërarchie van 3 niveaus:

```
{archive_root}\
├── RWZI's\
│   └── {kostplaats} - {installatienaam}\
│       ├── {kostplaats} - {installatienaam}, PLC01
│       ├── {kostplaats} - {installatienaam}, PLC01_CE   ← voorkeur boven PLC01
│       ├── {kostplaats} - {installatienaam}, PLC02_CE
│       └── ...
└── PS\
    └── {kostplaats} - {installatienaam}\
        └── {kostplaats} - {installatienaam}, PLC01_CE
```

## Sleutelvelden

| Veld | Beschrijving | Voorbeeld |
|------|-------------|---------|
| **Installatienaam** | Naam van de RWZI of het pompstation | `Dendermonde`, `Gent`, `Dessel` |
| **Kostplaats** | 6-cijferige code vóór de naam | `100026`, `100020`, `100078` |
| **PLC-nummer** | 2-cijferig nummer na `PLC` | `01`, `02`, `06` |

## Padresolutie-regels

### 1. Rootmap (RWZI's vs PS)
- Prompt vermeldt **RWZI** → gebruik `RWZI's`
- Prompt vermeldt **PS** of **pompstation** → gebruik `PS`
- **Niets vermeld** → standaard `RWZI's`

### 2. Installatiesubmap
- Zoek de map waarvan de naam de installatienaam of kostplaats bevat
- Formaat: `{kostplaats} - {installatienaam}` (bijv. `100026 - Dendermonde`)

### 3. Componentmap (PLC-selectie)
- Formaat: `{kostplaats} - {installatienaam}, PLC{##}` (bijv. `100026 - Dendermonde, PLC06_CE`)
- **Geen PLC-nummer opgegeven** → standaard `PLC01`
- **Zowel `PLC##` als `PLC##_CE` bestaan** → gebruik altijd `PLC##_CE`, tenzij expliciet anders gevraagd
- **Alleen `PLC##`** (geen _CE variant) → gebruik `PLC##`

## Padopbouw (stap voor stap)

Gegeven: *"RWZI Dendermonde, PLC06 uitchecken"*

1. Rootmap: `RWZI's` (want RWZI vermeld)
2. Installatiesubmap: `100026 - Dendermonde` (zoek op naam)
3. Componentmap: `100026 - Dendermonde, PLC06_CE` (PLC06 + _CE voorkeur)

**Resulterende `/dirR:` waarde:**
```
\RWZI's\100026 - Dendermonde\100026 - Dendermonde, PLC06_CE
```

> ⚠️ De leading backslash is **verplicht** — zonder geeft `VDogAutoCheckOut.exe` fout 20043.

## Voorbeelden

| Prompt | `/dirR:` parameter |
|--------|-------------------|
| "RWZI Dendermonde PLC06" | `\RWZI's\100026 - Dendermonde\100026 - Dendermonde, PLC06_CE` |
| "RWZI Gent" *(geen PLC)* | `\RWZI's\100020 - Gent\100020 - Gent, PLC01_CE` |
| "PS Achel PLC02" | `\PS\100138 - Achel\100138 - Achel, PLC02_CE` |
| "kostplaats 100078" *(geen PLC)* | `\RWZI's\100078 - Dessel\100078 - Dessel, PLC01_CE` |

## Bekende kostplaatsen (lokale archive)

| Kostplaats | Naam | Type |
|------------|------|------|
| 100020 | Gent | RWZI |
| 100026 | Dendermonde | RWZI |
| 100078 | Dessel | RWZI |
| 100114 | Overpelt | RWZI |
| 100138 | Achel | RWZI |

> **Let op:** De lokale archive bevat enkel componenten die al eens zijn uitgecheckt. Componenten die nog nooit zijn uitgecheckt bestaan wel op de server maar nog niet lokaal. Gebruik de `/dirR:` parameter op basis van de naamgevingsconventie — de server kent het pad ook als de map lokaal nog niet bestaat.

## Gebruik in MCP-tools

Bij `checkout_component` of `checkout_all` gebruik je de opgebouwde waarde als `component_path`:

```python
checkout_component(
    component_path=r"\RWZI's\100026 - Dendermonde\100026 - Dendermonde, PLC06_CE"
)
```
