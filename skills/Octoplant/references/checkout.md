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
de lokale clientarchive. Gebruik voor de volledige lifecycle
`checkout_copy_and_release_component`: die vereist een absolute
`workspace_path` en voert de native vrijgave alleen uit nadat de checkout én
artifactmirror zijn geslaagd. De tool vereist directe gebruikersbevestiging.
`checkin_unchanged_component` blijft beschikbaar voor een afzonderlijke,
bevestigde vrijgave. De native check-in maakt nooit een versie (`Enabled=N`),
slaat vergelijking over (`WithoutComparison=Y`) en geeft de checkout vrij
(`ReleaseAfterCheckIn=Y`).

Gebruik voor de tool altijd `component_path` uit `resolve_project`; voeg de
fysieke `ARCHIVE`-submap niet toe aan dit CLI-componentpad.

## Resultaatafronding

Na iedere ontvangen `work_request` levert de specialist, voor hij idle wordt,
precies een volledig en schema-geldig `work_result` v1.2 JSON-object. Behoud
`correlation_id` en `step_id` exact; neem `status`, `output_artifacts`,
niet-lege `evidence` en niet-lege `risks` altijd op. Gebruik geen proza,
tooluitvoer of idle als vervanging.

Bij `completed`, `blocked`, `failed`, `ambiguous`, `needs_input` en `unsafe`
blijft het resultaat niet-sensitief. `output_artifacts` is aanwezig en bevat
alleen objecten met exact `ref`, `kind` en `local_path`; gebruik `[]` wanneer
geen lokaal artifact bestaat.
