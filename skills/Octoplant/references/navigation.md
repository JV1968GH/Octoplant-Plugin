# Serverarchive-navigatie

`resolve_project` leest bij elke oproep de vast ingebouwde, read-only
RWZI-serverarchive. Deze locatie is niet via configuratie te wijzigen.

Deze share is strikt **read-only** voor de plugin. Gebruik haar nooit als
de instelling `OCTOPLANT_CLIENT_ARCHIVE_PATH` onder hoofdkaart `Octoplant`.
Alle schrijf- en mirroracties horen uitsluitend in de lokale clientarchive en
de sessieworkspace thuis.

## Resolutieregels

1. De vaste hoofdmap is `RWZI's`.
2. Normaliseer een korte kostenplaats altijd naar `100000 + kostenplaats`:
   `0026` wordt dus exact `100026`. Zoek vervolgens uitsluitend naar die
   volledige cijfergroep; deelmatches zoals `100268` zijn nooit geldig. De
   installatienaam mag vóór of na die kostenplaats staan.
3. Zoek in de gevonden `ARCHIVE`-submap naar het gevraagde PLC-project.
4. Vergelijk PLC-nummers ongeacht voorloopnullen. Een `_CE`-variant krijgt
   voorrang boven een klassieke variant.
5. Als kandidaten inhoudelijk gelijk zijn, vergelijk dan de timestamp van de
   recentste versie in elk project en kies de recentste.

Gebruik geen vaste naamgevingsconventie als vervanging voor deze scan: de
archive is de bron van waarheid voor ontbrekende namen, omgekeerde
kostenplaatsen en typefouten.

De specialist gebruikt de geresolveerde paden uitsluitend intern. Een gebruiker
of orchestrator geeft alleen de zichtbare `⬇️✋ HANDOFF — OctoPlant`; de
specialist geeft geen component- of archiefpad weer in het eindresultaat.
