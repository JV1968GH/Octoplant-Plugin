# CLI-export

Exports verlopen uitsluitend via `VDogAutoExport.exe` met een bestaande
INI-configuratie. Roep vóór de export altijd `resolve_project` aan. Gebruik
alleen `archive_relative_path` wanneer het betrokken INI-veld expliciet een
filesystempad in de gedeelde archive verwacht; gebruik anders het path type
dat de INI-documentatie voorschrijft.

De CLI krijgt de lokale clientarchive mee via `OCTOPLANT_ARCHIVE_PATH`; de
gedeelde serverarchive is uitsluitend de read-only bron voor padresolutie.
Credentials, tokens en de ruwe uitvoer van de binary mogen nooit in
MCP-responses terechtkomen.
