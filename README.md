# dahlia-apps

App-Katalog für [Dahlia Linux](https://github.com/Fabiy99/dahlia-linux) /
App catalog for Dahlia Linux.

## Deutsch

Dahlia (ab 0.4) lädt `catalog.json` von
`https://raw.githubusercontent.com/Fabiy99/dahlia-apps/main/` (einstellbar in
`/etc/dahlia/apps.json`), alle 6 Stunden und mit "Katalog aktualisieren" im Dashboard.
Ist die Vorlage einer installierten App neuer, zeigt das Dashboard "Update auf X".

### Aufbau

| Datei | Inhalt |
| --- | --- |
| `apps/<id>.yaml` | eine App-Vorlage (Schema 2) |
| `catalog.json` | alle Vorlagen in einer Datei, erzeugt von `tools/build.py` |
| `tools/check.py` | Prüfung, läuft in der CI bei jedem PR |
| `tools/bump.py` | sucht neue Image-Versionen, `tools/bump.json` legt die Regeln fest |
| `.github/workflows/bump.yml` | täglich: neue Versionen als Pull Request `bump/images` |

### Vorlage

```yaml
schema: 2
id: paperless                        # a-z, 0-9, -; gleich dem Dateinamen
name: Paperless-ngx
category: productivity               # media, downloads, photos, books, cloud, productivity,
                                     # home, network, security, monitoring, communication,
                                     # development, tools, other
description: {de: "...", en: "..."}  # beide Sprachen sind Pflicht
website: https://docs.paperless-ngx.com/
notes: {de: "...", en: "..."}       # optional, Hinweise nach der Installation
web: {port: 8000, public_port: 8000} # Port im Container, Port im LAN
login: {user: admin, password: "{SECRET_ADMIN}"}   # optional, zeigt das Dashboard an
services:
  app:                               # Pflicht, Hauptdienst
    image: ghcr.io/paperless-ngx/paperless-ngx:2.18.4   # feste Version, nie latest
    depends_on: [db, redis]
    lan_ports:                       # optional, nur wenn nötig
      - {container: 22000, host: 22000, protocol: tcp}
    volumes:
      - {container: /usr/src/paperless/data, appdata: data}   # /mnt/user/appdata/<id>/data
      - {container: /usr/src/paperless/consume, share: scans} # /mnt/user/scans
    environment:
      PAPERLESS_DBHOST: db           # Dienste erreichen sich über ihren Namen
      PAPERLESS_DBPASS: "{SECRET_DB}"
    user: "{PUID}:{PGID}"            # optional
    command: [--flag]                # optional
    gpu: true                        # optional, nur mit schema: 3 / only with schema: 3
  db:
    image: postgres:17.6-alpine
    environment: {POSTGRES_PASSWORD: "{SECRET_DB}"}
    volumes:
      - {container: /var/lib/postgresql/data, appdata: db}
  redis:
    image: redis:8.2.1-alpine
```

Platzhalter: `{TZ}`, `{PUID}`, `{PGID}`, `{HOSTNAME}`, `{DOMAIN}`, `{SECRET_<NAME>}`
(Zufallswert, 32 Hex-Zeichen, bleibt bei Updates gleich). Andere Felder gibt es nicht;
`privileged`, Host-Netzwerk, Geräte, Capabilities und beliebige Host-Pfade lehnt Dahlia ab.
Deshalb fehlen Apps, die das brauchen (WireGuard, Tailscale, Frigate, Plex mit
Host-Netzwerk, Zigbee-Sticks, alles mit Docker-Socket).

`gpu: true` (ab Dahlia 0.8, nur mit `schema: 3`) gibt dem Dienst `/dev/dri` für
Hardware-Transcoding, wenn der Server eine Intel- oder AMD-GPU hat. Nur Apps, die es
nutzen, bekommen `schema: 3`; ältere Dahlia-Versionen überspringen diese Vorlagen.

Regeln der Prüfung: Version mit mindestens `major.minor` oder Datum; Web- und LAN-Ports
im ganzen Katalog eindeutig; reserviert sind 22, 80, 443, 5353, 8080 und 41000-41999
(53 nur als LAN-Port); `image: ...` steht auf einer eigenen Zeile.

### Updates

`tools/bump.py` liest die Tags jeder Registry und nimmt den neuesten Tag derselben Form
(`1.2.3` -> `1.2.4`, nie `-rc1`, `latest` oder `1`). Standard ist: gleiche Hauptversion.
Neue Hauptversionen stehen nur im Bericht des PRs und werden von Hand übernommen.
`tools/bump.json` setzt je Image `major`, `patch` oder `hold`.

Der Workflow braucht einmalig: Settings > Actions > General > "Allow GitHub Actions to
create and approve pull requests". PRs aus dem Workflow starten keine weitere CI; er
prüft den Katalog vor dem PR selbst.

### Neue App

1. `apps/<id>.yaml` anlegen.
2. `python3 tools/build.py`
3. Prüfen: `python3 tools/check.py --linux ../dahlia-linux --images`
4. Pull Request.

## English

Dahlia (0.4 and later) downloads `catalog.json` from
`https://raw.githubusercontent.com/Fabiy99/dahlia-apps/main/` (configurable in
`/etc/dahlia/apps.json`) every 6 hours and on "Refresh catalog" in the dashboard. When an
installed app's template is newer, the dashboard shows "Update to X".

### Layout

| File | Contents |
| --- | --- |
| `apps/<id>.yaml` | one app template (schema 2) |
| `catalog.json` | all templates in one file, written by `tools/build.py` |
| `tools/check.py` | checks, run by CI on every PR |
| `tools/bump.py` | looks for new image versions, rules in `tools/bump.json` |
| `.github/workflows/bump.yml` | daily: new versions as pull request `bump/images` |

### Template

See the example above. Placeholders: `{TZ}`, `{PUID}`, `{PGID}`, `{HOSTNAME}`, `{DOMAIN}`,
`{SECRET_<NAME>}` (random, 32 hex characters, kept across updates). There are no other
fields; Dahlia rejects `privileged`, host networking, devices, capabilities and arbitrary
host paths, so apps that need those (WireGuard, Tailscale, Frigate, Plex with host
networking, Zigbee sticks, anything with the Docker socket) are not in the catalog.

`gpu: true` (Dahlia 0.8 and later, only with `schema: 3`) gives the service `/dev/dri` for
hardware transcoding when the server has an Intel or AMD GPU. Only apps that use it get
`schema: 3`; older Dahlia versions skip those templates.

Check rules: version with at least `major.minor` or a date; web and LAN ports unique
across the catalog; 22, 80, 443, 5353, 8080 and 41000-41999 are reserved (53 only as a LAN
port); `image: ...` on its own line.

### Updates

`tools/bump.py` reads each registry's tags and takes the newest tag of the same form
(`1.2.3` -> `1.2.4`, never `-rc1`, `latest` or `1`). Default: same major version. New major
versions are only listed in the PR report and applied by hand. `tools/bump.json` sets
`major`, `patch` or `hold` per image.

The workflow needs once: Settings > Actions > General > "Allow GitHub Actions to create
and approve pull requests". PRs opened by the workflow start no further CI; it checks the
catalog itself before opening the PR.

### New app

1. Add `apps/<id>.yaml`.
2. `python3 tools/build.py`
3. Check: `python3 tools/check.py --linux ../dahlia-linux --images`
4. Open a pull request.

## Lizenz / License

GPLv3, see [LICENSE](LICENSE).
