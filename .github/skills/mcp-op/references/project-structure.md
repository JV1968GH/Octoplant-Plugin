# Configuratie

| Variabele | Betekenis |
|---|---|
| `OCTOPLANT_ARCHIVE_PATH` | Lokale clientarchive voor `VDogAutoExport.exe`. |
| `OCTOPLANT_SERVER_ARCHIVE_PATH` | Gedeelde, read-only serverarchive voor `resolve_project`; standaard `\\pOctoplan1\poctoplan1_D\vdServerArchive`. |
| `OCTOPLANT_VDOG_CLIENT_PATH` | Map met `VDogAutoExport.exe`, indien auto-discover niet volstaat. |

De gedeelde archive wordt nooit beschreven door de plugin. De runtime weigert
te starten als `OCTOPLANT_SERVER_ARCHIVE_PATH` gelijk is aan de lokale
`OCTOPLANT_ARCHIVE_PATH` of `OCTOPLANT_CHECKOUT_PATH`.
