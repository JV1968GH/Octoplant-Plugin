# Check-out naar de sessieworkspace

`checkout_component` is read-only voor OctoPlant. Na een geslaagde checkout
spiegelt `VDogCheckOut.exe` het component met `robocopy /MIR` van de lokale
clientarchive naar:

```text
{workspace}\octoPlantCheckouts\{component_path}
```

Deze bestemming is vast en wordt afgeleid van de runtime-workspace:
`octoPlantCheckouts` onder die workspace.

Gebruik voor de tool altijd `component_path` uit `resolve_project`; voeg de
fysieke `ARCHIVE`-submap niet toe aan dit CLI-componentpad.
