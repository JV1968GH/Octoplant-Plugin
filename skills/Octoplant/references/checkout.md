# Check-out naar de sessieworkspace

`checkout_component` is read-only voor OctoPlant en vereist de absolute
`workspace_path` van de hoofdchat. Een pad onder
`.copilot\session-state\...\files` wordt automatisch opgelost naar de
projectworkspace (`cwd`) van die sessie. Na een geslaagde checkout
spiegelt `VDogCheckOut.exe` het component met `robocopy /MIR` van de lokale
clientarchive naar:

```text
{workspace}\octoPlantCheckouts\{component_path}
```

De MCP-server draait vanuit de plugininstallatiemap, maar gebruikt uitsluitend
de verplichte `workspace_path` als bestemming: `octoPlantCheckouts` onder de
workspace van de hoofdchat, nooit onder de plugininstallatiemap.

Gebruik voor de tool altijd `component_path` uit `resolve_project`; voeg de
fysieke `ARCHIVE`-submap niet toe aan dit CLI-componentpad.
