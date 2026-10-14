# Planisphere

A watch face prototype for the Pebble Round 2 and Time 2: the sky as it is right now, on a planisphere.

## Plates

Like Groundtrack's plates, each plate follows a real tradition of sky charts, set in the type of its time. Every plate sets the time in hours and minutes the way almanacs and astronomers write it, **9ʰ 30ᵐ**, large in the card above the window (or **21ʰ 30ᵐ** on the 24-hour clock, below). The small type is pixel type, every letter in whole pixels: Not Jam Old Style (CC0), a pixel serif after the old Garalde faces, with star names leaning in an oblique cut from it a pixel at a time. Under it are the date in italic and the Sun's next rising or setting in small capitals. The sky carries names the way the old atlases letter them: constellations in spaced capitals, stars in italic, planets in small capitals.

![A day on the Time 2, the paper planisphere plate, eight minutes a frame](docs/plate-planisphere-day-time2.gif)

![The same day on the Round 2](docs/plate-planisphere-day.gif)

![Every plate at 9:30 pm and at noon on the Round 2, and at 9:30 pm on the Time 2](docs/plates.png)

| Plate | After | Type |
| --- | --- | --- |
| **Planisphere** | The paper planispheres of the early 1900s: a cream card printed in black and red, a deep blue star disc behind its window, MIDNIGHT and NOON lettered round the ring | Old Standard, a revival of the period's scientific type |
| **Burritt** | Elijah Burritt's *Geography of the Heavens* (1835): white stars and figures on a blue ground | Playfair Display, after copperplate lettering |
| **Flamsteed** | Flamsteed's *Atlas Coelestis* (London, 1729): engraved rayed stars and figures, ink on paper, the Moon hatched | Libre Caslon: Caslon cut his type in London in the same decade |
| **Observatory** | Red light, for eyes adapted to the dark | Old Standard |
| **Night** | The first take: a black card, white type | Old Standard |

The planisphere, observatory and night plates show the live sky in their window: night blue, the blue hour with its warm glow, day blue with the Sun in it. Burritt and Flamsteed are printed atlases, so their windows keep the stars by day as a chart would, with the Sun drawn among them.

![The paper planisphere at 9:30 pm](docs/plate-planisphere.png)

![Flamsteed's plate at 9:30 pm](docs/plate-flamsteed.png)

## On the Time 2, and the Round 2

The Time 2 comes first. Its ring is a cushion: arcs along the top and bottom, the sides gently bowed, the corners rounded. It fills the screen, so the window stays as large as the card allows, and MIDNIGHT and NOON still curve along it as they do round a planisphere's ring. The band is wider in the corners, its inner edge rounder than its outer, which leaves room for the hours that fall there. Each hour's tick stands where that hour's ray from the pole meets the ring, so the ticks fall unevenly round the cushion, as hour lines do on a sundial plate. Each numeral sits on its own ray, wherever it stands clearest of the rules and ticks. The four corners outside the ring each carry a small compass star, the way a printer finishes a border. On the Round 2 the ring is a circle.

![Every plate on the Time 2 at 9:30 pm, then the paper planisphere at dusk and at noon](docs/time2-plates.png)

By day the Sun in the window has a face and sixteen rays, straight and flaming in turn, after the Sun of May. It stands in its own light, as the first takes drew it: a glow stippled thinner outward, the sky brightest round the Sun, white by day and warm when the Sun is low. The glow shows between the rays and past them, and draws the eye to the Sun, the hour hand. A small rayed Sun points at the hour on the ring and passes behind the lettering, which stays whole.

### The 12-hour or the 24-hour clock

The ring counts the hours as old planispheres do, twelve and twelve: III, VI and IX in the morning and again in the evening, with MIDNIGHT and NOON between. The time reads 9ʰ 30ᵐ. The 24-hour clock is an option. With it the ring's figures run on through the day (3, 6, 9, 15, 18, 21), and the time reads 21ʰ 30ᵐ, as astronomers write it. On the watch the option starts from the watch's own 12 or 24-hour setting.

![9:30 pm on the 12-hour and the 24-hour clock, on the Time 2 and the Round 2](docs/clock-12-24.png)

## The almanac

The face carries what an almanac page would, each thing in its old form.

- **Night on the ring.** Where the Sun's pointer will stand while the Sun is down, the band is hatched like an engraving. The hatching is sparse in civil twilight, closer through nautical and astronomical twilight, and closest in full night. You see the day's length at a glance, and the pointer walks into the hatching at sunset.
- **The day's planet.** Before the date stands the sign of the planet that rules the day, as almanacs mark their days: ☽ Monday, ♂ Tuesday, ☿ Wednesday, ♃ Thursday, ♀ Friday, ♄ Saturday, ☉ Sunday.
- **The zenith and the meridian.** A small cross marks the point straight overhead, turned on its side so it is not taken for a star. At night a dotted line runs north to south through the pole and the zenith, as on an astrolabe's plate.
- **The zodiac.** At night the signs are set along the ecliptic, each at its sign's middle, wherever no name or bright star is drawn.
- **The sky's news.** On a day with something to see, the line under the date says so in place of the sunrise or sunset:
  - an eclipse of the Sun or the Moon, if it can be seen from here;
  - two planets meeting;
  - a meteor shower's peak;
  - the Moon by a planet.

  The eclipses and the planets come from the same ephemeris as the rest of the face; the showers from where the Earth is in its orbit. During an eclipse the Moon turns copper in the Earth's shadow, or the Moon's dark disc crosses the Sun's face. At a shower's peak its radiant is drawn in the sky, where the meteors seem to come from.
- **Jupiter's moons.** Beside Jupiter its four great moons stand where they are tonight (Meeus's theory), magnified along its equator. At the chart's scale they would all fall inside one pixel.
- **The place.** The face says whose sky it is, as a map's border does. The city and its country stand either side of MIDNIGHT, and the latitude and longitude either side of NOON, in small capitals that follow the ring. A city too long for its room has its leading words cut to their initials (N. YORK), or becomes all initials (N.Y.). On the watch the phone would give the place.

### Eclipses

An eclipse gets the sky it really has.

As the Moon covers the Sun, the Sun's glow thins. Past about four fifths covered, the daylight drains toward twilight. In totality the sky is deep blue with a sunset all round the horizon. The bright planets and stars come out. The Sun is a black disc in a pearly corona, its streamers reaching out, with small red prominences at the Moon's edge. Just before and after totality the corona is fainter and the diamond ring flashes at the Moon's edge, the last point of sunlight. An annular eclipse leaves a ring of fire. The line under the date reads TOTALITY.

A bright Moon at night pales the sky round it and hides the faint stars near it. In the Earth's shadow its light goes out and the stars come back round it. The Moon turns red: copper at the shadow's edge, deepest toward its middle.

The eclipses are worked out for wherever the watch is, from Meeus's theories of the Sun and the Moon (`proto/lunar.py`, checked against his worked examples to every digit). They come out within a minute of the real ones:
- Dallas on 8 April 2024: totality from 18:41 to 18:44 UTC (in fact 18:40:43 to 18:44:35).
- New York the same day: partial.
- Burgos on 12 August 2026: total at sunset.
- New York on 14 March 2025: the Moon totally eclipsed from 06:27 to 07:32 UTC (06:26 to 07:31).

![Dallas, 8 April 2024: the Sun nearly covered, the sky darkening, the diamond ring, totality; Burgos at sunset, 12 August 2026; the blood Moon over New York, 14 March 2025](docs/eclipses.png)

And the filigree, all drawn by hand:

- a village on the southern horizon (hills, trees, a house, the church, a windmill), bent along the window's lower edge;
- the engraver's glory of fine rays round the Sun on the printed charts;
- a beaded rule inside the ring's outer rule, as on a clock's chapter ring;
- studs on the inner rule at the numbered hours;
- a star at the south point, clasping the window's two rules, to go with the fleur-de-lis at the north and the lozenges east and west;
- a leaf turning into each of the Time 2's corners;
- a face on the full Moon, as the almanacs give it.

![At the Orionids' peak, at an eclipse of the Moon, at an eclipse of the Sun, and as Venus meets Jupiter; below, Jupiter's moons, the village by day, and the glory on Flamsteed's plate](docs/almanac.png)

## Experimental: the compass, on a flick

Off unless you turn it on, as an experimental setting. The magnetometer costs battery while it runs, so it only runs when you ask. Flick your wrist and the compass turns on for half a minute. The face becomes a window onto the sky where the watch points: the horizon along the bottom, the compass points on it, and names on what is bright. Then the compass switches off and the planisphere comes back; a second flick ends it sooner.

![Turning round under the evening sky, 4 degrees a frame](docs/compass-turn.gif)

![Pointing northeast (Capella rising), southeast (Saturn), southwest (Altair and the Milky Way) and northwest (Vega)](docs/compass-views.png)

## Earlier takes

### A round ring on the Time 2

Before the cushion, the Time 2 had the Round 2's circular ring, with a woodcut texture in the corners (rays, stars or hatching) and nothing there to read. The circle made the window smaller.

![The round ring on the Time 2 with rays, stars, hatching and plain corners; the Sun at noon](docs/time2-corners.png)

### The readable version

The time is large above the window, with the date and the Sun's next rising or setting. The sky names what is bright in it: the Moon, the planets, and the brightest stars in view.

![A day on the Round 2, eight minutes a frame](docs/readable-day.gif)

![9:30 pm in New York on 14 October 2026: Capella, Vega and Saturn named](docs/readable-evening.png)

![The readable version at 9:30 pm, noon, dusk and before dawn, on the Round 2 and the Time 2](docs/readable-moods.png)

### The instrument version

The first take, before readability: no clock, only the planisphere. The Sun's golden pointer on the 24-hour ring is the only way to read the time.

![A day on the Round 2, eight minutes a frame: noon, sunset, the night turning, dawn](docs/a-day.gif)

![The evening sky over New York at 9:30 pm on 14 October 2026](docs/round2-evening.png)

## How the planisphere works

- **The star disc** is the whole sky as a planisphere draws it: the celestial pole at the centre, the stars round it, turning once a sidereal day as the real sky does.
- **The window** is your horizon. The black jacket hides everything below it, so the oval shows exactly the sky above you now (here, New York; east is on the left, as when you look up).
- **The Sun is the hour hand.** It rides the ecliptic through the sky, and the small rayed Sun on the ring follows it. The ring keeps the Sun's own time, as a sundial does: NOON under the window's south point and MIDNIGHT above the pole, fixed, so the pointer reaches NOON as the Sun crosses the south (12:42 by the clock in New York in October). The large numerals keep the clock's time.
- **The sky's colour is the real sky's**, from the Sun's height and direction: flat night blue with the Milky Way, the blue hour with a warm glow on the Sun's side, day blue with the Sun in it. The colours come in clean bands along the sky's own contours, each edge softened by a fine dither.
- About 1,000 stars, down to magnitude 4.6, in their own colours. The figures are drawn only between the brighter stars, and stop just short of them. The Moon shows its true phase, lit from the Sun's side, and the five bright planets are there too.

![Evening, dusk, dawn and noon on the Round 2, and the evening on the Time 2](docs/moods.png)

![Sunset, every fourteen minutes from 6:10 pm, then the night, then dawn](docs/sunset.png)

## How it is drawn

Every image above is drawn at the watch's own size (260×260 round, 200×228) in its 64 colours (two bits a channel), so what you see is what the watch can show. The lines and edges are kept to whole palette colours, and the only dithered texture at night is the Milky Way, as blue-noise grain.

The pieces are drawn by hand, pixel by pixel, not generated from shapes. Each is kept as text art in `proto/sprites.py`:

- **The Sun** has a face and sixteen rays. One eighth of the rays is drawn and turned round the circle, so they are exactly symmetric.
- **The Moon** goes through its phases across the month. The terminator curves as on the real Moon, so a crescent thins to points at its horns. The dark part carries the engraver's hatching.
- **The stars** are drawn by brightness: eight points, four, a cross, a point.
- **The planets** each have a little picture: Saturn's ring, Jupiter's bands.
- **The ornaments** are the fleur-de-lis standing on the window at the north, the lozenges, the south star, the studs, the corner leaves, the engraved glory and the village on the horizon.
- **The almanac's signs** are the zodiac and the planets that rule the days.
- **The ring's hours** are hand-drawn too: roman numerals on the 12-hour clock, figures on the 24-hour clock.
- **MIDNIGHT and NOON** are roman capitals with thick stems, thin hairlines and serifs. Each letter is drawn turned to its own place on each screen's ring, its stems stepping and its bars sloping as the curve turns.

![The hand-drawn pieces at six times and at their own size](docs/pieces.png)

- `proto/astro.py`: sidereal time and the planets, from Paul Schlyter's orbital elements (well under a pixel at this scale); `proto/lunar.py`: the Sun and the Moon from Meeus, closely enough for eclipses.
- `proto/plates.py`: the plates (the current design): the projection, the window as the horizon for your latitude, the sky's colour bands, and the ring.
- `proto/frame.py`: the Time 2's cushion, with exact distances to its edge, so the rules, ticks and lettering run along true parallels of it.
- `proto/events.py`: Jupiter's moons, eclipses, planets meeting and the meteor showers, for the almanac.
- `proto/sprites.py`: the hand-drawn pieces; `proto/letterer.py` and `proto/coverage.py`: the drafting table the curved words were drawn from; `proto/closeup.py`: close-ups of the faces, pixel by pixel, for checking.
- `proto/typeset.py`: the large type, the astronomers' 21ʰ 30ᵐ; `proto/pixeltext.py`: the pixel type.
- `proto/look.py`: the compass view.
- `proto/film_plates.py`: the plates' films and stills; `proto/film.py`, `proto/film_readable.py`: the earlier takes' (`proto/render2.py` draws those).

```
uv run python proto/film_plates.py      # writes docs/
```

Next: the same drawing in C for the watch, with the pieces and the stars as small tables.

## Credits

Star positions and colours, constellation lines and the Milky Way's outline come from [d3-celestial](https://github.com/ofrohn/d3-celestial), © 2015 Olaf Frohn, BSD 3-Clause (`data/`). The numerals use the monoline stroke font made for Morphogen 9.

Pixel type: Not Jam Old Style 11 by Not Jam (CC0, `fonts/pixel/`). Type: Old Standard TT (Alexey Kryukov), Libre Caslon Text, Playfair Display, with IM Fell, EB Garamond and Cinzel tried in [the type specimen](docs/type-specimen.png). All are SIL Open Font License 1.1, and the licences are in `fonts/`.
