# Planisphere

A watch face prototype for the Pebble Round 2 and Time 2: the sky as it is right now, on a planisphere.

## The readable version

The time is large above the window, with the date and the Sun's next rising or setting. The sky names what is bright in it: the Moon, the planets, and the brightest stars in view.

![A day on the Round 2, eight minutes a frame](docs/readable-day.gif)

![9:30 pm in New York on 14 October 2026: Capella, Vega and Saturn named](docs/readable-evening.png)

![The readable version at 9:30 pm, noon, dusk and before dawn, on the Round 2 and the Time 2](docs/readable-moods.png)

## Compass, on a flick

The magnetometer costs battery while it runs, so it only runs when you ask. Flick your wrist and the compass turns on for half a minute. The face becomes a window onto the sky where the watch points: the horizon along the bottom, the compass points on it, and names on what is bright. Then the compass switches off and the planisphere comes back; a second flick ends it sooner.

![Turning round under the evening sky, 4 degrees a frame](docs/compass-turn.gif)

![Pointing northeast (Capella rising), southeast (Saturn), southwest (Altair and the Milky Way) and northwest (Vega)](docs/compass-views.png)

## The instrument version

The first take, before readability: no clock, only the planisphere. The Sun's golden pointer on the 24-hour ring is the only way to read the time.

![A day on the Round 2, eight minutes a frame: noon, sunset, the night turning, dawn](docs/a-day.gif)

![The evening sky over New York at 9:30 pm on 14 October 2026](docs/round2-evening.png)

## What you are looking at

- **The star disc** is the whole sky as a planisphere draws it: the celestial pole at the centre, the stars round it, turning once a sidereal day as the real sky does.
- **The window** is your horizon. The black jacket hides everything below it, so the oval shows exactly the sky above you now (here, New York; east is on the left, as when you look up).
- **The Sun is the hour hand.** It rides the ecliptic through the sky, and the golden pointer on the jacket's 24-hour ring reads it. The ring is set to civil time, so it sits a little turned: in New York in October the Sun crosses the south at 12:42.
- **The sky's colour is the real sky's**, from the Sun's height and direction: flat night blue with the Milky Way, the blue hour with a warm glow on the Sun's side, day blue with the Sun in it. The colours come in clean bands along the sky's own contours, each edge softened by a fine dither.
- About 1,000 stars, down to magnitude 4.6, in their own colours. The figures are drawn only between the brighter stars, and stop just short of them. The Moon shows its true phase, lit from the Sun's side, and the five bright planets are there too.

![Evening, dusk, dawn and noon on the Round 2, and the evening on the Time 2](docs/moods.png)

![Sunset, every fourteen minutes from 6:10 pm, then the night, then dawn](docs/sunset.png)

## How it is drawn

Every image above is drawn at the watch's own size (260×260 round, 200×228) in its 64 colours (two bits a channel), so what you see is what the watch can show. The stars are stamped by brightness, the lines and edges are kept to whole palette colours, and the only dithered texture at night is the Milky Way, as blue-noise grain.

- `proto/astro.py`: sidereal time, the Sun, the Moon (with its main perturbations) and the planets, from Paul Schlyter's orbital elements. That is well under a pixel at this scale.
- `proto/render2.py`: the face. The projection is equidistant from the pole, the window is the horizon for your latitude, and the sky model works out its colour bands.
- `proto/look.py`: the compass view.
- `proto/film.py`, `proto/film_readable.py`: the day films and the stills (`readable=True` in `render2.render` gives the readable version).

```
uv run python proto/film.py      # writes out/
```

Next: the same drawing in C for the watch, with the stars and figures as a small table.

## Credits

Star positions and colours, constellation lines and the Milky Way's outline come from [d3-celestial](https://github.com/ofrohn/d3-celestial), © 2015 Olaf Frohn, BSD 3-Clause (`data/`). The numerals use the monoline stroke font made for Morphogen 9.
