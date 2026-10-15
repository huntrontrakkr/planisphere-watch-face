#!/usr/bin/env python3
"""Package, check and publish one version of Planisphere (after Morphogen 9's and Groundtrack's).

package  copies watchface/build/watchface.pbw to release-artifacts/, deflated,
         every member byte for byte, with SHA256SUMS and the release notes
check    verifies the packaged .pbw: identity, version, platforms, the store's
         and the watch's limits, and that the renderer's code is among its
         resources (tools/build_blob.py) and matches the app built with it
create   makes the store listing from the verified package (once; it is public
         from then on); prints the id for PLANISPHERE_STORE_APP_ID
publish  uploads it to the Pebble app store and verifies the public listing

No credentials are written to the repo. Publishing needs the listing id in
PLANISPHERE_STORE_APP_ID and either `pebble login` or
PEBBLE_FIREBASE_REFRESH_TOKEN. Run with the Pebble tool's Python.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import struct
import sys
import time
import zipfile

ROOT = Path(__file__).resolve().parents[1]
API = "https://appstore-api.repebble.com"
PROJECT = ROOT / "watchface"
TITLE = "Planisphere"
NAME = "planisphere.pbw"
LISTING = ROOT / "docs/STORE-LISTING.md"
GALLERY = ROOT / "docs/screenshots/store"
STORE_ENV = "PLANISPHERE_STORE_APP_ID"
SOURCE = "https://github.com/huntrontrakkr/planisphere-watch-face"
PLATFORMS = ["emery", "gabbro"]
# The store takes at most 256 KB of resources an app; an app's code and static
# data are capped at 64 KB (PebbleOS #1873): the renderer is a resource
# (tools/build_blob.py), and the app's own binary small.
MAX_RESOURCES = 256 * 1024
MAX_BINARY = 64 * 1024
CAPABILITIES = {"configurable", "location"}
CODE_MAGIC = b"PLNC"             # the renderer's code, as tools/build_blob.py packs it
UUID = json.loads((PROJECT / "package.json").read_text())["pebble"]["uuid"].lower()


def version_for(tag=None):
    version = json.loads((PROJECT / "package.json").read_text())["version"]
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        raise ValueError("watchface/package.json must name a version major.minor.patch.")
    if tag and tag != "v" + version:
        raise ValueError("Release tag must match the package version: v" + version)
    return version


def validate_pbw(path, version):
    with zipfile.ZipFile(path) as archive:
        if archive.testzip():
            raise ValueError("PBW archive is corrupt.")
        names = archive.namelist()
        for platform in PLATFORMS:
            for member in ["pebble-app.bin", "app_resources.pbpack", "manifest.json"]:
                if platform + "/" + member not in names:
                    raise ValueError("PBW is missing " + platform + "/" + member)
        for name in ["appinfo.json", "pebble-js-app.js"]:
            if name not in names:
                raise ValueError("PBW is missing " + name)
        info = json.loads(archive.read("appinfo.json"))
        if info.get("uuid", "").lower() != UUID or info.get("versionLabel") != version:
            raise ValueError("PBW UUID/version does not match this release.")
        if sorted(info.get("targetPlatforms", [])) != sorted(PLATFORMS) or not info.get("watchapp", {}).get("watchface"):
            raise ValueError("This release must be a watchface for " + " and ".join(PLATFORMS) + ".")
        missing = CAPABILITIES - set(info.get("capabilities", []))
        if missing:
            raise ValueError("PBW lacks capabilities: " + ", ".join(sorted(missing)))
        for platform in PLATFORMS:
            if archive.getinfo(platform + "/app_resources.pbpack").file_size > MAX_RESOURCES:
                raise ValueError("Resources exceed the store's 256 KB.")
            if archive.getinfo(platform + "/pebble-app.bin").file_size > MAX_BINARY:
                raise ValueError("The app binary exceeds 64 KB.")
            # the code blobs (the renderer's, the calendars'), whole, in this watch's resources
            pack = archive.read(platform + "/app_resources.pbpack")
            at, found = pack.find(CODE_MAGIC), 0
            while at >= 0:
                image, bss, nrel = struct.unpack_from("<III", pack, at + 4)
                if at + 20 + image + 2 * nrel > len(pack):
                    raise ValueError("A code blob in " + platform + "'s resources is cut short.")
                found += 1
                at = pack.find(CODE_MAGIC, at + 20 + image)
            if found < 2:
                raise ValueError("The renderer's and the calendars' code are not both among " + platform + "'s resources.")
        js = archive.read("pebble-js-app.js").decode("utf-8", "replace")
        if "PLAN_STATE" not in js:
            raise ValueError("The phone's bundle lacks the settings page.")
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def notes_for(version):
    return ROOT / "releases" / ("v" + version + ".md")


def package(version):
    out = ROOT / "release-artifacts"
    out.mkdir(exist_ok=True)
    source = PROJECT / "build/watchface.pbw"
    validate_pbw(source, version)
    # A PBW is a ZIP archive. Deflate changes only its transport size.
    with zipfile.ZipFile(source) as src, zipfile.ZipFile(out / NAME, "w", zipfile.ZIP_DEFLATED) as dest:
        for item in src.infolist():
            dest.writestr(item.filename, src.read(item.filename))
    digest = validate_pbw(out / NAME, version)
    with zipfile.ZipFile(source) as src, zipfile.ZipFile(out / NAME) as dest:
        assert src.namelist() == dest.namelist()
        assert all(src.read(name) == dest.read(name) for name in src.namelist())
    (out / "SHA256SUMS").write_text(digest + "  " + NAME + "\n")
    print(f"Packaged {TITLE} {version}: {(out / NAME).stat().st_size:,} bytes; all SDK contents preserved.")
    notes = notes_for(version)
    if notes.is_file():
        (out / "release-notes.md").write_bytes(notes.read_bytes())
    else:
        print(f"(No {notes.relative_to(ROOT)} yet: not releasable.)")


def description():
    copy = LISTING.read_text().split("## Description\n", 1)[1].split("\n## ", 1)[0].strip()
    if not copy or len(copy) > 1600:
        raise ValueError("The store description must contain 1-1600 characters.")
    if re.search(r"ressence|wittock|type\s*9|rocs|claude|anthropic", copy, re.I):
        raise ValueError("The store description names a third party's brand or model: remove it.")
    return copy


def gallery():
    shots = sorted(p for p in GALLERY.glob("*_*") if p.name.split("_", 1)[0] in PLATFORMS)
    return [str(p) for p in shots if p.suffix == ".gif"], [str(p) for p in shots if p.suffix == ".png"]


def check(version, tag=None):
    digest = validate_pbw(ROOT / "release-artifacts" / NAME, version)
    description()
    print("Verified", TITLE, version, digest)
    if tag and not notes_for(version).is_file():
        raise ValueError("Add release notes at " + str(notes_for(version).relative_to(ROOT)))


def access_token():
    from pebble_tool.account import get_account
    from pebble_tool.firebase_account import DEFAULT_FIREBASE_API_KEY
    import requests
    refresh = os.environ.get("PEBBLE_FIREBASE_REFRESH_TOKEN")
    if refresh:
        r = requests.post("https://securetoken.googleapis.com/v1/token",
                          params={"key": DEFAULT_FIREBASE_API_KEY},
                          data={"grant_type": "refresh_token", "refresh_token": refresh}, timeout=30)
        if not r.ok:
            raise RuntimeError("Pebble release sign-in could not be refreshed. Reconnect the publishing secret.")
        token = r.json()["id_token"]
    else:
        if os.environ.get("GITHUB_ACTIONS"):
            raise RuntimeError("Set the repository secret PEBBLE_FIREBASE_REFRESH_TOKEN before publishing.")
        account = get_account(auth_provider="firebase")
        if not account.is_logged_in:
            raise RuntimeError("Run pebble login before publishing.")
        token = account.get_access_token()
    if os.environ.get("GITHUB_ACTIONS"):
        print("::add-mask::" + token)
    return token


def public_app(store_id):
    import requests
    # The public endpoint caches for five minutes; a unique query reads the release just uploaded.
    response = requests.get(API + "/api/v1/apps/id/" + store_id, params={"_release_check": str(time.time_ns())}, timeout=30)
    response.raise_for_status()
    return response.json()["data"][0]


def create(version):
    """Creates the store listing from the verified package, with the listing's
    copy, the release notes and the gallery, through the Pebble tool's own
    publishing code. A listing is public as soon as it exists."""
    import requests
    from pebble_tool.commands.publish import PublishCommand
    pbw = ROOT / "release-artifacts" / NAME
    validate_pbw(pbw, version)
    token = access_token()
    r = requests.get(API + "/api/v1/developer/me", headers={"Authorization": "Bearer " + token}, timeout=30)
    r.raise_for_status()
    existing = r.json().get("app_lookup", {}).get("by_app_uuid", {}).get(UUID)
    if existing:
        print(f"{TITLE} already has a listing: {existing}")
        return existing
    gifs, stills = gallery()
    if not gifs and not stills:
        raise RuntimeError("No gallery in docs/screenshots/store (tools/build-host.sh && cd proto && "
                           "uv run python ../tools/store_gallery.py).")
    details = {"name": TITLE, "version": version, "description": description(), "source": SOURCE, "category": "faces",
               "icon_small_path": "", "icon_large_path": ""}
    metadata = {"app_uuid": UUID, "version": version, "platforms": PLATFORMS, "app_name": TITLE, "app_type": "watchface"}
    payload = PublishCommand._create_app(API, token, str(pbw), metadata, details, notes_for(version).read_text().strip(),
                                         True, gifs, stills)
    app_id = PublishCommand._extract_app_id(payload)
    if not app_id:
        r = requests.get(API + "/api/v1/developer/me", headers={"Authorization": "Bearer " + token}, timeout=30)
        r.raise_for_status()
        app_id = r.json().get("app_lookup", {}).get("by_app_uuid", {}).get(UUID)
    if not app_id:
        raise RuntimeError("The listing was created but its id was not returned: see the developer dashboard.")
    for item in (payload.get("screenshotResults") or {}).get("failed") or []:
        print(f"  screenshot not taken: {item.get('filename')}: {item.get('error')}")
    print(f"Created {TITLE}'s listing: {app_id} (https://apps.repebble.com/{app_id}); set {STORE_ENV} to it.")
    return app_id


def publish(version):
    store_id = os.environ.get(STORE_ENV, "")
    if not store_id:
        raise RuntimeError(f"No store listing id: set {STORE_ENV}.")
    import requests
    from pebble_tool.commands.publish import PublishCommand
    check(version, "v" + version)
    pbw = ROOT / "release-artifacts" / NAME
    digest = validate_pbw(pbw, version)
    copy = description()
    notes = notes_for(version).read_text().strip()
    token = access_token()
    headers = {"Authorization": "Bearer " + token}
    r = requests.get(API + "/api/v1/developer/me", headers=headers, timeout=30)
    r.raise_for_status()
    me = r.json()
    if me.get("app_lookup", {}).get("by_app_uuid", {}).get(UUID) != store_id:
        raise RuntimeError("This account does not own the expected listing. No changes made.")
    if pbw.stat().st_size > me.get("upload_constraints", {}).get("max_pbw_bytes", 4400000):
        raise ValueError("PBW exceeds the store upload limit.")
    app = public_app(store_id)
    current = (app.get("latest_release") or {}).get("version", "0.0.0")
    parse = lambda v: tuple(int(n) for n in v.split("."))
    if parse(current) > parse(version):
        raise ValueError("Refusing to replace a newer published version.")
    if current != version:
        gifs, stills = gallery()
        PublishCommand._upload_release(API, store_id, token, str(pbw), version, notes, True, gifs, stills,
                                       replace_screenshots=bool(gifs or stills))
    # A rerun verifies an existing version instead of creating it again.
    app = public_app(store_id)
    if app["latest_release"]["version"] != version:
        raise RuntimeError("The public store has not confirmed the new version.")
    download = requests.get(app["latest_release"]["pbw_file"], timeout=90)
    download.raise_for_status()
    if hashlib.sha256(download.content).hexdigest() != digest:
        raise RuntimeError("Published version has a different package. Use a new version; do not overwrite it.")
    with requests.Session() as session:
        response = session.post(API + "/api/auth/firebase/session", json={"idToken": token}, timeout=30)
        response.raise_for_status()
        values = {"title": TITLE, "description": copy, "source": SOURCE, "visibility": "listed"}
        response = session.patch(API + "/api/dashboard/apps/" + store_id,
                                 files={key: (None, value) for key, value in values.items()}, timeout=45)
        response.raise_for_status()
    app = public_app(store_id)
    if app.get("description") != copy or not app.get("visible"):
        raise RuntimeError("Release uploaded, but listing verification failed.")
    store = "https://apps.repebble.com/" + store_id
    print(f"Verified public release of {TITLE} {version}: {store}")
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a") as f:
            f.write(f"Published **{TITLE} {version}** to [Pebble]({store}).\n\nPublic download SHA-256: `{digest}`.\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=["package", "check", "create", "publish"])
    parser.add_argument("--tag")
    args = parser.parse_args()
    version = version_for(args.tag)
    if args.command == "package":
        package(version)
    elif args.command == "check":
        check(version, args.tag)
    elif args.command == "create":
        create(version)
    else:
        publish(version)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("Release failed:", str(error), file=sys.stderr)
        sys.exit(1)
