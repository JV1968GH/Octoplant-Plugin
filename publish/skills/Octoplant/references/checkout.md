# Gerichte checkoutbestemming

`checkout_component` voert uitsluitend een read-only, gerichte componentcheckout
uit. `component_path` of `component_id` is verplicht; brede checkouts zijn
verboden.

Met een absolute `workspace_path` leidt de tool de installatie-root af. De
native checkout gebruikt altijd de geconfigureerde clientarchive als `/RD`;
na succes wordt standaard uitsluitend het unieke `.stu`-bestand uit een
leaf-map van het geresolveerde component naar de artifactroot gekopieerd. Met
`full_component=true` wordt de volledige componentstructuur zoals voorheen
gespiegeld. Het artifact komt op:

```text
{workspace}\PLC-projecten\{installatienaam} - {kostenplaats}\{component_path}
```

Een optionele `destination_folder` heeft voorrang op deze legacy-routing. Die
moet een bestaande absolute map zijn. Bij een standaardcheckout kopieert
Octoplant het unieke `.stu`-bestand rechtstreeks als
`{destination_folder}\{stu-bestandsnaam}` en maakt of gebruikt hij geen enkele
submap daaronder. Zonder `destination_folder` blijft de bovenstaande
`checkout_root.joinpath(*component_parts)`-bestemming ongewijzigd.

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

Geef Octoplant een zichtbaar `⬇️✋ HANDOFF — Octoplant`-blok met de actie,
installatie of kostenplaats, het PLC indien bekend en een absolute workspace
voor een lokale projectkopie. Een orchestrator met een al berekende directe
installatiemap geeft die als `Destination folder` door; Octoplant resolveert de
component zelf en voert checkout, lokale mirror en versieloze vrijgave als één
veilige flow uit.

De enige eindvorm is `↩️ RESULTAAT — <terminal state>`, met een van:
✅ COMPLETED, 🔎 NOT_FOUND, ❓ NEEDS_INPUT, ⚠️ BLOCKED, ❌ FAILED of 🛑 UNSAFE.
Bij ✅ COMPLETED geeft het resultaat alleen een niet-sensitieve samenvatting
en het lokale projectpad. Bij de overige states geeft het alleen een korte,
niet-sensitieve toelichting. Geef geen JSON, toolpayloads, identifiers,
evidence, risico's of lifecyclevelden weer.
