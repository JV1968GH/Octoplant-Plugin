# MCP-tools

| Tool | Gebruik |
|---|---|
| `resolve_project` | Verplicht eerst: actuele installatie- en PLC-projectmap uit de gedeelde serverarchive bepalen. |
| `checkout_copy_and_release_component` | **Standaard:** één opgelost component uitchecken, naar de workspace spiegelen en daarna versieloos vrijgeven; vereist directe gebruikersbevestiging. |
| `checkout_component` | Alleen wanneer een gebruiker uitdrukkelijk een behouden native checkout vraagt. |
| `checkin_unchanged_component` | Eén al bestaande native checkout versieloos vrijgeven na directe gebruikersbevestiging. |
| `authenticate` | Eén OAuth2-verbindingstest via de wrapper uitvoeren. |

`VDogClient.exe` is geen MCP-tool: de CLI opent alleen de interactieve
versiondog-GUI en voert geen checkout uit. `VDogAutoCheckOut.exe` is de
native checkoutclient die uitsluitend via de wrapper wordt aangeroepen.

Bij gebruik via de Octoplant Specialist geeft de gebruiker geen toolparameters
door. De zichtbare `⬇️✋ HANDOFF — OctoPlant` bevat de gevraagde actie en
projectcontext; de specialist handelt de resolutie en veilige flow intern af
en sluit af met `↩️ RESULTAAT — <terminal state>`.

## Verboden: checkout-all

`checkout_all`, `--all`, een leeg componentpad en iedere andere brede checkout
zijn verboden. Zij kunnen alle beschikbare projectversies lokaal ophalen en
daardoor de harde schijf snel vullen. De MCP-server en wrapper accepteren
uitsluitend een expliciet `component_path` of `component_id`.
