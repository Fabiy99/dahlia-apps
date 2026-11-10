# dahlia-apps

App-Katalog für [Dahlia Linux](https://github.com/Fabiy99/dahlia-linux) /
App catalog for Dahlia Linux.

## Deutsch

Dahlia lädt den Katalog von
`https://raw.githubusercontent.com/Fabiy99/dahlia-apps/main/` (einstellbar in
`/etc/dahlia/apps.json`). Im Dashboard: Apps, "Katalog aktualisieren".

### Aufbau

| Datei | Inhalt |
| --- | --- |
| `index.json` | `{"apps": [...]}`, alle IDs, sortiert |
| `apps/<id>.yaml` | eine App-Vorlage |
| `tools/check.py` | Prüfung, läuft in der CI bei jedem PR |

### Vorlage

```yaml
schema: 1
id: uptime-kuma                      # a-z, 0-9, -; gleich dem Dateinamen
name: Uptime Kuma
description:                         # beide Sprachen sind Pflicht
  de: Überwacht Webseiten und Dienste.
  en: Monitors websites and services.
image: louislam/uptime-kuma:1.23.16  # feste Version, nie latest
web: {port: 3001, public_port: 3001} # Port im Container, Port im LAN
lan_ports:                           # optional, nur wenn nötig
  - {container: 22000, host: 22000, protocol: tcp}
volumes:
  - {container: /app/data, appdata: data}             # /mnt/user/appdata/<id>/data
  - {container: /media, share: media, readonly: true} # /mnt/user/media
environment:
  TZ: "{TZ}"                         # Platzhalter: {TZ}, {PUID}, {PGID}
```

Andere Felder gibt es nicht. `privileged`, Host-Netzwerk, Geräte, Capabilities und
beliebige Host-Pfade lehnt Dahlia ab. Der Web-Port läuft nur auf 127.0.0.1, im LAN ist die
App über nginx unter `http://<server>:<public_port>/` erreichbar. Öffentliche Ports
dürfen sich zwischen Apps nicht überschneiden; reserviert sind 22, 53, 80, 443, 5353, 8080
und 41000-41999.

### Neue App

1. `apps/<id>.yaml` anlegen, ID in `index.json` eintragen.
2. Prüfen: `python3 tools/check.py --linux ../dahlia-linux --images`
3. Pull Request. Die CI prüft Vorlage und Image.

## English

Dahlia loads the catalog from
`https://raw.githubusercontent.com/Fabiy99/dahlia-apps/main/` (configurable in
`/etc/dahlia/apps.json`). In the dashboard: Apps, "Refresh catalog".

### Layout

| File | Contents |
| --- | --- |
| `index.json` | `{"apps": [...]}`, all ids, sorted |
| `apps/<id>.yaml` | one app template |
| `tools/check.py` | checks, run by CI on every PR |

### Template

See the example above. There are no other fields. Dahlia rejects `privileged`, host
networking, devices, capabilities and arbitrary host paths. The web port is bound to
127.0.0.1 only; in the LAN the app is reachable through nginx at
`http://<server>:<public_port>/`. Public ports must not overlap between apps; 22, 53, 80,
443, 5353, 8080 and 41000-41999 are reserved. `description` needs both `de` and `en`.

### New app

1. Add `apps/<id>.yaml` and the id in `index.json`.
2. Check: `python3 tools/check.py --linux ../dahlia-linux --images`
3. Open a pull request. CI checks the template and the image.

## Lizenz / License

GPLv3, see [LICENSE](LICENSE).
