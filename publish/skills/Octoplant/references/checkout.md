# Gerichte checkoutbestemming

`checkout_component` voert uitsluitend een read-only, gerichte componentcheckout
uit. `component_path` of `component_id` is verplicht; brede checkouts zijn
verboden.

Met een absolute `workspace_path` leidt de tool de installatie-root af en geeft
die rechtstreeks als `/RD` aan `VDogAutoCheckOut.exe`. De root wordt zo nodig
aangemaakt en het component komt op:

```text
{workspace}\PLC-projecten\{installatienaam} - {kostenplaats}\{component_path}
```

Wanneer `workspace_path` ontbreekt, gebruikt de wrapper uitsluitend
`OCTOPLANT_CLIENT_ARCHIVE_PATH` uit de lokale instellingen als `/RD`. Die
clientarchive wordt alleen gelezen, nooit gewijzigd, en er is geen mirrorstap.
De tool retourneert in beide gevallen het concrete `checkout_path` en
`artifact_path`. Een niet gevonden project retourneert `status: not_found`.

Gebruik voor de tool altijd `component_path` uit `resolve_project`; voeg de
fysieke `ARCHIVE`-submap niet toe aan dit CLI-componentpad.
