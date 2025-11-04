# AUDAC MTX – Home Assistant (HACS)

Intégration simple pour AUDAC MTX48/MTX88 via TCP (port 5001).
- Une entité `media_player` par zone
- Sélection **Source** et contrôle **Volume/Mute**
- Lecture d'état réelle (`GZI0x`) pour volume/mute/source

## Installation (HACS)
1. Ajoutez ce dépôt dans HACS → Custom repositories (Integration).
2. Installez **AUDAC MTX**, redémarrez Home Assistant.
3. Ajoutez l'intégration **AUDAC MTX** (host, port, zones).

## Protocole
- Dest = `X001`, Source ≤ 4 chars (ex. `HA`)
- Source : `SRx|y` (x sans zéro, y=0..8)
- Volume : `SVx|v` (v=0..70, **0 = max**). L’UI 0..100% est convertie automatiquement.
- Mute : `SM0x|0/1` (x avec zéro)
- État : `GZI0x|0` → `ZIxx|vol^route^mute^bass^treble`
