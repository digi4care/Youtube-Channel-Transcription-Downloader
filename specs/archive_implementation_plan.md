# Archive-Functionaliteit Implementatie Plan

## Overzicht

Implementatie van download-archive functionaliteit voor YouTube Channel Transcript Downloader.

Dit zorgt ervoor dat het script hervat waar het gebleven was na rate limiting, in plaats van altijd vanaf 0 te beginnen.

## Gesegmenteerde Stappen

### Configuratie (Stap 1-2)

1. **Config veld toevoegen**: `enable_archive: bool = True` aan `TranscriptOptions` - standaard aan zodat het automatisch werkt
2. **Archive pad logica**: Bepaal pad: `downloads/{channel_name}/.transcript_archive.txt`

### Archive Management (Stap 3-5)

1. **Archive-lezer**: Nieuwe `ArchiveManager` class die archive-bestand kan lezen en lijst van verwerkte video-IDs teruggeeft
2. **Video filter**: Functie die video-lijst filtert - alleen video's die níet in archive staan worden verwerkt
3. **Archive-schrijver**: Na succesvolle transcript-download wordt video-ID toegevoegd aan archive-bestand

### Integratie (Stap 6-8)

1. **Hoofdproces aanpassen**: `YouTubeTranscriptDownloader` integreren met archive-logica in `process_single_channel()`
2. **Error handling**: Archive operaties moeten niet crashen bij corrupte/ontbrekende bestanden
3. **Backward compatibility**: Bestaande runs blijven werken (archive is optioneel)

## Voordelen

- **Resume capability**: Hervat na rate limiting waar gebleven
- **Per-kanaal archives**: Geen conflicten tussen verschillende kanalen
- **Backward compatible**: Bestaande installs werken door
- **Veilig**: Archive operaties crashen niet bij problemen

## Implementatie Details

- Archive bestand: eenvoudig tekstformaat, één video-ID per regel
- Formaat: `VIDEO_ID` (bijv. `dQw4w9WgXcQ`)
- Locatie: `downloads/{channel_name}/.transcript_archive.txt`
- Config: `enable_archive` in `[transcripts]` sectie van config.toml

## Test Scenario

1. Channel met 50 video's
2. Script downloadt eerste 40, raakt rate limit
3. Volgende dag hervat bij video 41
4. Archive toont 40 verwerkte video's
