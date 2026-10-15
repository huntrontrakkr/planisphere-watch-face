# Releasing Planisphere

Nothing is published yet. The store listing is made once, by `tools/release.py create`, and is public from that
moment, so it is made only with the owner's go-ahead.

## The first release

1. Try the build on a real watch first (the emulator has run it, but the renderer is loaded from the app's
   resources as code, which only a real Time 2 or Round 2 fully proves): install `watchface/build/watchface.pbw`
   from the phone.
2. Add the release notes at `releases/v0.1.0.md` (a draft is below).
3. With the Pebble tool's Python, signed in to the developer account (`pebble login`):

       cd watchface && pebble build && cd ..
       python tools/release.py package
       python tools/release.py check --tag v0.1.0
       python tools/release.py create

   `create` prints the listing's id. Record it here and in [STORE-LISTING.md](STORE-LISTING.md).
4. For CI to publish later versions, set the repository variable `PLANISPHERE_STORE_APP_ID` to that id and the
   secret `PEBBLE_FIREBASE_REFRESH_TOKEN` (the same Pebble account's sign-in, as for Morphogen 9 and Groundtrack).

Draft notes for v0.1.0:

> The first release: the sky over where you are on ten plates after the old star charts, with the weather from
> Open-Meteo, the sky's news on the almanac's line, eclipses as they happen, and the labours of the months as an
> option. For Pebble Time 2 and Pebble Round 2.

## Later versions

1. Bump `version` in `watchface/package.json` (`pebble clean` before building so the new version is compiled in).
2. Add release notes at `releases/vX.Y.Z.md`.
3. Optionally refresh the gallery: `tools/build-host.sh && cd proto && uv run python ../tools/store_gallery.py`.
4. Push to main. `.github/workflows/release.yml` builds and checks the face, tags the commit, publishes the package
   to the Pebble store (verifying the public download byte for byte), and attaches it to a GitHub release.

By hand:

    cd watchface && pebble build && cd ..
    python tools/release.py package
    python tools/release.py check --tag vX.Y.Z
    PLANISPHERE_STORE_APP_ID=<id> python tools/release.py publish --tag vX.Y.Z

## What the checks guard

`tools/release.py check` verifies the package's identity, version and platforms, the store's 256 KB of resources and
the 64 KB cap on the app's binary, that the renderer's code (`tools/build_blob.py`) is whole in each watch's
resources, and that the store's copy is 1 to 1,600 characters with no third-party brand names. CI also runs
`tools/stack_depth.py --budget 1000` (the renderer's deepest call chain, from the compiler: the watch's stack is
2 KB) and `tools/check_memory.py` (every latitude's frame against the heap left after loading).

Before a release, also run the checks CI does not:

    tools/build-host.sh && (cd proto && uv run python ../tools/parity.py)     # the C against the prototype
    LD_LIBRARY_PATH=~/.local/lib/chromedeps node tools/check-page.mjs          # the settings page, in Chromium
    <pebble-tool-python> tools/emulator.py emery shots --gdb g_heap_free g_heap_low
