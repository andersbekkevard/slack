# Hvordan legge til meldinger

1. **Opprett en fil** i `messages/` mappen
2. **Navngi filen** med datoen du vil sende meldingen (f.eks. `15.12.25.md` for 15. desember 2025)
3. **Skriv meldingen** i filen
4. **Last opp** filen til GitHub

Boten sjekker hver dag klokka 08:00 UTC og sender meldinger som matcher dagens dato.

## Velg Slack-kanal per mappe (valgfritt)

Hvis en undermappe i `messages/` inneholder en fil kalt `SLACK_CHANNEL_ID`, vil meldinger i den mappen sendes til kanalen angitt i denne filen (første ikke-tomme linje). Hvis filen ikke finnes, brukes standardkanalen fra miljøvariablene `SLACK_CHANNEL_ID` eller `CHANNEL_ID`.

### Eksempel
- Fil: `25.12.25.md`
- Innhold: "God jul!"
- Resultat: Meldingen sendes automatisk 25. desember 2025