# Check-out naar de sessieworkspace

`checkout_component` is read-only voor OctoPlant en vereist de absolute
`workspace_path` uit de initiële agent-handoff, met de beschikbare
`installation_name` en/of `cost_center`. Child-sessionworkspaces en
plugininstallatiemappen zijn nooit geldig als bestemming. Na een geslaagde checkout
spiegelt `VDogCheckOut.exe` het component met `robocopy /MIR` van de lokale
clientarchive naar:

```text
{workspace}\PLC-projecten\{installatienaam} - {kostenplaats}\{component_path}
```

Wanneer alleen een installatienaam of kostenplaats beschikbaar is, is dat de
naam van de map onder `PLC-projecten`. De tool retourneert zowel
`checkout_path` (de installatiemap) als `artifact_path` (de componentmap).
Een bestaand maar niet gevonden PLC-project retourneert `status: not_found`;
de tool voert nooit een bredere checkout uit.

Gebruik voor de tool altijd `component_path` uit `resolve_project`; voeg de
fysieke `ARCHIVE`-submap niet toe aan dit CLI-componentpad.
