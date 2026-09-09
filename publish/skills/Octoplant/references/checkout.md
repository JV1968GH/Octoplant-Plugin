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

## Bestaande lokale checkout

Roep direct na `resolve_project` eerst
`inspect_checkout_destination(workspace_path, installation_name, cost_center,
component_path)` aan. De inspectie creëert, verwijdert en wijzigt niets. Zij
retourneert het exacte `checkout_path` (installatieroot) en `artifact_path`
(installatieroot plus componentpad).

Bij `status: existing_checkout_detected` moet de gebruiker expliciet kiezen:

1. `replace`: verwijder uitsluitend het gerapporteerde lokale `artifact_path`
   en voer daarna een verse gerichte checkout uit.
2. `reuse`: retourneer de bestaande lokale paden en vervolg de orkestratie
   zonder native checkout.
3. `stop`: behoud de bestaande lokale versie en stop zonder wijziging.

`checkout_component` dwingt deze keuze ook af als de inspectie wordt
overgeslagen: een bestaand artifact geeft
`status: existing_checkout_requires_choice` terug en start de native client
niet. De uitkomsten zijn respectievelijk `checked_out` met
`outcome: fresh_checkout`, `existing_checkout_reused` met
`outcome: reused_existing_checkout`, en `existing_checkout_stopped` met
`outcome: stopped_existing_checkout`. Een onveilig bestand of link op de
bestemming retourneert `checkout_destination_unsafe`; dit wordt nooit
automatisch verwijderd.
