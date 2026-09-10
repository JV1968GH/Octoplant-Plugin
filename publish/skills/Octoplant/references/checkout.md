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
artifactmirror zijn geslaagd. `checkin_unchanged_component` blijft beschikbaar
voor een afzonderlijke vrijgave. De native check-in maakt nooit een versie (`Enabled=N`),
slaat vergelijking over (`WithoutComparison=Y`) en geeft de checkout vrij
(`ReleaseAfterCheckIn=Y`).

Gebruik voor de tool altijd `component_path` uit `resolve_project`; voeg de
fysieke `ARCHIVE`-submap niet toe aan dit CLI-componentpad.

## Gedeelde handoff en resultaat

Geef de specialist een zichtbaar `⬇️✋ HANDOFF — OctoPlant`-blok met de actie,
installatie of kostenplaats, het PLC indien bekend en een absolute workspace
voor een lokale projectkopie. De specialist resolveert de
component zelf en voert checkout, lokale mirror en versieloze vrijgave als één
veilige flow uit.

De enige eindvorm is `↩️ RESULTAAT — <terminal state>`, met een van:
✅ COMPLETED, 🔎 NOT_FOUND, ❓ NEEDS_INPUT, ⚠️ BLOCKED, ❌ FAILED of 🛑 UNSAFE.
Bij ✅ COMPLETED geeft het resultaat alleen een niet-sensitieve samenvatting
en het lokale projectpad. Bij de overige states geeft het alleen een korte,
niet-sensitieve toelichting. Geef geen JSON, toolpayloads, identifiers,
evidence, risico's of lifecyclevelden weer.
