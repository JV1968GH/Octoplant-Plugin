# Serverarchive-navigatie

`resolve_project` leest de gedeelde archive
`\\pOctoplan1\poctoplan1_D\vdServerArchive` bij elke oproep. De locatie kan
alleen voor een andere installatie worden gewijzigd via
`OCTOPLANT_SERVER_ARCHIVE_PATH`.

Deze share is strikt **read-only** voor de plugin. Gebruik haar nooit als
`OCTOPLANT_ARCHIVE_PATH` of `OCTOPLANT_CHECKOUT_PATH`; de runtime weigert die
configuratie. Alle schrijf- en mirroracties horen uitsluitend in de lokale
clientarchive en de sessieworkspace thuis.

## Resolutieregels

1. Gebruik standaard de hoofdmap `RWZI's`. Geef `root_name="PS"` voor
   pompstations; een andere expliciete hoofdmap wordt eveneens ondersteund.
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

De response bevat twee expliciete paden:

```text
component_path: \{hoofdmap}\{installatiemap}\{PLC-project}
archive_relative_path: \{hoofdmap}\{installatiemap}\ARCHIVE\{PLC-project}
```

`component_path` is het pad voor `checkout_component`; de CLI-serverboom kent
de filesystemmap `ARCHIVE` niet. `archive_relative_path` is uitsluitend voor
INI-velden die expliciet een pad in de gedeelde archive verwachten.
