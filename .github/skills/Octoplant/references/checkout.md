# Check-out naar de sessieworkspace

`checkout_component` is read-only voor OctoPlant. Na een geslaagde checkout
spiegelt `VDogCheckOut.exe` het component met `robocopy /MIR` van de lokale
clientarchive naar:

```text
{workspace}\octoPlantCheckouts\{component_path}
```

`OCTOPLANT_CHECKOUT_PATH` mag deze bestemming alleen naar een dedicatede
sessieworkspace-map verplaatsen. Als de variabele leeg is, is
`octoPlantCheckouts` onder de pluginworkspace de standaard.

Gebruik voor de tool altijd `component_path` uit `resolve_project`; voeg de
fysieke `ARCHIVE`-submap niet toe aan dit CLI-componentpad.
