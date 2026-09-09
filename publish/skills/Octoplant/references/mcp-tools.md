# MCP-tools

| Tool | Gebruik |
|---|---|
| `resolve_project` | Verplicht eerst: actuele installatie- en PLC-projectmap uit de gedeelde serverarchive bepalen. |
| `inspect_checkout_destination` | Direct daarna: de exacte lokale artifactmap controleren zonder wijziging. |
| `checkout_component` | Eén door `resolve_project` gevonden component read-only uitchecken. |
| `authenticate` | Eén OAuth2-verbindingstest via de wrapper uitvoeren. |

`VDogClient.exe` is geen MCP-tool: de CLI opent alleen de interactieve
versiondog-GUI en voert geen checkout uit. `VDogAutoCheckOut.exe` is de
native checkoutclient die uitsluitend via de wrapper wordt aangeroepen.

Een inspectie met `existing_checkout_detected` vereist een expliciete
`collision_action` voor `checkout_component`: `replace`, `reuse` of `stop`.
Zonder selectie retourneert de checkout `existing_checkout_requires_choice`
zonder de native client aan te roepen. Alleen `replace` verwijdert data, en
dan uitsluitend het exacte lokale `artifact_path`; de gedeelde archive blijft
strikt read-only.

## Verboden: checkout-all

`checkout_all`, `--all`, een leeg componentpad en iedere andere brede checkout
zijn verboden. Zij kunnen alle beschikbare projectversies lokaal ophalen en
daardoor de harde schijf snel vullen. De MCP-server en wrapper accepteren
uitsluitend een expliciet `component_path` of `component_id`.
