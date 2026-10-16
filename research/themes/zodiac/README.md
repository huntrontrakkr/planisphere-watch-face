# The Zodiac: woodcut references for the twelve signs

Reference set for drawing the zodiac signs as faint 40x30 px background scenes
and 20 px corner roundels. Every image here is public domain or CC0. The notes
describe what is **actually drawn** in each cut: the pose, the attributes, which
way the figure faces, and how much of the frame it fills.

All files are in `images/`, named `<source>-<subject>.jpg`. Pages that held
several things are cropped to the figure.

## Sources

| Key | Title / edition | Printer, place, year | Holding institution / id | URL | Licence |
|---|---|---|---|---|---|
| `hyginus1482` | Hyginus, *Poeticon astronomicon* ("Clarissimi viri Iginij poeticon astronomicon ..."), constellation woodcuts of book III, printed in black with some red | **Erhard Ratdolt, Venice, 1482** (eds. Jacobus Sentinus and J. L. Santritter; colophon g10v) | Boston Public Library, via Internet Archive `poeticaastronomi00hygi`; page images `$69`-`$83` of the IIIF sequence (Aries $69 ... Pisces $83; the zodiac runs $69-$74 and $79-$83) | https://archive.org/details/poeticaastronomi00hygi | Public Domain Mark 1.0 (IA licenseurl) |
| `kalendrier1529` | *Le compost et kalendrier des bergiers*: the zodiac roundels inside the twelve large month woodcuts, as reproduced in *The Kalendar of Shepherds* (London: Sidgwick & Jackson, 1908) | Blocks of the **Troyes edition of 1529** (same set as Guy Marchant, Paris 1493/1499) | Internet Archive `kalendarofshephe00compiala`; cropped from `../../labours/images/kalendrier1529-MM-*.jpg` (see the labours README for leaf numbers) | https://archive.org/details/kalendarofshephe00compiala | Public domain (woodcuts 1493-1529; 1908 reproduction published before 1930; IA: NOT_IN_COPYRIGHT) |
| `durer1515` | Albrecht Dürer, *Imagines coeli Septentrionales cum duodecim imaginibus zodiaci* (The Northern Celestial Hemisphere), woodcut | **Albrecht Dürer** (with Johannes Stabius and Konrad Heinfogel), Nuremberg, **1515** | National Gallery of Art, Washington, Rosenwald Collection, accession **1954.12.233** (NGA object 43181); Commons `File:Albrecht Dürer, The Northern Celestial Hemisphere, 1515, NGA 43181.jpg` (3588x3822) | https://commons.wikimedia.org/wiki/File:Albrecht_D%C3%BCrer,_The_Northern_Celestial_Hemisphere,_1515,_NGA_43181.jpg | CC0 (NGA Open Access) |
| `kalendarium1482` | Regiomontanus, *Kalendarium*: the volvelle "Instrumentum veri motus lune" (leaf [d]1), outer ring of zodiac glyphs | **Erhard Ratdolt, Venice, 9 August 1482** | Bibliothèque Sainte-Geneviève, Paris, OEXV 540 RES (P.1), via Internet Archive `OEXV540_P1`, file `BSG_OEXV540_P1__02_000068.jpg` | https://archive.org/details/OEXV540_P1 | Public Domain Mark 1.0 (IA: "domaine public") |
| `sacrobosco1490` | Johannes de Sacrobosco, *Sphaerae mundi compendium*: diagram of the nine spheres, outer ring of zodiac glyphs, planet glyphs along one radius (leaf a3v area) | **Boneto Locatelli for Ottaviano Scoto, Venice, 1490** (blocks from the De Sanctis edition of 1488, perhaps designed by Santritter) | Boston Public Library, via Internet Archive `sphaeraemundicom00sacr`, IIIF page `$16` | https://archive.org/details/sphaeraemundicom00sacr | Public Domain Mark 1.0 (IA licenseurl) |

Notes on sources:

- A second copy of the Ratdolt Hyginus woodcuts is Getty Research Institute's
  **1485** Ratdolt edition, IA `clarissimivirihy00hygi` ("31 woodcuts from the
  1482 ed."). It is the same set of blocks, so it was not downloaded; use it if
  a figure in the BPL copy is weakly inked.
- The 1482 Hyginus follows the old tradition in which **Libra is the Scorpion's
  claws**: there is no separate Libra cut. The scorpion holds the balance in its
  right claw (`hyginus1482-scorpio-libra.jpg`).
- The Kalendrier roundels are a fully independent series, and each sign appears
  **twice** in it (see the next section), so every sign has at least three
  drawings across Hyginus, the Kalendrier and Dürer.
- Dürer's chart shows the sky **from outside the globe**, so the figures are
  mirror-reversed, mostly seen from behind, and turned to follow the ecliptic
  (Aries and Taurus are upside down at the top). Grid lines, star numbers and
  neighbouring constellations cross them. Use them for anatomy and style, not
  as silhouettes. The crops overlap and are loose.
- Not used: the Regiomontanus *Kalendarium* month pages carry sign glyphs in
  the sun column, but the Sainte-Geneviève scans are only about 1090 px high,
  so the glyphs are about 12 px tall; Gallica's own *Kalendarium* images on
  Commons (btv1b21001577) are 1024 px and too small as well.

## The roundels in the Kalendrier month cuts

Each month cut has **two roundels in the right-hand column**: the upper one is
the sign the sun is in at the start of the month, the lower one the sign it
enters during the month. So each sign appears at the bottom of one month and
at the top of the next. Several roundels also hold a large 12- to 16-point
star (the sun, or simply a star).

| Month | Upper roundel | Lower roundel | Files |
|---|---|---|---|
| Jan | Capricorn | Aquarius | `kalendrier1529-roundel-capricorn-01`, `-aquarius-01` |
| Feb | Aquarius | Pisces | `-aquarius-02`, `-pisces-02` |
| Mar | Pisces | Aries | `-pisces-03`, `-aries-03` |
| Apr | Aries | Taurus | `-aries-04`, `-taurus-04` |
| May | Taurus | Gemini | `-taurus-05`, `-gemini-05` |
| Jun | Gemini | Cancer | `-gemini-06`, `-cancer-06` |
| Jul | Cancer | Leo | `-cancer-07`, `-leo-07` |
| Aug | Leo | Virgo | `-leo-08`, `-virgo-08` |
| Sep | Virgo | Libra | `-virgo-09`, `-libra-09` |
| Oct | Libra | Scorpio | `-libra-10`, `-scorpio-10` |
| Nov | Scorpio | Sagittarius | `-scorpio-11`, `-sagittarius-11` |
| Dec | Sagittarius | Capricorn | `-sagittarius-12`, `-capricorn-12` |

(The two "scorpion-like" things in July and October/November are different
animals: July's upper roundel is Cancer drawn as a **crayfish or lobster**, while
October's and November's Scorpio is a crayfish-bodied scorpion whose tail ends in
a second, snake-like head.)

Each roundel is a single ruled circle, about 27% of the cut's width (about
560-620 px in these scans). There is no inner border or lettering. The figure
stands on a strip of hatched ground across the lower third and usually reaches
the circle at the head and the feet. The background outside the circle is the
busy month scene, so the crops include some of it.

## Image index

| Sign | Hyginus 1482 (constellation figure) | Kalendrier 1529 (roundel) | Dürer 1515 (chart figure) |
|---|---|---|---|
| Aries | `hyginus1482-aries.jpg` | `kalendrier1529-roundel-aries-03.jpg`, `-04` | `durer1515-aries.jpg` |
| Taurus | `hyginus1482-taurus.jpg` | `kalendrier1529-roundel-taurus-04.jpg`, `-05` | `durer1515-taurus.jpg` |
| Gemini | `hyginus1482-gemini.jpg` | `kalendrier1529-roundel-gemini-05.jpg`, `-06` | `durer1515-gemini.jpg` |
| Cancer | `hyginus1482-cancer.jpg` | `kalendrier1529-roundel-cancer-06.jpg` (crab), `-07` (crayfish) | `durer1515-cancer.jpg` |
| Leo | `hyginus1482-leo.jpg` | `kalendrier1529-roundel-leo-07.jpg`, `-08` | `durer1515-leo.jpg` |
| Virgo | `hyginus1482-virgo.jpg` | `kalendrier1529-roundel-virgo-08.jpg`, `-09` | `durer1515-virgo.jpg` |
| Libra | `hyginus1482-scorpio-libra.jpg` (in the claws) | `kalendrier1529-roundel-libra-09.jpg`, `-10` | `durer1515-libra.jpg` |
| Scorpio | `hyginus1482-scorpio-libra.jpg` | `kalendrier1529-roundel-scorpio-10.jpg`, `-11` | `durer1515-scorpio.jpg` |
| Sagittarius | `hyginus1482-sagittarius.jpg` | `kalendrier1529-roundel-sagittarius-11.jpg`, `-12` | `durer1515-sagittarius.jpg` |
| Capricorn | `hyginus1482-capricorn.jpg` | `kalendrier1529-roundel-capricorn-01.jpg`, `-12` | `durer1515-capricorn.jpg` |
| Aquarius | `hyginus1482-aquarius.jpg` | `kalendrier1529-roundel-aquarius-01.jpg`, `-02` | `durer1515-aquarius.jpg` |
| Pisces | `hyginus1482-pisces.jpg` | `kalendrier1529-roundel-pisces-02.jpg`, `-03` | `durer1515-pisces.jpg` |

Glyphs: `kalendarium1482-volvelle-glyphs.jpg` (Ratdolt 1482, whole volvelle;
the glyphs are about 20 px in the scan) and `sacrobosco1490-spheres-glyphs.jpg`
(Venice 1490, about 50-60 px glyphs, the clearest set found).

Resolution: the Hyginus crops are 1600 px on the long side (from 2771x4013
page scans), crisp, on toned paper with show-through. The Kalendrier roundels
are about 640x700 px, crisp black-and-white. The Dürer crops are 500-1400 px.

## Sign by sign

"Faces" means the direction the head points as printed. In the Hyginus cuts the
stars of the constellation are marked on the figure as six-pointed stars. They
make a natural pixel motif: one lit pixel per star over a faint body.

### Aries

- **Hyginus 1482**: a woolly ram **walking to the left** on its own (no ground
  line), head held high at the upper left with the face turned back to the
  right, one big curled horn, fleece drawn as rows of curls, a tufted tail. It
  is long and low, about 1.3:1 wide to tall.
- **Kalendrier**: a ram **walking right** on hatched ground, one curled horn,
  smooth body with a few hatch lines, the star above its back (Mar and Apr are
  nearly the same drawing).
- **Dürer**: a ram lying upside down along the ecliptic, its head with a large
  ram's-horn spiral at the lower right, fleece in curls.
- Scene 40x30: the Kalendrier ram walking right, body about 26x14 px, legs
  4-5 px, on a 1 px ground line, with the star (a 5-7 px asterisk) up to the
  left. Corner 20 px: ram's head and forequarters facing right, with the horn as
  a 4 px spiral, the one detail that reads at that size.

### Taurus

- **Hyginus 1482**: the traditional **half bull**, forepart only, **kneeling to
  the left** with the forelegs folded under, head turned three-quarters to the
  viewer, two tall horns, the Pleiades as a cluster of seven stars below the
  muzzle. The body ends on the right in a scalloped cloud edge.
- **Kalendrier**: a whole bull **facing right**. In April its head is lowered
  as if grazing or charging and the tail is thrown up in a large loop over the
  back; in May the head is up and the tail is raised.
- **Dürer**: half bull, upside down, at top left.
- Scene: the Kalendrier April bull, head down to the right, tail loop up at the
  left; the loop is the identifying mark. About 30x18 px. Corner: bull's head,
  frontal, with two horns curving up (a U on a block), 14 px wide.

### Gemini

- **Hyginus 1482**: two **winged** youths in long robes **standing side by side,
  frontal**, the left one's arm over the other's shoulder; the left holds a
  curved staff or sickle, the right a small lyre or basket. Tall: about 1:1.
- **Kalendrier**: two nude figures, a man and a woman, **embracing, cut off at
  the waist**: in May they stand in water (wavy lines), in June among leaves.
  Only heads, shoulders and arms show.
- **Dürer**: two putti tumbling head-down along the ecliptic.
- Scene: the Kalendrier pair, two heads 5 px wide touching, shoulders joined,
  and three wavy water lines below; about 20x18 px in the 40x30 frame. Corner:
  two heads side by side over a single line of water.

### Cancer

- **Hyginus 1482**: a large **crab seen from above**, round carapace with a
  rimmed edge, both claws on the right (it **faces right**), four legs per side
  ending in little stars, eyes on stalks. It is nearly round.
- **Kalendrier**: June shows a crab from above (round shell, scale-like marks,
  claws up); **July shows a crayfish or lobster** lying horizontally, facing
  right, legs and claws raised, a fan tail at the left.
- **Dürer**: a lobster/crayfish seen from above, tail up.
- Scene: the round top-view crab of Hyginus or June, about 18 px across with
  the claws on the right, centred. Corner: the same crab, 12-14 px: a circle,
  two claws, three legs a side. Avoid the crayfish, which is too close to
  Scorpio at small size.

### Leo

- **Hyginus 1482**: a lion **walking left**, head turned to face the viewer,
  a full curly mane, the tail raised and curled into a loop above the back.
- **Kalendrier**: a lion **walking right**, face frontal with a ruff of mane,
  the tail flicking up behind (in August it is drawn like a flame).
- **Dürer**: a lion rearing, seen from behind, head turned back.
- Scene: Kalendrier lion walking right, body about 26x14 px, the mane a dark
  mass of 8-9 px round the face, the tail up. Corner: the lion's frontal face in
  its mane, 14 px across (a sun-like face reads well at 20 px).

### Virgo

- **Hyginus 1482**: a **winged woman standing frontal** in a long girdled
  robe, holding an ear of wheat (left) and a caduceus-like staff (right); a row
  of stars along the hem.
- **Kalendrier**: a long-haired maiden, three-quarter view, in a long gown,
  holding a palm frond or ear of wheat (August), or seated holding a frond
  (September), with stars around.
- **Dürer**: a winged woman lying along the ecliptic, robe streaming.
- Scene: a standing robed figure 10 px wide and 24 px tall, triangular skirt,
  long hair, an ear of wheat held up to one side. Corner: head and shoulders
  with the wheat ear rising beside them.

### Libra

- **Hyginus 1482**: no separate figure; the **balance hangs from the Scorpion's
  right claw**, with two dish pans on chains.
- **Kalendrier**: September shows **just a balance**: a beam with a pointer,
  two dish pans on three cords each, stars round it. October shows a **woman
  holding the balance** in front of her by its handle.
- **Dürer**: a plain balance, its handle held by Virgo's hand.
- Scene: the plain balance, centred, beam 24 px wide, pans 8 px wide at 10 px
  below the beam, a vertical post to a base. Corner: the balance alone, beam
  14 px, pans 5 px: the most legible of all twelve.

### Scorpio

- **Hyginus 1482**: a scorpion **seen from above, facing right**, a segmented
  oval body, four legs a side, the claws reaching right (one holding Libra's
  balance), the tail curved up to the left ending in a sting.
- **Kalendrier**: an odd **crayfish-like scorpion facing right**: a long
  segmented body with legs and claws raised, the tail curling down and forward
  beneath the body and **ending in a second small head** (like a snake's).
- **Dürer**: a scorpion seen from above with its tail curled to the right.
- Scene: the Hyginus top-view scorpion with the tail arched up and over, about
  28x16 px. Corner: the tail curl and claws are what read; draw the body as a
  3 px wide segmented bar with a tail curling up into a hook.

### Sagittarius

- **Hyginus 1482**: a **centaur galloping, the human half at the left drawing
  a bow aimed left**, horns and beard (satyr-like), a cloak billowing behind to
  the right; an arrow lies below.
- **Kalendrier**: a bearded centaur with a long serpent-like tail curling up
  behind; the man's torso faces the viewer, drawing a bow held at the right with
  one hand at his ear.
- **Dürer**: a centaur with a flowing tail, bow drawn, seen from behind.
- Scene: a centaur in profile, horse body 20x10 px with four legs, torso rising
  from the front, the bow a 10 px arc with the string drawn back. Corner: the
  bow and arrow alone (bent arc plus an arrow across it, diagonal) reads better
  than a 20 px centaur.

### Capricorn

- **Hyginus 1482**: the classical **sea-goat**: the forepart of a goat facing
  left, head three-quarter with long swept-back horns and a beard, one foreleg
  raised, and a long scaly **fish tail running right and tied in a knot**,
  ending in a ring at the upper right.
- **Kalendrier**: a **plain goat** with no fish tail, standing **facing
  right**, long curved horns and a beard (January and December).
- **Dürer**: a goat forepart with a curling fish tail.
- Scene: the Hyginus sea-goat turned to face right: goat forequarters about
  14x14 px with the horns sweeping back, and a fish tail curling up behind in a
  12 px spiral. Corner: goat head with a long curved horn over a tail curl.

### Aquarius

- **Hyginus 1482**: a young man **striding left** with his head turned right
  and down, long hair, a short tunic and boots, a cloak over one arm, **pouring
  water from a jar** held in both hands at his right side; the stream (drawn
  as a column of stars) falls into a shallow basin at his feet.
- **Kalendrier**: a **winged nude boy kneeling, frontal, pouring from two jars**
  at once, one in each hand; the streams fall to the ground on both sides.
- **Dürer**: a man pouring from a jar, upside down.
- Scene: a figure about 10x22 px holding a jar tipped to one side, with a
  3-4 line zigzag stream falling to a basin. Corner: a single tipped jar
  pouring three wavy lines.

### Pisces

- **Hyginus 1482**: **two fish, one above the other, both facing right**,
  joined tail to tail by a long star-dotted cord that loops between them.
- **Kalendrier**: **three fish** (not two) laid horizontally across the
  roundel: in March the top and bottom face right and the middle one left; the
  February version adds extra small heads at the lower right.
- **Dürer**: one fish diving, the other far away round the rim.
- Scene: the Hyginus pair, each fish about 16x5 px, offset, facing opposite
  ways if a mirror pair is wanted (the later convention), joined by a 1 px cord.
  Corner: two fish in a circle swimming in opposite directions; the 3-fish
  Kalendrier layout fits a roundel well too.

## Glyphs as the period printers cut them

The Sacrobosco 1490 diagram (`sacrobosco1490-spheres-glyphs.jpg`) puts the
twelve glyphs round the outer ring, running **counter-clockwise from Aries at
the left**: Aries, Taurus, Gemini at the bottom, Cancer, Leo, Virgo on the right,
Libra, Scorpio, Sagittarius at the top, Capricorn, Aquarius, Pisces. The forms
differ from modern type:

- **Aries**: a simple Y-like fork.
- **Taurus**: a small circle with a hooked stroke on top, closer to a tailed
  "8" than to the modern circle with horns.
- **Gemini**: two upright strokes with bars top and bottom (Roman II).
- **Cancer**: two hooks, "69", stacked rather than side by side.
- **Leo**: a loop with a long tail, like a looped "d" or "ϑ".
- **Virgo**: an "m" whose last stroke ends in a closed loop.
- **Libra**: a hump over a bar.
- **Scorpio**: an "m" whose last stroke ends in an arrowhead.
- **Sagittarius**: a vertical shaft with a cross-bar and arrowhead (‡-like).
- **Capricorn**: a ligature like "ƀ", an upright with a looped tail.
- **Aquarius**: two (sometimes three) short wavy lines.
- **Pisces**: two back-to-back arcs crossed by a bar, ")-(".

The Ratdolt *Kalendarium* volvelle has the same forms at a smaller size,
around a dark disc holding a man-in-the-moon crescent inside a sun with wavy
rays, a ready-made motif for a planisphere face. The 1490 diagram also shows
the planet glyphs (Saturn, Jupiter, Mars, Sun, Venus, Mercury, Moon) in a column
along one radius.

## Suggestions for the pixel art

- **Corner roundels (20 px)**: copy the Kalendrier format: a single 1 px
  circle, a 1-2 px ground strip across the lower third, and the figure filling
  the circle edge to edge. A 3-5 px star in the free upper corner balances it
  and ties the set together. Best readers at 20 px: Libra (balance), Cancer
  (top-view crab), Pisces (fish), Aries (horn spiral), Taurus (horned head),
  Leo (maned face). Hardest: Virgo, Gemini, Sagittarius and Aquarius. For these,
  reduce to an attribute (wheat ear, two heads, bow and arrow, tipped jar).
- **Faint 40x30 scenes**: the Hyginus figures are the better model. They float
  on blank paper with no frame, which suits a faint background, and their stars
  are already marked; draw the figure in the faintest tone and put the
  constellation's stars on top as single brighter pixels. Face the figures in
  one consistent direction (the Kalendrier mostly faces right).
- **Glyphs**: if a 7-9 px glyph is needed, base it on the 1490 forms above; they
  are more calligraphic than modern type and match the woodcut look.
