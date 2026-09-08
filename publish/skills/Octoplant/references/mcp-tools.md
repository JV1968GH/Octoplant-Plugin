# MCP-tools

| Tool | Gebruik |
|---|---|
| `resolve_project` | Verplicht eerst: actuele installatie- en PLC-projectmap uit de gedeelde serverarchive bepalen. |
| `checkout_component` | Een door `resolve_project` gevonden component read-only uitchecken naar de initiële promptworkspace. |
| `authenticate` | Eén OAuth2-verbindingstest via de wrapper uitvoeren. |

`VDogClient.exe` is geen MCP-tool: de CLI opent alleen de interactieve
versiondog-GUI en voert geen checkout uit. `VDogAutoCheckOut.exe` is de
native checkoutclient die uitsluitend via de wrapper wordt aangeroepen.
