"""Read-only access to container registries (Docker Hub, ghcr.io, quay.io, ...).

Only anonymous token auth and the registry v2 API; no Docker needed.
Docker Hub counts manifest GETs against a small anonymous pull limit, so
existence checks use HEAD requests, which it does not count.
"""

import http.client
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request

TIMEOUT = 30
MANIFEST_TYPES = (
    "application/vnd.oci.image.index.v1+json, "
    "application/vnd.docker.distribution.manifest.list.v2+json, "
    "application/vnd.oci.image.manifest.v1+json, "
    "application/vnd.docker.distribution.manifest.v2+json"
)
HOSTS = {"docker.io": "registry-1.docker.io"}


class RegistryError(Exception):
    pass


def split_image(image: str) -> tuple[str, str, str]:
    """registry, repository, tag. Digests are not handled here."""
    name, _, tag = image.split("@")[0].rpartition(":")
    first = name.split("/")[0]
    if "/" in name and ("." in first or ":" in first or first == "localhost"):
        registry, repo = name.split("/", 1)
    else:
        registry, repo = "docker.io", name
    if registry == "docker.io" and "/" not in repo:
        repo = "library/" + repo
    return registry, repo, tag


_tokens: dict[tuple[str, str], str] = {}


def _request(method: str, url: str, headers: dict) -> tuple[int, dict, bytes]:
    req = urllib.request.Request(url, method=method, headers=headers)
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                return r.status, dict(r.headers), r.read()
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and attempt < 3:
                time.sleep(2 ** attempt * 3)
                continue
            return e.code, dict(e.headers), e.read()
        # Registries and CDNs drop connections now and then under load;
        # http.client raises those as RemoteDisconnected/ConnectionError.
        except (urllib.error.URLError, TimeoutError, ConnectionError, http.client.HTTPException) as e:
            if attempt < 3:
                time.sleep(2 ** attempt * 3)
                continue
            raise RegistryError(f"{url}: {e}") from None
    raise RegistryError(f"{url}: giving up")


def _token(registry: str, repo: str, challenge: str) -> str:
    key = (registry, repo)
    if key in _tokens:
        return _tokens[key]
    params = dict(re.findall(r'(\w+)="([^"]*)"', challenge))
    realm = params.pop("realm", None)
    if not realm:
        raise RegistryError(f"{registry}: no token realm in {challenge!r}")
    params.setdefault("scope", f"repository:{repo}:pull")
    status, _, body = _request("GET", realm + "?" + urllib.parse.urlencode(params), {})
    if status != 200:
        raise RegistryError(f"{registry}: token request failed ({status})")
    data = json.loads(body)
    tok = data.get("token") or data.get("access_token")
    _tokens[key] = tok
    return tok


def call(registry: str, repo: str, method: str, path: str, headers: dict | None = None):
    host = HOSTS.get(registry, registry)
    url = path if path.startswith("https://") else f"https://{host}/v2/{repo}/{path}"
    headers = dict(headers or {})
    tok = _tokens.get((registry, repo))
    if tok:
        headers["Authorization"] = f"Bearer {tok}"
    status, h, body = _request(method, url, headers)
    if status == 401:
        challenge = {k.lower(): v for k, v in h.items()}.get("www-authenticate", "")
        headers["Authorization"] = f"Bearer {_token(registry, repo, challenge)}"
        status, h, body = _request(method, url, headers)
    return status, h, body


def tags(image: str) -> list[str]:
    """All tags of the image's repository."""
    registry, repo, _ = split_image(image)
    out: list[str] = []
    path = "tags/list?n=1000"
    for _ in range(200):
        status, h, body = call(registry, repo, "GET", path)
        if status != 200:
            raise RegistryError(f"{registry}/{repo}: tag list failed ({status})")
        out += json.loads(body).get("tags") or []
        link = {k.lower(): v for k, v in h.items()}.get("link", "")
        m = re.match(r"<([^>]+)>", link)
        if not m:
            break
        nxt = m.group(1)
        host = HOSTS.get(registry, registry)
        path = nxt if nxt.startswith("https://") else f"https://{host}{nxt}"
    return out


def exists(image: str) -> bool:
    registry, repo, tag = split_image(image)
    if registry == "docker.io":
        # Docker Hub's own API: no anonymous pull limit applies here.
        url = f"https://hub.docker.com/v2/repositories/{repo}/tags/{urllib.parse.quote(tag)}"
        status, _, _ = _request("GET", url, {})
        if status in (200, 404):
            return status == 200
        raise RegistryError(f"{image}: tag check failed ({status})")
    status, _, _ = call(registry, repo, "HEAD", f"manifests/{tag}", {"Accept": MANIFEST_TYPES})
    if status in (200, 404):
        return status == 200
    raise RegistryError(f"{image}: manifest check failed ({status})")
