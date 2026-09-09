# MCP-tools

| Tool | Gebruik |
|---|---|
| `resolve_project` | Verplicht eerst: actuele installatie- en PLC-projectmap uit de gedeelde serverarchive bepalen. |
| `checkout_component` | Eén door `resolve_project` gevonden component read-only uitchecken. |
| `authenticate` | Eén OAuth2-verbindingstest via de wrapper uitvoeren. |

`VDogClient.exe` is geen MCP-tool: de CLI opent alleen de interactieve
versiondog-GUI en voert geen checkout uit. `VDogAutoCheckOut.exe` is de
native checkoutclient die uitsluitend via de wrapper wordt aangeroepen.

## Verboden: checkout-all

`checkout_all`, `--all`, een leeg componentpad en iedere andere brede checkout
zijn verboden. Zij kunnen alle beschikbare projectversies lokaal ophalen en
daardoor de harde schijf snel vullen. De MCP-server en wrapper accepteren
uitsluitend een expliciet `component_path` of `component_id`.
