# Gerichte checkoutbestemming

`checkout_component` voert uitsluitend een read-only, gerichte componentcheckout
uit. `component_path` of `component_id` is verplicht; brede checkouts zijn
verboden.

Met een absolute `workspace_path` leidt de tool de installatie-root af. De
native checkout gebruikt altijd de geconfigureerde clientarchive als `/RD`;
na succes wordt uitsluitend het geresolveerde component naar de artifactroot
gespiegeld. Het component komt op:

```text
{workspace}\PLC-projecten\{installatienaam} - {kostenplaats}\{component_path}
```

Wanneer `workspace_path` ontbreekt, retourneert de tool de componentlocatie in
de lokale clientarchive. Een checkout kan alleen worden vrijgegeven met
`checkin_unchanged_component` na directe gebruikersbevestiging. Die native
check-in maakt nooit een versie (`Enabled=N`), slaat vergelijking over
(`WithoutComparison=Y`) en geeft de checkout vrij (`ReleaseAfterCheckIn=Y`).

Gebruik voor de tool altijd `component_path` uit `resolve_project`; voeg de
fysieke `ARCHIVE`-submap niet toe aan dit CLI-componentpad.
