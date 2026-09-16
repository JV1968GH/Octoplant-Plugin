# MCP-tools

| Tool | Gebruik |
|---|---|
| `resolve_project` | Verplicht eerst: actuele installatie- en PLC-projectmap uit de gedeelde serverarchive bepalen. |
| `checkout_copy_and_release_component` | **Standaard:** één opgelost component uitchecken, alleen het unieke `.stu`-bestand uit een leaf-map naar de workspace kopiëren en daarna versieloos vrijgeven. `full_component=true` spiegelt de volledige componentstructuur. |
| `checkout_component` | Alleen wanneer een gebruiker uitdrukkelijk een behouden native checkout vraagt; standaard wordt bij een workspace alleen het unieke `.stu`-bestand uit een leaf-map gekopieerd. |
| `checkin_unchanged_component` | Eén al bestaande native checkout versieloos vrijgeven. |
| `authenticate` | Eén OAuth2-verbindingstest via de wrapper uitvoeren. |

`VDogClient.exe` is geen MCP-tool: de CLI opent alleen de interactieve
versiondog-GUI en voert geen checkout uit. `VDogAutoCheckOut.exe` is de
native checkoutclient die uitsluitend via de wrapper wordt aangeroepen.

Bij gebruik via Octoplant geeft de gebruiker geen toolparameters
door. De zichtbare `⬇️✋ HANDOFF — Octoplant` bevat de gevraagde actie en
projectcontext; Octoplant handelt de resolutie en veilige flow intern af
en sluit af met `↩️ RESULTAAT — <terminal state>`.

## Verboden: checkout-all

`checkout_all`, `--all`, een leeg componentpad en iedere andere brede checkout
zijn verboden. Zij kunnen alle beschikbare projectversies lokaal ophalen en
daardoor de harde schijf snel vullen. De MCP-server en wrapper accepteren
uitsluitend een expliciet `component_path` of `component_id`.
