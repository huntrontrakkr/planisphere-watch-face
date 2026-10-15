# Planisphere

A watch face for the Pebble Time 2 and Round 2: the sky as it is right now, on a planisphere. The Python prototype
(`proto/`) is where it is designed; the watch runs the same drawing in C (`watchface/`), and its settings page shows
the face live, the same C built to WebAssembly. See [On the watch](#on-the-watch).

## Plates

Like Groundtrack's plates, each plate follows a real tradition of sky charts, set in the type of its time. Every plate sets the time in hours and minutes the way almanacs and astronomers write it, **9ʰ 30ᵐ**, large in the card above the window (or **21ʰ 30ᵐ** on the 24-hour clock, below). Its figures are drawn by hand, pixel by pixel, after each plate's type and for each watch. The small type is pixel type, every letter in whole pixels: Not Jam Old Style (CC0), a pixel serif after the old Garalde faces, with star names leaning in an oblique cut from it a pixel at a time. Under it are the date in italic and the Sun's next rising or setting in small capitals, with the temperature after it when the weather is known. The sky carries names the way the old atlases letter them: constellations in spaced capitals, stars in italic, planets in small capitals.

![A day on the Time 2, the paper planisphere plate, eight minutes a frame](docs/plate-planisphere-day-time2.gif)

![The same day on the Round 2](docs/plate-planisphere-day.gif)

![Every plate at 9:30 pm and at noon on the Round 2, and at 9:30 pm on the Time 2](docs/plates.png)

| Plate | After | Type |
| --- | --- | --- |
| **Planisphere** | The paper planispheres of the early 1900s: a cream card printed in black and red, a deep blue star disc behind its window, MIDNIGHT and NOON lettered round the ring | Old Standard, a revival of the period's scientific type |
| **Burritt** | Elijah Burritt's *Geography of the Heavens* (1835): white stars and figures on a blue ground | Playfair Display, after copperplate lettering |
| **Flamsteed** | Flamsteed's *Atlas Coelestis* (London, 1729): copper engraving, black ink on white paper, rayed stars, the figures and the hatching in grey, the Moon hatched | Libre Caslon: Caslon cut his type in London in the same decade |
| **Observatory** | Red light, for eyes adapted to the dark | Old Standard |
| **Night** | The first take: a black card, white type | Old Standard |
| **Astrolabe** | A brass astrolabe, after the Sloane astrolabe (c. 1300) and Arsenius's gilt instruments: the rete's flame pointers marking the bright stars over the plate's engraved circles (the equator, the tropics, the almucantars), the ecliptic a solid ring, the throne and ring at the north, Gothic figures on the ring, beads at the unequal hours | Libre Caslon's old-style figures |
| **Hours** | A Book of Hours, after the *Très Riches Heures* (c. 1412–1416): gold stars in an ultramarine sky on vellum, the ring painted ultramarine with its hours and lettering in gold as the calendar lunettes' bands are, vermilion, the hours in the small roman of the manuscripts (iij, vj, ix), ivy in the corners | Libre Caslon's old-style figures |
| **Orloj** | Prague's astronomical clock (1410): gold on black, the sky and the ring in the clock's three flat zones, blue for the day, red-brown for the twilight, black for the night | Old Standard |
| **Cyanotype** | A cyanotype, Herschel's blueprint (1842) as Anna Atkins used it for her *British Algae* (1843): white on cobalt, a seaweed frond in each corner | Old Standard |
| **Apian** | Apian's *Astronomicum Caesareum* (Ingolstadt, 1540), a woodcut coloured by hand on old rag paper, buff and lightly foxed: heavy black line, a yellow zodiac band across a light blue sky, the stars cut in outline and coloured, a yellow-washed ring, the dragon at the Moon's nodes in eclipse seasons, a silk thread and a seed pearl for the Sun's index | Libre Caslon's old-style figures |

The planisphere, observatory and night plates show the live sky in their window: night blue, the blue hour with its warm glow, day blue with the Sun in it. Burritt, Flamsteed, the Hours, the Cyanotype and Apian's woodcut are printed or painted, so their windows keep the stars by day as a chart would, with the Sun drawn among them. The Astrolabe keeps its rete up by day as the instrument does. The Orloj's window takes the clock's zones: blue while the Sun is up, red-brown through the twilight, black at night.

Each new plate brings its own pieces:
- **The Astrolabe** has its throne and ring at the north in place of the fleur-de-lis, and flame pointers for the stars, after the Gothic retes. Its ring has Gothic figures (the 3 a yogh, the 6 a sigma, the 9 tailed, after Hill's tables of 1915) and beads at the unequal hours: the day from sunrise to sunset in twelve and the night in twelve, crowding and spreading with the seasons, as the plates engrave them.
- **The Hours** has its hours in small roman, the last i written j, and gold ivy in the corners.
- **The Orloj** fills its ring with the clock's zones in place of the engraver's hatching, so the gilded Sun travels through blue, brown and black.
- **The Cyanotype** has white seaweed fronds in its corners.
- **The cards differ as their originals do.** The Planisphere is the cream card of the paper planispheres. Flamsteed's is the white paper of a copper engraving, in black ink only. The Hours' vellum carries an ultramarine ring lettered in gold. Apian's is old rag paper, lightly foxed with buff specks.
- **Apian's woodcut** is coloured as his volvelles were: the zodiac a band six degrees either side of the ecliptic, washed yellow and ruled black, the ecliptic red through it, and the Milky Way a flat wash with no grain. The bright stars are cut in outline and coloured; the faint ones are black dots. The ring is washed yellow, with the night hatched over it in a quiet tone so the lettering stays clear. In an eclipse season, when the Sun is within eighteen degrees of a node of the Moon's path, the dragon's head ☊ and tail ☋ stand at the nodes, where the eclipses happen, as on Apian's dragon volvelle; the nodes come from Meeus. The Sun's hour is marked not by the gilded Sun but by a silk thread across the ring with a seed pearl on it, as Apian's volvelles are read.

![The paper planisphere at 9:30 pm](docs/plate-planisphere.png)

![Flamsteed's plate at 9:30 pm](docs/plate-flamsteed.png)

## On the Time 2, and the Round 2

The Time 2 comes first. Its ring is a cushion: arcs along the top and bottom, the sides gently bowed, the corners rounded. It fills the screen, so the window stays as large as the card allows, and MIDNIGHT and NOON still curve along it as they do round a planisphere's ring. The band is wider in the corners, its inner edge rounder than its outer, which leaves room for the hours that fall there. Each hour's tick stands where that hour's ray from the pole meets the ring, so the ticks fall unevenly round the cushion, as hour lines do on a sundial plate. Each numeral sits on its own ray, wherever it stands clearest of the rules and ticks. The four corners outside the ring each carry a sprig turning into the corner, in the season's dress: two blossoms in spring, a leaf in summer, the leaf turned gold in autumn, a bare twig in winter. On the Round 2 the ring is a circle.

![Every plate on the Time 2 at 9:30 pm, then the paper planisphere at dusk and at noon](docs/time2-plates.png)

By day the Sun in the window has a face and sixteen rays, straight and flaming in turn, after the Sun of May. It stands in its own light, as the first takes drew it: a glow stippled thinner outward, the sky brightest round the Sun, white by day and warm when the Sun is low. The glow shows between the rays and past them, and draws the eye to the Sun, the hour hand. On the ring a gilded Sun hand rides the band at the Sun's own hour, as on the old astronomical clocks (Prague's Orloj, Strasbourg, Wells). A short index runs from it to the scale on the inner rule. It covers whatever it passes, as a clock's hand covers its numerals.

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

### The weather

With the weather, the face shows the place's own sky, drawn as an engraver would draw it. On the watch the phone fetches it from Open-Meteo, which needs no key.

- **The temperature** follows the Sun's rising or setting, set off by a lozenge: 61°, its degree sign raised like the ʰ and ᵐ. The sign came into thermometry in the 1770s. Fahrenheit or Celsius, as the phone is set.
- **Clouds** drift across the window downwind while the stars turn beneath them. They take Luke Howard's three forms (1803):
  - cumulus heaps, flattening into banks as they thicken;
  - the stratus sheet in ruled lines, as the engravers drew it;
  - cirrus in single hair strokes.

  By day the clouds are white with grey bases. At sunset their undersides light rose and gold. At night they are dark, edged with silver, brighter under the Moon.
- **Weather by subtraction.** Haze and cloud take the faintest stars first, then the Milky Way. Behind a heap nothing shows; through the stratus only the brightest stars. Under a closed sky the day goes an even grey, whiter in fog and darker under rain.
- **Rain** falls in fine lines of two tones, leaning with the wind, as Hiroshige cut it. **Snow** falls in soft pecked flakes, never a star's cross.
- **The halo.** Thin high cloud rings the Moon (by day the Sun) at 22 degrees. The ring is drawn in the chart's own projection, so it stretches as the chart does.
- **Fog** lies over the hills in three ruled lines, and the village fades to a ghost of itself.
- **The village reports the weather too:**
  - the church's vane points into the wind;
  - smoke rises from the house's chimney on a cold day and leans downwind;
  - snow lies on every roof, treetop and hilltop.

![Fair at noon, broken cloud at dusk, overcast, rain; snow, fog, the Moon's halo in thin high cloud, and a frosty night with snow lying](docs/weather.png)

### The distant hills

Behind the village, low distant hills stand along the horizon in one quiet tone that takes the hour's light:
- pale with the haze by day;
- gold, then rose, then the mauve of the afterglow as the Sun goes down;
- by night a dark cutout where the stars stop, its ridge faintly silvered.

They are lost in fog and falling rain or snow, and go grey under a closed sky. On the printed charts only their ridge is drawn, engraved.

The hills can be the place's own. From the terrain (Open-Meteo's elevation service, the Copernicus 90 m model, no key), the skyline is worked out once for the place, every two degrees across the window's southern edge:
- Along each bearing the ground is sampled from 5 to 140 km out. The nearer ground is skipped, because the model includes buildings and woods.
- The skyline's height is the steepest angle up to any of that ground, with the Earth's curve taken off and the air's refraction put back.
- It is kept as quiet as the drawn hills: gentle country is magnified at most twice, and big mountains are brought down to the same low band.
- Where the land is flat, as round New York, the drawn hills stand in.

On the watch the phone would do the survey once for each new place and keep the result.

![New York's drawn hills at noon, at sunset, in the afterglow and at night; Chamonix's own skyline (the Mont Blanc massif) at noon, at sunset, in the afterglow, and on a winter's night](docs/mountains.png)

### The year

The village keeps the year, as an almanac's cuts of the months do. The season comes from the Sun's place in the zodiac, turned half a year for the southern hemisphere.
- The trees come into blossom in April, stand in full leaf through the summer, turn gold in October and stand bare through the winter. The firs stay green.
- The house's windows are lit of an evening.
- The Time 2's corner sprigs follow the season.
- The flowers beside the time keep the season too (below).
- As an option the owner can turn on (it is off by default), the month's labour, as the calendars' woodcuts show the year's work, is drawn faint in the card behind the window, in the ring hatching's khaki, so it is felt more than seen. Its field runs on behind the oval: furrows, rows of vines, stubble, grass or snow come out from a point hidden behind the window's top, and a far line of hills crosses behind it. The labourer stands in the cream on the left and the month's thing on the right. The figures follow the cuts' own way of being known at a glance, chiefly the *Kalender of Shepherdes* (Paris, 1493): the labourer's wide straw hat, one pose and one tool drawn large.

| Month | The labour | Beside it | The field |
| --- | --- | --- | --- |
| January | feasting, seated in his hood, the cup raised | the laid table | snow |
| February | warming at the fire, hands held out | the fire | snow |
| March | pruning the vines with a billhook | the vine stakes | vines |
| April | the youth in a plumed hat with a flowering branch | a tree in blossom | grass |
| May | riding out, a hawk on the fist | a heron put up | grass |
| June | mowing, the scythe swept low | a haycock | grass |
| July | reaping, bent double with the sickle | a sheaf | stubble |
| August | threshing, the flail over his head | a stook | stubble |
| September | treading the grapes in the vat | a barrel | vines |
| October | sowing, the seed bag at his front | crows after the seed | furrows |
| November | knocking down acorns for the pigs | the pigs | grass |
| December | baking, the peel at the oven's mouth | the oven | snow |

  South of the equator the labours turn half a year, as the seasons do.

![The labours of the months, January to December, faint in the card either side of the window's top](docs/labours.png)

![The year at eleven in the morning: blossom in April, leaf in July, gold in October, snow in January; below, the village up close: blossom, high summer, autumn leaves, frost and snow; a frosty evening with chimney smoke and lit windows, fog, a summer gale, a snowy night](docs/seasons.png)

And the filigree, all drawn by hand:

- on the southern horizon, a church and a house among trees, after the cuts of a village on an almanac's page. The church stands at the south point, its spire on the meridian and a weather vane on its mast. Each piece is drawn whole and stood on the ground along the window's lower edge: a tree where its trunk meets the ground, a building as low as the ground under it goes. Behind them low distant hills catch the light (below). They keep the season and the weather;
- the engraver's glory of fine rays round the Sun on the printed charts;
- a beaded rule inside the ring's outer rule, as on a clock's chapter ring;
- studs on the inner rule at the numbered hours;
- a star at the south point, clasping the window's two rules, to go with the fleur-de-lis at the north and the lozenges east and west;
- a sprig turning into each of the Time 2's corners, in the season's dress;
- a printer's flower either side of the time, as a title is set off, changing on the hour. The flowers are charted needlework, the period's own pixel art, copied stitch for stitch from the pattern books and samplers in `research/needlework/`.
  - Half the hours bring a piece for the season: a rosette, tulip, bud sprig, lily or buds in spring; a strawberry in summer; grapes, an acorn or an oak leaf in autumn; a fir, berries or snowflakes in winter.
  - The weather takes those hours when it has something to say: a thundercloud in a storm, an ice crystal or a snowflake in snow or frost, a rain cloud in rain, fog lines in fog, and in a gale a pair of pennants (from a Dutch sampler of 1857) blowing outward. No period chart of rain, thunder or fog is known, so those three are drawn here in the samplers' solid stitch, after Mignerak's lacis squares of the elements (Paris, 1605).
  - The other hours bring a piece for any time of year: Quentel's broken lozenge (Cologne, 1529), stars from an Italian sampler of 1802, a chequered lozenge, a ship's globe, a quatrefoil, small birds, an anchor, a little tree. After dark the man in the Moon joins them, from Dillmont's DMC album.
  - Each flower stands midway between the ring and the widest the time can be, so it stays put as the minutes change. Where the hour's piece will not fit (the Round 2 is narrow there), the next of the cycle that will takes its place;
- a face on the full Moon, as the almanacs give it.

![At the Orionids' peak, at an eclipse of the Moon, at an eclipse of the Sun, and as Venus meets Jupiter; below, Jupiter's moons, the village by day, and the glory on Flamsteed's plate](docs/almanac.png)

## Animations

Designed in the prototype; the watch does not play them yet. Each plays for a moment, then the face is still again: a
watch has no battery for more.

- **Falling stars.** Now and then at night a meteor streaks across the window, its head a small cross of white, its trail fading through cream and grey into the sky. On a shower's peak night they come often, and all streak out from the shower's radiant.
- **Birds.** Now and then by day a little flock crosses the sky in a loose V, wings beating, in the village's dark ink.
- **The village.** The hour and the season bring their own passers-by:
  - swallows hawking low over the fields on summer mornings, swooping round the church tower;
  - on a mild evening, a bat dropping out of the belfry and flitting over the roofs;
  - by night the owl on the church's ridge, blinking its gold eyes and looking east and west, with fireflies flashing among the trees on warm summer nights;
  - in autumn, leaves loosed from the trees, tumbling downwind to the ground, and geese going south in a long V;
  - in winter, jackdaws wheeling round the church tower.
- **The weather.** Rain and snow fall, the clouds drift downwind and the chimney smoke rises.
- **The hour.** At the top of each hour, one of two animations, as you choose:
  - **The constellations** (the default). The figures in the window are traced one by one, without their names, each over a second. A cream line runs star to star like an engraver's pen, with its tip white, and each star flashes as the line reaches it. The figure holds a moment, then fades back as the next begins. Those that came into the window during the hour go first, east to west, then the highest in the sky; five at most. By day the figures that are up behind the blue are sketched faintly in white, then fade.
  - **The turn.** The star disc spins through a whole day in a few seconds, then settles back to now, as a planisphere turns in the hand. The window races from night through dawn, the day and dusk, while the Sun's pointer sweeps round the ring. The clock keeps its time throughout.

![Falling stars from the Orionids' radiant on their peak night, at the watch's own frame rate](docs/anim-meteors.gif)

![A flock crossing the morning sky](docs/anim-birds.gif)

![Swallows on a June morning, a bat on an August evening, the owl on an October night, fireflies on a July night, leaves and geese on an October afternoon, jackdaws on a January afternoon](docs/anim-village.gif)

![Rain at noon, snow falling at dusk with smoke from the chimney, and broken cloud hurried across an evening sky](docs/anim-weather.gif)

![The hour's constellations at 9 pm: Taurus and Auriga just risen, then Grus, Cygnus and Cepheus](docs/anim-constellations-night.gif)

![And at noon, sketched over the day sky](docs/anim-constellations-day.gif)

![Or the turn, at 9 pm on the Time 2](docs/anim-turn-time2.gif)

![The turn on the Round 2](docs/anim-turn-round2.gif)

## Experimental: the compass, on a flick

Designed in the prototype; not on the watch yet. Off unless you turn it on, as an experimental setting. The magnetometer costs battery while it runs, so it only runs when you ask. Flick your wrist and the compass turns on for half a minute. The face becomes a window onto the sky where the watch points: the horizon along the bottom, the compass points on it, and names on what is bright. Then the compass switches off and the planisphere comes back; a second flick ends it sooner.

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
- **The Sun is the hour hand.** It rides the ecliptic through the sky, and the gilded Sun hand on the ring follows it. Paper planispheres had no moving marker: you turned the star disc until the date on its rim met the time. Astrolabes read the hour with a straight rule laid over the Sun's place. Astronomical clocks carried a gilded Sun round a 24-hour ring, which is what this ring is. The ring keeps the Sun's own time, as a sundial does: NOON under the window's south point and MIDNIGHT above the pole, fixed, so the pointer reaches NOON as the Sun crosses the south (12:42 by the clock in New York in October). The large numerals keep the clock's time.
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
- **The ornaments** are:
  - the fleur-de-lis standing on the window at the north, the lozenges and the south star;
  - the studs;
  - the corner sprigs through the year;
  - the hour's flowers beside the time;
  - the engraved glory;
  - the village on the horizon.
- **The distant hills** are drawn as straight ridges between hand-placed points: a long ridge rising to a summit on either side, with the steeple against the sky between.
- **The village** is a church (tower, pinnacles, tall spire, nave with lancet windows), a two-storey house with a chimney, and trees: a broad tree, a poplar and a small tree, each in leaf, blossom, turning, gold and bare, and a fir. The church's vane is drawn three ways. Its passers-by are drawn too: a swallow, a bat and a jackdaw on the wing, the owl blinking and looking about, a tumbling leaf, a firefly's flash.
- **The clouds** are Howard's: cumulus heaps and banks drawn as silhouettes, whose tops and bases the face lights for the hour, and cirrus in hair strokes.
- **The almanac's signs** are the zodiac and the planets that rule the days.
- **The ring's hours** are hand-drawn too: roman numerals on the 12-hour clock, figures on the 24-hour clock.
- **The large time** is drawn by hand for each plate's type and each watch:
  - modern scientific figures after Old Standard, with ball terminals and a flagged 1;
  - an engraver's copperplate Didone for Burritt;
  - Caslon's old-style figures for Flamsteed, with 3 4 5 7 9 below the line.

  The Round 2's figures are the Time 2's, grown along their straight runs.
- **MIDNIGHT and NOON** are roman capitals with thick stems, thin hairlines and serifs. Each letter is drawn turned to its own place on each screen's ring, its stems stepping and its bars sloping as the curve turns.

![The hand-drawn pieces at six times and at their own size](docs/pieces.png)

- `proto/astro.py`: sidereal time and the planets, from Paul Schlyter's orbital elements (well under a pixel at this scale); `proto/lunar.py`: the Sun and the Moon from Meeus, closely enough for eclipses.
- `proto/plates.py`: the plates (the current design): the projection, the window as the horizon for your latitude, the sky's colour bands, and the ring.
- `proto/frame.py`: the Time 2's cushion, with exact distances to its edge, so the rules, ticks and lettering run along true parallels of it.
- `proto/events.py`: Jupiter's moons, eclipses, planets meeting and the meteor showers, for the almanac.
- `proto/sprites.py`: the hand-drawn pieces; `proto/letterer.py` and `proto/coverage.py`: the drafting table the curved words were drawn from; `proto/closeup.py`: close-ups of the faces, pixel by pixel, for checking.
- `proto/figures.py`: the large time's hand-drawn figures; `proto/foundry.py`: the drafting table they were drawn from; `proto/typeset.py`: the typefaces they follow (and the large time where no figures are drawn); `proto/pixeltext.py`: the pixel type.
- `proto/weather.py`: the weather as the phone would fetch it, Howard's sky from it, and the barometer's and thermometer's words; `proto/skies.py`: the clouds, rain, snow and halo drawn into the window.
- `proto/horizon.py`: the place's own skyline from the terrain, kept in `data/horizons/`.
- `proto/look.py`: the compass view; `proto/animate.py`: the animations and their films.
- `proto/film_plates.py`: the plates' films and stills; `proto/film.py`, `proto/film_readable.py`: the earlier takes' (`proto/render2.py` draws those).

```
uv run python proto/film_plates.py      # writes docs/
```

## On the watch

`watchface/` is the face itself: the prototype's drawing ported to C (`watchface/src/c`), the pieces, the stars, the
type and each watch's ring packed into the app's resources by `tools/gen_tables.py`. It lands on the prototype's
pixels: `tools/parity.py` compares the two case by case (every plate, both watches, the south, the weather, the
eclipses, the labours), and no case differs in more than 0.7% of its pixels. The watch has no room for double
precision, so the Sun, the Moon and the planets are worked out in single precision, their large angles kept exact as
fractions of a turn in whole numbers.

The phone (`watchface/src/pkjs/index.js`) finds where it is, names the place, and fetches the weather there from
Open-Meteo every half hour; the watch keeps them and draws the face once a minute. The settings page shows the face
as you set it, at any time and date: the watch's own C built to WebAssembly (`preview/`) draws the preview and each
plate's thumbnail.

The page is set like a page of the chart: Old Standard (the type the plate's large time follows), letter-spaced
red titles under the face's own fleur-de-lis, the engraver's double rules, the gilded Sun riding the clock's scale, the
plates captioned as in an atlas, the face's blue noise as the paper's grain. It takes the colours of the plate chosen:
vellum and ultramarine for the Book of Hours, black and gold for the Orloj, cobalt for the Cyanotype.

![The settings page: the live preview, and the plates as live thumbnails](docs/settings-page.png)

![The page in the Planisphere's, the Book of Hours', the Orloj's, the Cyanotype's and Apian's colours](docs/settings-themes.png)

The owner may keep the days of any of twelve calendars (the settings page's "The calendar"): the sky's year, the
Christian year, the Eastern churches, old English customs, the fire festivals, ancient Rome, the United States,
Britain and Ireland, and the Hebrew, Chinese, Islamic and Hindu calendars. On a feast day the almanac's line names it
in red, its emblem stands beside the time, and some bring a light in every window or fires on the hills
(`proto/feasts.py` has the days and their rules; `watchface/src/c/plan_feasts.c` follows it, checked day by day by
`tools/check_feasts.py`). Some mark the sky: Christmas Eve's first star, Qixi's Weaver and Cowherd with the magpies'
bridge, the rabbit in the Mid-Autumn Moon. And at the top of each evening hour of a fireworks feast (Independence Day,
Bonfire Night, Diwali, New Year's Eve, Hogmanay, the Spring Festival), and at the midnight when New Year's Eve and
Chuxi turn the year, a display of rockets plays over the window for seven or eight seconds, on the watch and in the
settings page's preview (`proto/feast_draw.py`, `watchface/src/c/plan_show.c`; films in `research/holidays/`).

The drawing is larger than PebbleOS lets an app's own code be (64 KB, from the way it records an app's size), so it
is not linked into the app. `tools/build_blob.py` compiles it into one of the app's resources, and the app loads it at
start, fixes up its addresses, flushes the caches and runs it from its own memory; the calendars' code is a second
blob, loaded once a day with the calendars' table to find the day's feast, then let go, and the fireworks display a
third, loaded for the seconds it plays. The app itself is under 5 KB.

```
cd watchface && pebble build                                         # the watch app, for both watches
sh tools/build-host.sh && build/host emery 0 $(date +%s) 40.71 -74.01 -240 out.ppm   # one face, on the computer
bash preview/build.sh && (cd proto && uv run python ../tools/build_page.py)          # the settings page
```

[docs/RELEASING.md](docs/RELEASING.md) has the release steps and the checks to run first;
[docs/STORE-LISTING.md](docs/STORE-LISTING.md) has the store's copy, and `docs/screenshots/store/` its gallery
(`tools/store_gallery.py`).

## Credits

Star positions and colours, constellation lines and the Milky Way's outline come from [d3-celestial](https://github.com/ofrohn/d3-celestial), © 2015 Olaf Frohn, BSD 3-Clause (`data/`). The numerals use the monoline stroke font made for Morphogen 9.

Quentel's flower is transcribed from *Eyn New Kunstlich Boich* (Peter Quentel, Cologne, 1529) in the Metropolitan Museum of Art's Open Access collection (CC0, 20.50.2). The season's pieces come from the same book and from Quentel's book of 1544 and Vosterman's of c. 1527 (the Met, CC0), a German sampler (Cooper Hewitt, public domain), Dillmont's DMC album of 1890 and the *Petit nécessaire* of 1819 (archive.org, public domain); `research/needlework/sources.md` gives every source.

Pixel type: Not Jam Old Style 11 by Not Jam (CC0, `fonts/pixel/`). Type: Old Standard TT (Alexey Kryukov), Libre Caslon Text, Playfair Display, with IM Fell, EB Garamond and Cinzel tried in [the type specimen](docs/type-specimen.png). All are SIL Open Font License 1.1, and the licences are in `fonts/`.
