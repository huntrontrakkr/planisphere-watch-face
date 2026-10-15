# Releasing Planisphere

Planisphere is on the Pebble app store:
[apps.repebble.com/1f998f38a4cb48abb78f8e89](https://apps.repebble.com/1f998f38a4cb48abb78f8e89) (developer
Segfaultgolf). Version 0.1.0 was published 2026-10-15: the repository made public, the listing made once by
`tools/release.py create` from CI's own package, then CI's publish job tagged v0.1.0, checked the store's public
download byte for byte against that package and attached it to the GitHub release.

CI has what it needs to publish: the repository variable `PLANISPHERE_STORE_APP_ID` (the listing's id) and the secret
`PEBBLE_FIREBASE_REFRESH_TOKEN` (the Pebble account's sign-in, as for Morphogen 9 and Groundtrack; from the Pebble
tool's `firebase_oauth_storage.json` after `pebble login`, piped to `gh secret set`, never printed). If the publish
job reports that the sign-in could not be refreshed, `pebble login` again and set the secret again.

## Later versions

1. Bump `version` in `watchface/package.json` (`pebble clean` before building so the new version is compiled in).
2. Add release notes at `releases/vX.Y.Z.md`.
3. Optionally refresh the gallery: `tools/build-host.sh && cd proto && uv run python ../tools/store_gallery.py`.
4. Push to main. `.github/workflows/release.yml` builds and checks the face (and the prototype job its parity), tags
   the commit, publishes the package to the Pebble store (verifying the public download byte for byte), and attaches
   it to a GitHub release. Nothing else is needed: a version that has release notes and no tag yet is released by
   the push.

By hand:

    cd watchface && pebble build && cd ..
    python tools/release.py package
    python tools/release.py check --tag vX.Y.Z
    PLANISPHERE_STORE_APP_ID=<id> python tools/release.py publish --tag vX.Y.Z

## What the checks guard

`tools/release.py check` verifies the package's identity, version and platforms, the store's 256 KB of resources and
the 64 KB cap on the app's binary, that the renderer's code (`tools/build_blob.py`) is whole in each watch's
resources, and that the store's copy is 1 to 1,600 characters with no third-party brand names. CI also runs
`tools/stack_depth.py --budget 1000` (each code blob's deepest call chain, from the compiler: the watch's stack is
2 KB), `tools/check_memory.py` (every latitude's frame, the day's feast lookup and a fireworks display against the
heap left after loading), `tools/check-page.mjs` (the phone's side and the settings page in Chromium, its preview
drawing and playing a fireworks display) and, in its prototype job, `tools/check_feasts.py` (the calendars, C against
the prototype day by day) and `tools/parity.py` (the faces against the prototype, against the accepted counts in
`tools/parity-baseline.json`). A release is published only when all of them pass.

By hand, after large changes: the heap in the emulator, to measure `tools/check_memory.py`'s baseline again, and for
changes that should not move a pixel, `tools/same_frames.py <commit>`:

    <pebble-tool-python> tools/emulator.py emery shots --set LABOURS=1 --gdb g_heap_free g_heap_low
    tools/build-host.sh && python3 tools/same_frames.py <commit>
