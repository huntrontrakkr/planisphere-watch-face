# Holidays and festivals for the Planisphere face

A working reference for "holiday effects": which days, how to compute them on the watch, what period sources draw
for them, and where a small hand-drawn piece would go on the face. Written 2026-10-15. Nothing here is implemented.

Contents: 1. how a feast shows on the face · 2. the candidates (table) · 3. the entries · 4. date code · 5. starter
set · 6. regions and settings · 7. sources and reference images.

Conventions. Sizes are in pixels at 1x. Inks are the face's own roles (K ink, R accent red, Y gold, the plate's
paper or cream, the hatch khaki), so no feast brings a new colour. "Eve" means from local sunset the evening before.
E = Western Easter Sunday. Dates are Gregorian unless marked O.S. (Old Style, Julian).

---------------------------------------------------------------------------------------------------------------------

## 1. How a feast shows on the face

Seven channels, quietest first. A feast uses the first two always, and at most one village effect and one window
effect besides. One feast per day (see §6 for clashes).

| # | Channel | Where | What it does | Notes |
| --- | --- | --- | --- | --- |
| 1 | **Red letters** | the almanac line, the date | The almanac line names the day ("CHRISTMAS DAY", short form "CHRISTMAS") in place of the sunrise or sunset. On principal feasts the date itself is written in red, as calendars rubricated their great feasts: that is what a *red-letter day* is (the Book of Common Prayer's calendar prints the principal holy days in red and the lesser saints in black). Folk and lesser days keep a black date. French Books of Hours write the great feasts in gold among saints in alternating red and blue ("Jour de noel" in gold: Walters W.99, the *Très Riches Heures*, §7), so the Hours plate can letter its feasts in gold. | Priority on the line: eclipse > feast > planets meeting > shower peak > Moon by a planet > sunrise/sunset. Each feast needs a long and a short wording, as `events.news` has. The eve's wording ("CHRISTMAS EVE", "TWELFTH NIGHT", "ALL HALLOWS' EVE") runs from sunset. |
| 2 | **Flank pieces** | either side of the time | The printer's flowers beside the time take the feast's emblem for the day, as `OF_WEATHER` takes the seasonal hours. One-colour pieces up to about 15×15 in the accent ink, after the calendar sticks' pictograms (§3, §7) or the needlework charts (`research/needlework/`). | The main picture for every feast. Mirror the pair where the emblem has a direction (birds, horn, goose). |
| 3 | **Corners** (Time 2) | the four 9×9 corner sprigs | The sprigs change to the feast's greenery: holly, ivy, box, yew, birch, oak with an oak apple, hawthorn, willow "palms", shamrock. | Herrick's *Ceremonies for Candlemas Eve* (1648) gives a whole year of house greenery that can drive the corners from the movable feasts (§3, the rule after A12). |
| 4 | **The village** | the church, the house, the two greens (dx ≈ −54 and +52), the gap between house and church (dx −11…−6), the far hills | FIRE: a bonfire on a green (about 7×9, two frames, ink core, gold and red flame, grey smoke leaning downwind as the chimney's does, a little stippled glow) or beacons on the far hills' summits (3×4 each, at dx ±31/±43). LIGHTS: the house's windows, the church's three lancets and belfry. PROPS: a maypole, a booth, a lantern string, a turnip lantern at the door, a flag or an oak bough on the church. SMOKE: the chimney smokes on Christmas regardless of the temperature (the Yule log). | Night effects only when the Sun is below −6°. Props stand on the ground the way the trees do (at their foot). |
| 5 | **The window** | the sky above the village | FIREWORKS: rockets rising from behind the village, bursts of 8 or 12 rays (7–11 px) in two inks, fading through cream and grey like the meteors' trails; the still frame keeps two bursts low over the village. KITES by day. SKY MARKS on real objects: the rabbit in the full Moon, the Weaver and the Cowherd (Vega, Altair), MATARIKI over the Pleiades, Sirius as the Dog Star, the young crescent. | Never paint a false object into the live sky (no Star of Bethlehem over the steeple: the star goes in the flank). Fireworks keep below the lowest label. |
| 6 | **The labours** (if on) | faint in the card | The feast's scene takes the month's labourer for the day: ploughboys hauling the plough, the spinner with her distaff, wassailers at the apple tree, candle-bearers, maypole dancers, the goose. | Same 12–18 px silhouette style as the Kalender figures. |
| 7 | **Animation** (when the watch plays them) | | Thirteen rockets (Independence Day), the Easter Sun dancing at sunrise, lanterns walking (Martinmas), a wheel of fire rolling down a hill (Midsummer Eve), a gun's flash under the apple tree (wassail). | Prototype first, as the other animations were. |

Restraint: two inks per emblem at most; no flags in full, no rainbows, no cartoon figures (Santa, rabbits, turkeys,
witches, leprechauns); a feast never hides a label or an eclipse. Things noted as garish in the entries are left out.

Fireworks' colours, historically: until the 1830s fireworks burned only gold, orange and white (charcoal and iron
filings); Italian makers then added metal salts, strontium for red and barium for green; blue, from copper, is still
the hardest to make ([Smithsonian](https://www.smithsonianmag.com/arts-culture/14-fun-facts-about-fireworks-180951957/),
[Live Science](https://www.livescience.com/63468-fireworks-history.html)). So Philadelphia's thirteen rockets of 1777
were gold and white. Gold-and-white bursts are the period-true palette for the paper plates; red, white and blue is a
modern reading (fine on the night plates).

**Drawing the emblems.** The calendar sticks show how: a saint is never drawn, only the thing that stands for him or
her (Catherine's wheel, Lawrence's gridiron, Clement's pot), cut as a few strokes. So each emblem is one object with
one strong outline: a horn's curve, a wheel's spokes, a candle's flame, a plough's handles, a goose's neck. Faces,
hands and lettering do not survive 15 pixels; neither do scenes, which belong to the labours (which are drawn bigger
and faint). Draw them as the needlework pieces are drawn, solid stitch or one-pixel line work, one ink plus gold for
flames, and mirror them for the pair either side of the time.

**Fitting the prototype's hook.** `proto/feasts.py` (dates), `proto/feast_draw.py` and `render(feast=…)` already take a
feast as a dict: `words` (long, short), `emblem` (a flank piece), `brings` (`"lights"`, `"bonfires"`) and `fireworks`
(a palette name); `proto/film_feasts.py` films July 4th and Bonfire Night into this folder. The channels above map onto
it as further keys: `rank` ("red" or "black" date), `eve` (start at sunset), `corner` (greenery), `brings` adding
`"church"` (lit lancets), `"smoke"` (the Yule log), `"maypole"`, `"lanterns"`, `"booth"`, `"kites"`, `"door-lantern"`,
`"pennant"`, and `sky` (`"rabbit-moon"`, `"weaver"`, `"matariki"`, `"dog-star"`, `"first-star"`, `"crescent"`). For example:

```python
CHRISTMAS = dict(calendar="christian", rule=("fixed", 12, 25), rank="red", eve="sunset",
                 words=("CHRISTMAS DAY", "CHRISTMAS"), eve_words=("CHRISTMAS EVE",),
                 emblem="holly", corner=("holly", "ivy"), brings=("smoke", "lights", "church"),
                 church_hours=("eve", 23, 1), sky=("first-star",))
PLOUGH_MONDAY = dict(calendar="old english", rule=("weekday after", 1, 6, "Mon"), rank="black", lapsed=True,
                     words=("PLOUGH MONDAY",), emblem=("plough", "distaff"), labour="ploughboys")
```

---------------------------------------------------------------------------------------------------------------------

## 2. The candidates

46 days in three groups. ★ = in the starter set (§5). Rules in full in §3 and §4.

| # | Day | Date rule | Where, era | Now | The picture, and where it goes |
| --- | --- | --- | --- | --- | --- |
| **A** | **Living civic and religious** | | | | |
| A1 | New Year's Day | 1 Jan; eve 31 Dec | universal; English legal year only from 1752 | living | Janus heads (flank); fireworks at midnight |
| A2 | St Valentine's Day | 14 Feb | from Chaucer, c. 1381 | living | two birds facing (flank) |
| A3 | Shrove Tuesday | E − 47 | Christian Europe | living | pan and pancake (flank) |
| A4 | National saints | 1 Mar, 17 Mar, 23 Apr, 30 Nov | Wales, Ireland, England, Scotland | living | leek, shamrock, saltire (flank, corners); St George's pennant on the church |
| A5 | Easter and Holy Week ★ | E, the computus | Christian | living | Agnus Dei (flank); willow catkins (corners); the Sun dances at sunrise |
| A6 | Independence Day ★ | 4 Jul | US, since 1777 | living | rockets and illuminated windows; ring of 13 stars (flank) |
| A7 | Halloween, All Saints, All Souls ★ | 31 Oct, 1–2 Nov | Scotland, Ireland, US; Catholic Europe | living | turnip lantern at the door (village, flank); the church lit for All Souls |
| A8 | Guy Fawkes Night | 5 Nov | Britain, NZ, since 1605 | living | bonfire on the green, rockets |
| A9 | Thanksgiving | US 4th Thu Nov; Canada 2nd Mon Oct | US 1863/1941; Canada 1957 | living | sheaf (flank) |
| A10 | St Nicholas | 6 Dec; eve 5 Dec | Netherlands, Germany, Central Europe | living | three gold balls (flank) |
| A11 | St Lucy | 13 Dec | Sweden, Norway, Finland, Sicily | living | crown of candles (flank); windows lit before dawn |
| A12 | Christmas and Yule ★ | 24 Dec to 6 Jan; greenery to 1 Feb | Christian; Germanic Yule | living | holly and ivy (corners); Yule-log smoke; the church lit at midnight |
| **B** | **Lapsed and historical** | | | | |
| B1 | Saturnalia | 17 Dec (to 23 Dec) | Rome | lapsed, 5th c. | wax taper and freedman's cap (flank) |
| B2 | Lupercalia | 15 Feb | Rome | ended c. 495 | she-wolf and twins (flank) |
| B3 | Feast of Fools, Boy Bishop | 1 Jan; 6–28 Dec | France, England | lapsed, 15th–16th c. | fool's hood with bells (flank) |
| B4 | Twelfth Night and the wassail ★ | 5 Jan from sunset; 6 Jan; Old Twelfth Night 17 Jan | England | mostly lapsed; orchard wassails revived | wassail bowl, bean-king's crown (flank); lanterns in the apple tree |
| B5 | Plough Monday, St Distaff's Day ★ | Monday after 6 Jan; 7 Jan | England | lapsed by the 1930s; revived | plough and distaff, a pair (flank); ploughboys (labours) |
| B6 | Candlemas ★ | 2 Feb | Europe | customs lapsed in Britain | candle (flank); the church lit; holly gives way to box |
| B7 | Imbolc, St Brigid's Day | 1 Feb | Ireland | living (holiday since 2023) | Brigid's cross (flank, corners) |
| B8 | Hocktide | E + 8, E + 9 | England | lapsed c. 1700 (Hungerford keeps it) | tutti-pole (flank) |
| B9 | Rogationtide, beating the bounds | E + 35 to E + 39 | England | mostly lapsed in the 19th c. | boundary stone; willow wands; a small procession |
| B10 | May Day ★ | 1 May | England, Europe | revived | maypole on the green; hawthorn (corners) |
| B11 | Beltane | 1 May; eve 30 Apr | Gaelic Scotland, Ireland, Man | lapsed 19th c.; revived 1988 | two fires on the hill; rowan cross (flank) |
| B12 | Oak Apple Day | 29 May | England | lapsed 1859 (kept locally) | oak with oak apple (corners); the Royal Oak (flank) |
| B13 | Midsummer Eve and Day ★ | 23 Jun from sunset; 24 Jun | Europe | lapsed in England; living in Scandinavia, the Baltic, Spain | beacons on the hills; birch (corners); fire wheel |
| B14 | Lammas, Lughnasadh | 1 Aug | England, Scotland, Ireland | lapsed | loaf (flank); wheat (corners) |
| B15 | Michaelmas | 29 Sep | England, Europe | quarter day lives; goose lapsed | scales or goose (flank) |
| B16 | Samhain | 1 Nov; eve 31 Oct | Gaelic | lapsed; revived | a fire on the far hill |
| B17 | Martinmas | 11 Nov | Europe | lapsed in England; living in Germany, the Netherlands | lanterns walking; goose (flank) |
| B18 | St Clement, St Catherine | 23 and 25 Nov | England | lapsed, 19th c. | anchor; spiked wheel (flank) |
| **C** | **Set by the Moon or the Sun** | | | | |
| C1 | Solstices and equinoxes ★ | the Sun at 0°, 90°, 180°, 270° | universal | living | almanac line; sun wheel (flank) |
| C2 | Dog Days | 3 Jul–11 Aug, or Sirius's first dawn rising | Egypt to the almanacs | an almanac relic | Sirius named the Dog Star |
| C3 | Passover | 15 Nisan | Jewish | living | matzah (flank); windows lit |
| C4 | Rosh Hashanah, Yom Kippur | 1 and 10 Tishrei | Jewish | living | shofar (flank) |
| C5 | Sukkot | 15 Tishrei, 7 days | Jewish | living | a booth by the house |
| C6 | Hanukkah | 25 Kislev, 8 nights | Jewish | living | the lamp with tonight's lights (flank) |
| C7 | Chinese New Year | month 1, day 1 | China, Vietnam, Korea | living | lanterns at the door; the year's animal (flank) |
| C8 | Lantern Festival | month 1, day 15 | China | living | a string of lanterns |
| C9 | Qixi, Tanabata ★ | month 7, day 7; 7 Jul in Japan | China, Japan | living | Vega and Altair as the Weaver and the Cowherd; a magpie bridge |
| C10 | Mid-Autumn, Tsukimi, Harvest Moon ★ | month 8, day 15; the full moon nearest the September equinox | China, Japan, England | living | the rabbit in the full Moon |
| C11 | Diwali | the amavasya ending Ashvin | India | living | a row of lamps; diya (flank) |
| C12 | Holi | the Phalguna full moon | India | living | the Holika bonfire |
| C13 | Ramadan and the Eids | the crescent | Islamic | living | "THE NEW MOON MAY BE SEEN"; lantern (flank) |
| C14 | Nowruz | the March equinox, Tehran noon rule | Iran, Central Asia | living | sprouted wheat (flank); small fires |
| C15 | Matariki | NZ law; the Pleiades' dawn rising | New Zealand | living | MATARIKI named on the Pleiades |
| C16 | Makar Sankranti, kite days | the Sun into sidereal Capricorn | India | living | kites in the day sky |

§6 groups these days into twelve opt-in calendars (the sky's year, the Christian year, the Eastern churches, Old
English customs, the fire festivals, ancient Rome, the United States, Britain and Ireland, Hebrew, Chinese, Islamic,
Hindu), with the quarter days and the Old Style days (§4.3) as options.

## 3. The entries

Each entry: **rule** · who, where, when · living or lapsed · what the period sources draw · **on the face**
(channels from §1, sizes, inks) · what to avoid. "Stick" = the calendar sticks (Norwegian primstav, English clog
almanac; §7.2 has the full table of their pictograms). BCP = the Book of Common Prayer (1662) calendar.

### (a) Living civic and religious days

**A1 New Year's Day** · 1 Jan; eve 31 Dec (Hogmanay in Scotland) · living.
The Roman consuls took office on the Kalends of January from 153 BC (gifts, *strenae*, of laurel and sweets); in
England the legal year began on Lady Day (25 Mar) until the Calendar Act of 1750 moved it to 1 Jan from 1752
(Scotland had moved in 1600). The church kept the Circumcision (red letter). January's calendar page is Janus,
two-faced, at the feast (the labours' January feaster). On the sticks: the clog marks 1 January with an eye-like device that Plot reads as the Circumcision; primstavs vary (a sun-wheel, an hourglass, a church; Worm's has a dish heaped with New Year cakes). Scotland's first-footing: a dark-haired man
over the threshold after midnight with coal, salt and bread.
- Face: RED "NEW YEAR'S DAY" / "NEW YEAR", red date; the eve from 22:00 "HOGMANAY" (Scottish places) or "NEW YEAR'S EVE". FIREWORKS from midnight for twenty minutes (a modern custom, but now the universal one). FLANK: Janus, two bearded heads back to back (11×11), after the calendar pages.

**A2 St Valentine's Day** · 14 Feb · living.
The lovers' day starts with Chaucer's *Parlement of Foules* (c. 1381): "For this was on seynt Valentynes day, / Whan
every foul cometh there to chese his make" (Oruch 1981 argues Chaucer began it); valentines drawn by lot in the 17th
century (Pepys), printed cards in the 19th. The Lupercalia link is a modern myth. A black-letter day in the BCP.
The clog marks the day with a true lover's knot, for "the coupling of birds" (Plot); the primstav has no Valentine.
- Face: FLANK: two small birds facing, the needlework `quentel1529-small-bird-11x9` and its mirror (Chaucer's birds choosing their mates). ANIM: by day the flock crosses as a single pair. RED "ST VALENTINE'S DAY" / "ST VALENTINE", black date. Avoid: hearts in pink, Cupids.

**A3 Shrove Tuesday** · E − 47 · living (its rougher customs lapsed).
Shriving before Lent; pancakes to use up eggs and fat, the pancake bell; Shrovetide football (Ashbourne, Atherstone,
Alnwick: living); cock-throwing (gone by c. 1800); Carnival and Mardi Gras. Bruegel's *Fight between Carnival and
Lent* (1559, Vienna) is the period picture: Carnival a fat man astride a barrel with a spit of meat, Lent a thin
woman with a baker's peel carrying two herrings. Chambers: "Pancake at Westminster School" ([vol 1 p. 237](https://archive.org/details/bookofdaysmiscel01chamuoft/page/n250/mode/1up)).
- Face: FLANK: the frying pan with the pancake in the air above it (13×10) and its mirror. RED "SHROVE TUESDAY" / "PANCAKE DAY". Ash Wednesday: "ASH WEDNESDAY" in black, no emblem. Avoid: masks and confetti.

**A4 The national saints** · St David 1 Mar, St Patrick 17 Mar, St George 23 Apr, St Andrew 30 Nov · living.
- St Patrick: Ireland's feast, public holiday since 1903; kept by Boston's Charitable Irish Society from 1737, paraded in New York from 1762. The shamrock's Trinity story is first printed by Caleb Threlkeld (*Synopsis Stirpium Hibernicarum*, 1726). No calendar stick marks St Patrick (the primstav's 17 March is St Gertrude's).
- St David: the leek and the daffodil. The clog gives St David a harp, on which he praised God (Plot).
- St George: the red cross on white, flown from church towers on his day; the dragon; the red rose (Catalonia's Sant Jordi: roses and books). The clog: a tall spearhead; primstavs: a cross or a horse.
- St Andrew (red letter in the BCP): the saltire. The clog: a saltire with flared ends; primstavs: a saltire or a fish-hook (the Christmas fishing begins).
- Face: FLANK: shamrock (7×7 trefoil on a stalk, in the plate's leaf ink), leek (5×14) or the clog's harp (9×11) for St David, the saltire after the sticks (9×9), St George's cross on a shield (9×11). On St George's Day the church's mast flies a pennant (6×3, white with a red cross) in place of the vane: it streams downwind, so it still shows the wind. CORNERS: shamrock sprigs on St Patrick's Day. RED "ST PATRICK'S DAY" etc. Avoid: leprechauns, green everywhere.

**A5 Easter and Holy Week** · E (computus, §4.2); Palm Sunday E − 7, Good Friday E − 2 · living.
In England the Palm Sunday "palms" were willow catkins (sallow), carried in procession (forbidden with Candlemas's candles and Ash Wednesday's ashes by the proclamation of January 1548, though "going a-palming" for sallow catkins lasted into the 19th century); hot cross buns on Good
Friday; on Easter morning people rose early to see the Sun dance for joy (Brand; Herrick's "the dancing Easter
day"); pace eggs dyed, rolled and given (Lancashire, Preston); the Paschal lamb with the cross-staff and pennon
(*Agnus Dei*) in calendars and on inn signs ("Lamb and Flag"); the Easter hare is German (described in 1682).
- Face: CORNERS: willow catkins (9×9, silver ovals on a twig) from Palm Sunday to Easter Eve; then yew (Herrick's order, the rule after A12). FLANK: the Agnus Dei (15×12: the lamb in profile with the cross-staff and pennon) or two pace eggs. RED "EASTER DAY" / "EASTER", red date; "PALM SUNDAY"; "GOOD FRIDAY" in black. ANIM: at sunrise on Easter Day the Sun dances, rising and falling a pixel three times. Orthodox Easter in the Eastern churches' calendar (§6). Avoid: rabbits, chicks, pastel eggs.

**A6 Independence Day** (US) · 4 Jul · living; federal holiday since 1870.
John Adams to Abigail, 3 July 1776, of the vote for independence: it "ought to be solemnized with Pomp and Parade,
with Shews, Games, Sports, Guns, Bells, Bonfires and Illuminations from one End of this Continent to the other". At
the first anniversary in Philadelphia, 1777, "there was a grand exhibition of fireworks (which began and concluded
with thirteen rockets) on the Commons, and the city was beautifully illuminated" (*Pennsylvania Evening Post*, 5 July
1777). An illumination meant a candle in every window.
- Face: from dusk (Sun below −6°) to midnight: FIREWORKS low over the village in gold and white, the 1777 palette (red may join on the night plates); the still frame keeps two bursts. LIGHTS: every window of the house and the church lit (the illumination). ANIM: the show begins and ends with thirteen rockets. FLANK: thirteen stars in a ring (13×13, single gold pixels on a circle): Congress's flag resolution of 14 June 1777 asked for "thirteen stars, white in a blue field, representing a new constellation", a fit for a star chart; or the Liberty Bell (11×12, its crack a gap). RED "INDEPENDENCE DAY" / "THE FOURTH", red date. Avoid: stripes, the whole flag, red-white-blue fills.
- The same machinery serves other national days: Canada Day (1 Jul), Bastille Day (14 Jul, *feux d'artifice*), and others the owner adds.

**A7 Halloween, All Saints, All Souls** · 31 Oct, 1 Nov, 2 Nov · living.
Guising (Scotland, Ireland); lanterns cut from turnips ("neep lanterns") or mangel-wurzels (Somerset's "punkies",
Hinton St George, last Thursday of October); the pumpkin is American (19th century); nuts burned in pairs and other
divinations (Burns, "Halloween", 1785; Chambers's "Ducking for apples", [vol 2 p. 520](https://archive.org/details/bookofdaysmiscel02chamuoft/page/n531/mode/1up)); souling for soul cakes and the bells tolled for the dead on All Souls;
candles on graves (Catholic Europe; Mexico's Día de Muertos).
- Face: VILLAGE (from dusk on the 31st): a turnip lantern at the house door (3×3, a dark round with a gold face); the owl and the bat (existing animations) are favoured that night. FLANK: the turnip lantern (9×9, ink, gold eyes and mouth). RED "ALL HALLOWS' EVE" / "HALLOWE'EN"; 1 Nov "ALL SAINTS" (red date); 2 Nov "ALL SOULS", the church's windows lit at dusk. Avoid: orange pumpkins, witches, ghosts, cobwebs.

**A8 Guy Fawkes Night** · 5 Nov · living (Britain; also New Zealand).
The plot of 1605; the Observance of 5th November Act 1605 set a thanksgiving service, kept in the Prayer Book until
the Anniversary Days Observance Act 1859; the bonfires and fireworks never stopped. Colonial Boston's "Pope Night"
was its American cousin (gone by the 1770s). The guy, a straw effigy in hat and cloak, burns on the bonfire;
rockets, squibs and Catherine wheels. Hone's "Guy Fawkes" (*Every-Day Book* I, cols 1431–2: [scan](https://archive.org/details/b29326072_0001/page/n829/mode/1up), [cut](https://www.gutenberg.org/cache/epub/53275/images/illo1858.jpg)); Chambers's "Procession of a Guy" ([vol 2 p. 549](https://archive.org/details/bookofdaysmiscel02chamuoft/page/n560/mode/1up)).
- Face: night: FIRE (a big bonfire on the right green, smoke downwind) and FIREWORKS (gold rockets, no bursts in colours). FLANK: a rocket (3×15: case, stick, a spark at the tail), the pair pointing outward. RED "BONFIRE NIGHT" / "GUY FAWKES".

**A9 Thanksgiving** · US: fourth Thursday of November; Canada: second Monday of October · living.
Lincoln's proclamation of 1863 (the last Thursday of November) after Sarah Josepha Hale's campaign; fixed by
Congress in 1941; Canada's date since 1957. Its English cousins: Harvest Home, the last load brought in (Herrick,
["The Hock-Cart, or Harvest Home"](https://www.gutenberg.org/cache/epub/22421/pg22421-images.html#id_1.p250); Chambers's hock-cart, [vol 2 p. 378](https://archive.org/details/bookofdaysmiscel02chamuoft/page/n389/mode/1up)), and the church's Harvest Festival (R. S. Hawker, Morwenstow, 1843).
- Face: FLANK: the wheat sheaf (11×13, bound at the waist: the heraldic garb) or the cornucopia (13×9). LABOUR: August's stook. RED "THANKSGIVING". Avoid: cartoon turkeys, buckled pilgrims (a 19th-century invention).

**A10 St Nicholas** · 6 Dec; eve 5 Dec · living in the Netherlands, Belgium, Germany, Central Europe.
Sinterklaas's presents on the evening of the 5th; shoes filled overnight (Nikolaus); the Boy Bishop was chosen on
this day (B3). Bishop with mitre and crozier; three golden balls (the three purses of the dowry legend, later the
pawnbrokers' sign); the three boys in the tub; a ship. A black-letter day in the BCP. On the sticks: a crozier (Helland, Worm); the clog an interlaced knot.
- Face: FLANK: three gold balls (three 3×3 discs in a triangle, 9×8), the mitre (9×11), or the sticks' crozier. RED "ST NICHOLAS", black date.

**A11 St Lucy** · 13 Dec · living in Sweden, Norway, Finland, Sicily.
Under the Julian calendar the winter solstice fell on about 12–13 December in the later Middle Ages, so this was the
shortest day: "Lucy light, the shortest day and the longest night"; Donne's "A Nocturnall upon S. Lucies Day, Being
the Shortest Day" (published 1633). Norway and Sweden kept *Lussinatta*, the longest night, when Lussi rode out;
the Swedish Lucia, in white with a crown of candles, before dawn, spread from the 18th century and nationally after
1927. A black-letter day in the BCP. On the sticks: a torch or a candle for the long night (Helland), or a bonfire; Worm's stick has a cow's hoof ringed with sun rays, for the solstice; the clog a lamp-like flask.
- Face: FLANK: the crown of candles (11×9, a wreath with five flames), or the primstav's torch (5×13). LIGHTS: the house's windows lit before dawn. RED "ST LUCY'S DAY" / "ST LUCY", black date; long form "ONCE THE SHORTEST DAY".

**A12 Christmas and Yule** · 24 Dec (eve) to 6 Jan; greenery up until Candlemas Eve · living.
Christmas Day, St Stephen, St John, the Holy Innocents, the Circumcision (1 Jan) and the Epiphany (6 Jan) are all
red-letter days. Yule: Bede names the Old English months around midwinter *Giuli* and the eve of Christmas
*Modranicht*, "the mothers' night" (*De temporum ratione* ch. 15, 725); the Norse *jól* was moved to Christmas by
Hákon the Good in the 10th century (Heimskringla). 25 December is also N INVICTI, the Unconquered Sun's birthday, in
the Calendar of 354 (C1). The Yule log is brought in with a noise and lit from last year's brand, which is kept till
Candlemas (Herrick, ["Ceremonies for Christmas"](https://www.gutenberg.org/cache/epub/22421/pg22421-images.html#id_2.p784) and the Candlemas poems after ["Ceremonies for Candlemas Eve"](https://www.gutenberg.org/cache/epub/22421/pg22421-images.html#id_2.p892)); holly, ivy, bays, rosemary and
mistletoe dress the house until Candlemas Eve (Herrick, below); the kissing bough; the boar's head; the wassail
bowl; the Christmas candle; mumming. The tree is German (Strasbourg, 1605) and came to Britain in the 1840s. Cuts: Chambers's "The Yule Log" ([vol 2 p. 734](https://archive.org/details/bookofdaysmiscel02chamuoft/page/n745/mode/1up)), "Mummers" (Father Christmas with holly and the wassail bowl, a girl with mistletoe: [p. 740](https://archive.org/details/bookofdaysmiscel02chamuoft/page/n751/mode/1up)), "Christmas Fare" ([p. 754](https://archive.org/details/bookofdaysmiscel02chamuoft/page/n765/mode/1up)); Hone's boar's head on its dish, garnished with rosemary (*Every-Day Book* I, cols 1619–20: [cut](https://www.gutenberg.org/cache/epub/53275/images/illo2093.jpg); `ref/`).
On the sticks a drinking horn, on both: the clog's "ancient vessel in which the Danes use to Wassayle" (Plot), Norway's *jolehonne*; some sticks stand horns upright from 21 Dec to 6 Jan, two leaning together on Christmas Day, and turn one upside down on 13 January, when the ale is drunk (Davis, after Gale; Helland).
- Face: CORNERS: holly in two corners and ivy in the other two (the carol's pair: `CORNER_IVY` exists) from Christmas Eve to Candlemas Eve. FLANK: a holly sprig (11×11, ink leaves, three red berries), alternating with the star (`ch-18616385-star-11`) or the Christmas candle (5×13); or the sticks' drinking horn (13×9), upright through the Twelve Days and turned upside down on 13 January, the primstav's *Tjugendedagen*, when Christmas is rung out. VILLAGE: the chimney smokes all of the 24th and 25th, whatever the temperature (the Yule log); the house's windows lit from dusk; the church's lancets lit on Christmas Eve from 23:00 to 01:00 (the midnight Mass). Snow only if it is snowing. SKY: at the end of civil twilight on Christmas Eve the almanac names the first star, when the Polish and Ukrainian suppers begin (§6). RED "CHRISTMAS EVE" (from sunset on the 24th), "CHRISTMAS DAY", then "ST STEPHEN", "ST JOHN", "CHILDERMAS", red dates through the red-letter days. South of the equator it is summer: the corners keep the local season; flank and red letters only. Avoid: Santa, reindeer, coloured light strings, false snow, a star painted into the live sky.

**Rule: Herrick's year of greenery** (for the corners, from A12 through A5 and on). Robert Herrick, ["Ceremonies for
Candlemas Eve"](https://www.gutenberg.org/cache/epub/22421/pg22421-images.html#id_2.p892) (*Hesperides*, 1648): "Down with the rosemary and bays, / Down with the misletoe; / Instead of holly,
now up-raise / The greener box (for show)." Box stays "until the dancing Easter day, / Or Easter's eve appear"; then
"the crisped yew"; "when yew is out, then birch comes in, / And many flowers beside, ... / To honour Whitsuntide";
then "green rushes ... and sweetest bents, / With cooler oaken boughs". So the corners can run all year off the
movable feasts:

| From | To | Corner greenery |
| --- | --- | --- |
| Christmas Eve | Candlemas Eve (1 Feb) | holly and ivy (with bays, rosemary, mistletoe as alternates) |
| Candlemas Eve | Easter Eve (E − 1) | box (Palm Sunday to Easter Eve: willow catkins, A5) |
| Easter Day | Whitsun Eve (E + 48) | yew |
| Whitsunday (E + 49) | about midsummer | birch and flowers |
| summer | Christmas Eve | rushes, bents and oak boughs (autumn: the existing gold leaf) |

This is an alternative to the present season sprigs (blossom, leaf, gold leaf, bare twig), not an addition.

### (b) Lapsed and historical festivals

**B1 Saturnalia** · 17 Dec (kept 17–23 Dec under the Empire) · Rome · lapsed with Christianisation (Macrobius
describes it c. 431). One day under the Republic, three under Augustus, later seven, the last the *Sigillaria*
(Macrobius, *Saturnalia* I.10). Business stopped, masters waited on slaves, everyone wore the *pileus* (the freed
slave's felt cap), dice were allowed in public, a mock king was chosen by lot, and people gave wax tapers (*cerei*)
and clay figurines (*sigillaria*); the cry "Io Saturnalia!". The Calendar of 354's December ([Commons](https://commons.wikimedia.org/wiki/File:Chronography_of_354_Mensis_December.png), a 17th-century copy; `ref/book-chronograph354-december.png`): a man in a short tunic beside a table with dice and a dice tower, a lit torch in his hand, a mask hung on the wall; its calendar marks 17 Dec SATVRNALIA and 25 Dec N·INVICTI·CM·XXX ([text](https://www.tertullian.org/fathers/chronography_of_354_06_calendar.htm)).
- Face: FLANK: the Calendar's dice and dice tower (9×9), a wax taper (3×13 with its flame), or the pileus (a conical cap, 9×9). LIGHTS: windows lit (the tapers). RED "SATURNALIA" / "IO SATURNALIA".

**B2 Lupercalia** · 15 Feb · Rome · ended c. 495 by Pope Gelasius I. Goats and a dog were sacrificed at the
Lupercal cave on the Palatine; the Luperci, naked but for goatskins, ran round the hill striking women with thongs
(*februa*, whence February) for fertility. Not the origin of St Valentine's Day.
- Face: FLANK: the she-wolf suckling the twins (15×10 silhouette after the Roman coin reverses, e.g. Constantine's VRBS ROMA bronzes of 330–335). RED "LUPERCALIA".

**B3 The Feast of Fools and the Boy Bishop** · 1 Jan (Fools), 6–28 Dec (Boy Bishop) · France, England · lapsed in
the 15th–16th centuries. The subdeacons' feast at the Circumcision in French cathedrals (Sens, Beauvais, Paris): a
mock bishop, the liturgy turned upside down, an ass led into church (Beauvais's Feast of the Ass, 14 Jan); condemned
by the Council of Basel (1435) and the Paris theologians (1445), gone in the 16th century. The Boy Bishop, chosen on
St Nicholas and reigning till Holy Innocents, was abolished in England by Henry VIII's proclamation of 1541 (back
briefly under Mary). The Lord of Misrule ruled Tudor courts, colleges and great houses at Christmas (Stubbes attacks
him, 1583). The fool's hood with ass's ears and bells, and the bauble.
- Face: FLANK: the fool's hood with its ears and bells (11×10). RED "FEAST OF FOOLS" (1 Jan, with Old English customs on); "CHILDERMAS" (28 Dec) with a small mitre.

**B4 Twelfth Night, Epiphany and the wassail** · 5 Jan from sunset; 6 Jan; Old Twelfth Night 17 Jan · England,
Europe · mostly lapsed; orchard wassails revived. The Twelfth cake held a bean and a pea, and whoever found them were
King and Queen of the night (Herrick, ["Twelfth Night, or King and Queen"](https://www.gutenberg.org/cache/epub/22421/pg22421-images.html#id_2.p1035)); the wassail bowl of "lamb's wool" (hot ale,
roasted apples, sugar and spice); the orchards wassailed: toast soaked in cider set in the branches for the robins,
cider poured on the roots, guns fired through the branches, the wassail song ("Wassail the trees, that they may
bear / You many a plum and many a pear": Herrick). Carhampton, Somerset, still does it on Old Twelfth Night, 17 Jan.
Epiphany: the Magi's star and their crowns (the Kalender's January shows the three kings crowned); 20+C+M+B+26 chalked over doors (Central Europe, living); the Three Kings' processions
(Spain). The Victorians moved the cake to Christmas. On the sticks: the clog's six-armed star (Plot's "Starr"); primstavs three crowns (Worm), three men (Helland) or three crosses. Hone's pastrycook's window full of Twelfth cakes (*Every-Day Book* I, cols 47–8: [cut](https://www.gutenberg.org/cache/epub/53275/images/illo0075.jpg); `ref/`); "The King drinks!" (II, cols 31–2: [scan](https://archive.org/details/b29326072_0002/page/n29/mode/1up)), the same picture as Chambers's "King of the Bean" ([vol 1 p. 63](https://archive.org/details/bookofdaysmiscel01chamuoft/page/n76/mode/1up)); the wassail-bowl headpiece, "Wass heil / Drinc heile": a two-handled footed bowl between fruiting sprigs, two birds on it (Chambers [vol 1 p. 23](https://archive.org/details/bookofdaysmiscel01chamuoft/page/n36/mode/1up); Hone II [cut](https://www.gutenberg.org/cache/epub/53276/images/illo0023.jpg); `ref/book-hone-wassail-bowl-headpiece.jpg`); the burning "Holly Tree" carried at Brough on Twelfth Night (*Table Book* I, cols 27–8: [cut](https://www.gutenberg.org/cache/epub/53277/images/illo0045.jpg)).
- Face: FLANK: the wassail bowl (13×9: a footed bowl with two handles, a garland and the apples showing) and the Twelfth-cake crown (11×7); on the Epiphany, the clog's six-armed star or the three crowns. VILLAGE (17 Jan, evening): two or three lantern points in the apple tree at dx −33; ANIM: a gun's white flash and a puff of smoke under it. RED "TWELFTH NIGHT" (5 Jan from sunset), "EPIPHANY" (6 Jan, red date), "OLD TWELFTH NIGHT" / "WASSAIL" (17 Jan).

**B5 Plough Monday and St Distaff's Day** · the first Monday after 6 Jan; 7 Jan · England (East Anglia, the East
Midlands, the North) · lapsed by the 1930s; revived by molly sides and Whittlesea's Straw Bear. The men's and the
women's return to work after Christmas. Before the Reformation a plough light burned in church. The ploughboys
("plough bullocks", "plough jags"), faces blacked, in ribbons, dragged a decorated plough from door to door with the
Bessy (a man dressed as a woman) and the Fool, collecting money, and ploughed up the doorstep of anyone who refused.
On St Distaff's Day the women went back to the spinning, the men set the flax on fire and the maids drenched them
(Herrick, ["Saint Distaff's Day, or the Morrow after Twelfth Day"](https://www.gutenberg.org/cache/epub/22421/pg22421-images.html#id_2.p1026)). The plough and the distaff, the medieval pair of
"when Adam delved and Eve span". Hone's "Plough Monday" (*Every-Day Book* I, cols 71–2: [scan](https://archive.org/details/b29326072_0001/page/n51/mode/1up), [cut](https://www.gutenberg.org/cache/epub/53275/images/illo0103.jpg); `ref/book-hone-plough-monday.jpg`): the plough hauled on ropes, the Bessy in a bonnet, the Fool in skins with a tail, a drummer. Chambers's procession ([vol 1 p. 95](https://archive.org/details/bookofdaysmiscel01chamuoft/page/n108/mode/1up)) and "Spinning with the Distaff" ([vol 1 p. 69](https://archive.org/details/bookofdaysmiscel01chamuoft/page/n82/mode/1up); [transcription](https://www.thebookofdays.com/months/jan/7.htm)).
- Face: FLANK: the plough (15×8, a swing plough: share, coulter, beam, handles) on one side and the distaff (5×15: a rod with its bulb of flax bound by a ribbon) on the other. LABOUR: the ploughboys hauling the plough in place of January's feaster. RED "PLOUGH MONDAY", "ST DISTAFF'S DAY", black dates (folk days).

**B6 Candlemas** · 2 Feb; eve 1 Feb · Europe · the church's feast lives (candles blessed); the customs lapsed in
England with the Reformation (candles forbidden by the proclamation of January 1548). The Purification of the Virgin (red letter): candles blessed
and carried in procession; the end of the old Christmas season: the greenery comes down on Candlemas Eve and the Yule
brand is relit and laid up (Herrick); a Scottish term day; *crêpes* in France; snowdrops were "Candlemas bells". The
weather lore: "If Candlemas Day be fair and bright, / Winter will have another flight; / If Candlemas Day be clouds
and rain, / Winter is gone and will not come again", which became Groundhog Day in Pennsylvania (1840s; Punxsutawney
from 1887). On the sticks: the primstav's many-branched candlestick (Helland, Worm; the Folkemuseum's drawing a three-armed one); the clog gives every Lady Day a heart instead (Plot).
- Face: LIGHTS: the church's windows lit at dusk (the candle procession). FLANK: a candle (5×13), or the primstav's candlestick of many branches (11×11). CORNERS: holly gives way to box (Herrick's rule, after A12). WEATHER: the face knows whether the day is fair; a fair Candlemas could add the rhyme's verdict to the long wording ("CANDLEMAS FAIR: MORE WINTER"). RED "CANDLEMAS", red date.

**B7 Imbolc and St Brigid's Day** · 1 Feb · Ireland, Gaelic Scotland, Man · living; an Irish public holiday since
2023. Brigid's crosses woven of rushes on the eve and hung over doors and in byres; the *Brídeóg*, a doll of the
saint carried door to door; the *brat Bríde*, a cloth left out overnight for her blessing; Imbolc, the start of
spring and the ewes' milk, in early Irish texts. The four-armed cross: a woven square centre, four arms, each tied
off in a tuft (a three-armed form too).
- Face: FLANK and CORNERS: the Brigid's cross (11×11, in the hatch khaki or gold: the colour of rushes). Draw the arms straight out from the woven square with the ties across them: a pinwheel of bent arms reads as a swastika at this size. RED "ST BRIGID'S DAY" / "IMBOLC".

**B8 Hocktide** · Hock Monday E + 8, Hock Tuesday E + 9 · England · 15th–16th centuries; suppressed under Henry
VIII, gone by c. 1700; Hungerford's Tutti Day lives. The women of a parish caught and bound the men, and the men the
women, for a forfeit paid to the church (which sex went first varied by place). Coventry's Hock Tuesday play was
played before Elizabeth at Kenilworth in 1575. At Hungerford on Hock Tuesday the tutti-men carry tutti-poles, staves
topped with a posy and a clove-studded orange, and collect a penny or a kiss at each house.
- Face: FLANK: the tutti-pole (5×15: staff, posy, orange) or a coiled rope. RED "HOCKTIDE" (Monday), "HOCK TUESDAY".

**B9 Rogationtide and beating the bounds** · Rogation Sunday E + 35, the Rogation days E + 36…38, Ascension E + 39 ·
England ("Gang days") · medieval; cut down at the Reformation (Elizabeth's Injunctions of 1559 kept the walk);
mostly lapsed in the 19th century; kept by a few parishes (Oxford's St Michael at the North Gate and St Mary the
Virgin on Ascension Day; the Tower of London every third year). The parish walked its bounds (crosses, banners and
handbells before the Reformation), prayed over the crops, read the Gospel at boundary trees (London's Gospel Oak),
beat the marks with willow wands, and bumped or whipped the boys at the stones so they would remember them.
Chambers's "Beating the Bounds" ([vol 1 p. 584](https://archive.org/details/bookofdaysmiscel01chamuoft/page/n597/mode/1up)).
- Face: VILLAGE (the Rogation days, by day): a boundary stone (3×4, cut with a cross) at the edge of a green; ANIM: four 3-px figures with wands walking along the ground. FLANK: two crossed willow wands (11×11) or the processional cross with its pennon. RED "ROGATIONTIDE" / "ROGATION SUNDAY"; "ASCENSION DAY" (red date).

**B10 May Day** · 1 May; eve 30 Apr · England, Europe · medieval on; maypoles banned by Parliament in 1644 and back
in 1660; Victorian revivals (the May Queen, ribbon plaiting); the UK's May Day bank holiday (first Monday) since
1978. Bringing in the May at dawn (hawthorn and flowers), washing in the May dew, garlands, Jack-in-the-Green (the
London sweeps, 18th–19th c.), Morris; Padstow's 'Obby 'Oss and Oxford's May Morning live. Philip Stubbes (*The
Anatomie of Abuses*, 1583) on the maypole drawn home by twenty or forty yoke of oxen with nosegays on their horns:
"covered all over with flowers and herbs, bound round about with strings from the top to the bottom, and sometimes
painted with variable colours ... with handkerchiefs and flags streaming on the top". SS Philip and James is a
red-letter day. Walpurgis Night bonfires on the eve (Sweden, Germany: living). International Workers' Day since
1890. On the sticks: the clog's bough "as set up for May Day" (Plot; a fan of strokes on his plate); the primstav's cuckoo (*Gauksmesse*) or a tree in leaf (Worm: the beech). Chambers's "Raising of the May-pole" ([vol 1 p. 572](https://archive.org/details/bookofdaysmiscel01chamuoft/page/n585/mode/1up)); Hone's "Country Maypole" (*Every-Day Book* II, cols 575–6: [scan](https://archive.org/details/b29326072_0002/page/n301/mode/1up), [cut](https://www.gutenberg.org/cache/epub/53276/images/illo0754.jpg)) and the sweeps' Jack-in-the-Green (I, cols 583–4: [cut](https://www.gutenberg.org/cache/epub/53275/images/illo0780.jpg); `ref/`).
- Face: VILLAGE (all day): a maypole on the green between the house and the church (a 1×17 pole, its spiral binding as alternate pixels, a small flag at the top, two streamers, green boughs at its foot). CORNERS: hawthorn in blossom (9×9, white five-petalled flowers on a thorny twig). FLANK: the maypole, a May garland (two crossed hoops with flowers, 11×11), or the primstav's cuckoo. RED "MAY DAY", red date; Scandinavian and German places: "WALPURGIS NIGHT" on the eve with a bonfire.

**B11 Beltane** · 1 May; eve 30 Apr · Gaelic Scotland, Ireland, Man · lapsed in the 19th century; revived
(Edinburgh's Calton Hill since 1988). Cormac's Glossary (c. 900): the druids lit two fires "with great incantations"
and drove the cattle between them against disease; bonfires on hills, the need-fire, rowan crosses over byre doors,
the Beltane bannock, May dew; the start of summer grazing.
- Face: VILLAGE (the eve, from dusk): two fires side by side on the far hill. FLANK: a rowan cross (two twigs bound crosswise with red thread, 9×9). RED "BELTANE". (When Old English customs are on too, the calendars' order decides between May Day and Beltane.)

**B12 Oak Apple Day** · 29 May · England · a public holiday from 1660 (Observance of 29th May Act) until the
Anniversary Days Observance Act 1859; kept locally (Castleton's Garland Day, Great Wishford's Grovely Rights, the
Royal Hospital Chelsea's Founder's Day, Worcester, Northampton). Charles II's birthday and his entry into London in
1660, remembering his escape in the oak at Boscobel (1651): oak sprigs or oak apples worn (or be stung with nettles:
"Shick-shack Day"), oak boughs on doors and church towers, bells. The Royal Oak with the crown in its branches is the
inn signs' and the Boscobel prints' picture (Hone, "Boscobel House", *Every-Day Book* II, cols 697–8: [cut](https://www.gutenberg.org/cache/epub/53276/images/illo0933.jpg)).
- Face: CORNERS: an oak sprig with an oak apple (9×9; the needlework library has `bk-1959-142-a-oak-leaf` and the acorns). VILLAGE: an oak bough on the church tower (a few leaf pixels at the mast's foot) and over the house door. FLANK: the Royal Oak (13×13, the tree with a small crown in its crown). RED "OAK APPLE DAY" / "ROYAL OAK DAY".

**B13 Midsummer Eve and Midsummer Day** · 23 Jun from sunset; 24 Jun (St John the Baptist, red letter; a quarter
day) · Europe · English fires lapsed (London's Midsummer Watch ended in 1539); Cornwall's hill fires revived since
1929; living in Scandinavia, Finland, the Baltic, Spain, Portugal, Brazil (where it is winter). Stow (*Survey of
London*, 1598) on the vigils: bonfires in the streets, and "every man's door being shadowed with green birch, long
fennel, St John's wort, orpin, white lilies and such like, garnished upon with garlands of beautiful flowers, had
also lamps of glass, with oil burning in them all the night". Burning wheels rolled downhill, the fires leapt, the
Swedish midsummer pole (raised on the Friday between 19 and 25 June). The Kalender's June shows the Baptist pointing to
the Lamb with its cross-banner (`ref/`), the *Agnus Dei* that also serves Easter. Hone's "Midsummer-Eve Bonfire", after a French
print (*Every-Day Book* I, cols 823–4: [scan](https://archive.org/details/b29326072_0001/page/n427/mode/1up), [cut](https://www.gutenberg.org/cache/epub/53275/images/illo1086.jpg)). On the sticks: the primstav's sun (*Jonsok*), often a hatched disc; the clog's sword (the Baptist beheaded).
- Face: VILLAGE (from sunset on the 23rd): beacons on the far hills (two or three 3×4 fires on the ridges) and a lamp at the house door; ANIM: a wheel of fire rolling down a hill. CORNERS: birch (9×9, a drooping twig) or St John's wort. FLANK: the bonfire, the fire wheel (9×9, a spoked wheel with flame tips), or the primstav's *Jonsok* sun (a hatched disc). RED "MIDSUMMER EVE" / "ST JOHN'S EVE", then "MIDSUMMER DAY" (red date). South of the equator these are midwinter fires (Brazil's *festas juninas*).

**B14 Lammas and Lughnasadh** · 1 Aug · England, Scotland, Ireland · Lammas lapsed after the Reformation (Lammas
lands still opened for grazing on the day); the Lughnasadh assemblies lapsed; Reek Sunday on Croagh Patrick (last
Sunday of July) and Puck Fair at Killorglin (10–12 Aug) live. *Hlafmæsse*, "loaf-mass": bread from the first ripe
corn blessed in church (the Anglo-Saxon Chronicle uses the name in the 10th century); a Scottish quarter day; in Ireland hilltop
gatherings, bilberries, the first fruits. "Lammas Day" is a black-letter day in the BCP. On the sticks: the primstav's key with its chain (St Peter's Chains); the clog's bow and arrows (Plot does not explain them).
- Face: FLANK: a round loaf (9×8, its top slashed) and a sheaf. CORNERS: wheat ears (9×9). RED "LAMMAS", black date.

**B15 Michaelmas** · 29 Sep (red letter; a quarter day) · England, Europe · the quarter day and the term live; the
goose and the hiring fairs lapsed (the Mop fairs survive as funfairs). Rents due, hiring fairs, the Michaelmas goose
("whoso eats goose on Michaelmas Day / shall never lack money his debts for to pay"), Michaelmas daisies; after Old
Michaelmas (10–11 Oct) no blackberries: the devil has spat on them. The Sun is in Libra at Michaelmas, and the Kalender's September sets Libra's balance beside St Michael
(`ref/`); St Michael weighs souls in the scales and spears
the dragon (Hone, "St Michael and other Archangels", *Every-Day Book* I, cols 1327–8: [cut](https://www.gutenberg.org/cache/epub/53275/images/illo1729.jpg)). On the sticks: scales on both (Worm; Davis: "common upon Cloggs"); some primstavs a horn or the archangel's head.
- Face: FLANK: the balance (13×11, a beam and two pans) or the goose (13×9). RED "MICHAELMAS", red date; "OLD MICHAELMAS" on 10 Oct with the Old Style option.

**B16 Samhain** · 1 Nov; eve 31 Oct · Gaelic Ireland, Scotland, Man · the pre-Christian feast lapsed; its customs
passed into Halloween; revived by modern pagans. In early Irish literature the great assembly of the year (the *feis*
of Tara); hilltop fires (the Scottish *samhnag*); the end of grazing; divination; guising. Hutton warns that the
"Celtic new year" and "festival of the dead" readings come from 19th-century scholars (Rhŷs, Frazer).
- Face: VILLAGE (the eve, from dusk): a single fire on the far hill. FLANK: the turnip lantern (shared with A7). RED "SAMHAIN".

**B17 Martinmas** · 11 Nov · Europe · lapsed in England ("Martlemas beef", hiring fairs, "St Martin's summer");
living in Germany, the Netherlands and Belgium (lantern processions) and as Scotland's term day. St Martin, a soldier,
cuts his cloak in two for a beggar (Chambers, [vol 2 p. 567](https://archive.org/details/bookofdaysmiscel02chamuoft/page/n578/mode/1up)); beasts were killed and salted for winter; the Martinmas goose; children's lantern
processions behind a rider as St Martin, and lantern songs on the evening of the 11th (Sint-Maarten). The same day is
Armistice Day (1918, the eleventh hour): the two minutes' silence and the poppy. On the sticks: a goose (Worm; the "Norway clogs" in Hone), a pig or a mitre (Helland); one English clog cuts a notch ending in a beak.
- Face: VILLAGE (evening): five lantern points walking slowly along the ground (the still frame keeps them as five gold points at lantern height). FLANK: the goose, or St Martin's paper lantern on its stick (7×13). RED "MARTINMAS" / "ST MARTIN", black date. Commonwealth places: "REMEMBRANCE DAY" in black at 11:00, without effects.

**B18 St Clement and St Catherine** · 23 and 25 Nov · England · lapsed in the 19th century. Old Clem, the
blacksmiths' feast (anvils fired with gunpowder; a few forges still do it); children went "Clementing" and
"Catterning" for apples and beer ("Cattern and Clemen be here, here, here, / Give us your apples and give us your
beer"); Catherine was patron of spinners and lacemakers (Bedfordshire's cattern cakes) and gives her name to the
Catherine wheel. Clement was drowned tied to an anchor; Catherine was to be broken on a spiked wheel: the Kalender of Shepherdes's November gives the pope his anchor and the crowned saint her wheel, and St Andrew his saltire (`ref/book-kalender-shepherdes-1503-november.jpg`; Hone, "St Catharine and Maxentius", from stained glass, *Every-Day Book* I, cols 1505–6: [cut](https://www.gutenberg.org/cache/epub/53275/images/illo1945.jpg)). Black-letter
days. On the sticks: the primstav's anchor or a church; the clog's pot, "from the ancient custom of going about that night, to begg drink to make merry with" (Plot). Catherine's wheel is on both sticks.
- Face: FLANK: Catherine's spiked wheel (9×9, eight spokes, spikes on the rim) and Clement's anchor (`bk-1980-63-anchor`), or the clog's pot. RED "ST CLEMENT" / "OLD CLEM", "ST CATHERINE" / "CATTERN DAY".

### (c) Festivals set by the Moon or the Sun

**C1 The solstices and equinoxes** · the Sun at 0°, 90°, 180°, 270° (§4.8) · universal. Newgrange's roof-box lets
in the midwinter sunrise (c. 3200 BC); Stonehenge's axis is solstitial; the Calendar of 354 marks 25 December, the
Julian *bruma*, N INVICTI, the birthday of the Unconquered Sun; Cusco's Inti Raymi at the June solstice (banned in
1572, restaged since 1944 on 24 June; Guaman Poma's June, 1615, shows the Inca raising a kero cup to a rayed,
faced Sun: Royal Danish Library, [p. 248](https://poma.kb.dk/permalink/2006/poma/248/en/text/), Public Domain Mark, `ref/`); China's Dongzhi; Iran's Yalda Night, the longest night (pomegranates, Hafez:
living); the French Republican year began on the autumnal equinox (1793–1805). St Thomas's Day (21 Dec, red letter)
falls on or next to the Gregorian shortest day: "St Thomas grey, St Thomas grey, / The longest night and the shortest day".
- Face: the almanac line on the day, by hemisphere: "THE LONGEST DAY" / "MIDSUMMER", "THE SHORTEST DAY" / "MIDWINTER", "EQUINOX" / "DAY AND NIGHT EQUAL", black. The ring already shows it (the night hatching at its longest or shortest). FLANK: the sun wheel (`quentel1544-wheel-15`) on the solstices. Peru: "INTI RAYMI" on 24 June, with Guaman Poma's kero cup raised to the rayed Sun as its emblem.

**C2 The Dog Days** · 3 Jul–11 Aug (the almanacs) or Sirius's first dawn rising (computed, §4.8) · ancient to the
almanacs. Egypt's year opened with Sirius's first rising before the Nile flood; Hesiod's summer "when Sirius parches
head and knees" (*Works and Days* 587); the Roman *dies caniculares*; almanac makers fixed them variously, and calendars wrote them in: the Kalender of Shepherdes has "Dies caniculares" against
6 September (`ref/book-kalender-shepherdes-1503-september.jpg`).
- Face: almanac: "DOG DAYS BEGIN", "DOG DAYS END"; on the computed morning "THE DOG STAR RISES" / "SIRIUS RISES". SKY: through the Dog Days Sirius, when up, is named "Dog Star" (or *Canicula* on the Latin plates). No emblem needed.

**C3 Passover** · 15 Nisan, from sunset on the 14th (§4.4) · living. The seder on the first night (two outside
Israel): the matzah, the seder plate, Elijah's cup; it falls at the spring full moon. The Golden Haggadah (Catalonia, c. 1320; British Library Add MS 27210) draws the matzot round: fol. 15r has the house cleaned, the round matzot and haroset handed out, Miriam's dance ([Commons](https://commons.wikimedia.org/wiki/File:Dance_of_Marian._Full_F15_from_Golden_Haggadah.jpg), PD-Art; `ref/`); the Exodus is fol. 14v ([Commons](https://upload.wikimedia.org/wikipedia/commons/f/f8/Exodus_golden_haggadah.jpg)).
- Face: LIGHTS: the house's windows lit on the seder night. FLANK: the matzah, round as the Haggadah draws it (9×9, a disc pricked in rows), or the cup (7×11). RED "PASSOVER" / "PESACH"; the eve "SEDER NIGHT". The Moon is full or nearly, as it should be.

**C4 Rosh Hashanah and Yom Kippur** · 1–2 Tishrei and 10 Tishrei, from sunset · living. The shofar (ram's horn)
blown; apples and honey; *tashlich* at running water; Yom Kippur a fast, ended by the shofar.
- Face: FLANK: the shofar (13×6, a curved horn). RED "ROSH HASHANAH", long form with the year ("NEW YEAR 5787" in 2026: y = G + 3761). Yom Kippur: "YOM KIPPUR" in black, no emblem.

**C5 Sukkot** · 15 Tishrei, seven days, from sunset · living. The booth (*sukkah*) roofed with cut branches laid so
that the large stars can be seen through them (Shulchan Arukh, Orach Chaim 631:3); the lulav (palm frond with myrtle
and willow) and the etrog (citron).
- Face: VILLAGE: a small booth beside the house (7×6: posts and a ragged leafy roof, the window's stars above it). FLANK: the lulav and etrog (a 3×15 frond and a 4×5 citron). RED "SUKKOT".

**C6 Hanukkah** · 25 Kislev, eight nights, the first light the evening before · living. The lamp of eight lights and
the shammash, set in a window facing the street to make the miracle known (Talmud, Shabbat 21b); one more light each
night. The Baraffael family's silver lamp (Rome, 1773–75; the Met, CC0, [751313](https://www.metmuseum.org/art/collection/search/751313); `ref/`): a back plate embossed with a menorah over a row of eight oil spouts, the servant light hung at the side.
- Face: FLANK: the lamp with tonight's lights (15×11: eight short branches and a taller shammash; on night n, n flames and the shammash lit in gold): the one emblem the face computes. LIGHTS: one light in the house's window from dusk. RED "HANUKKAH"; long "HANUKKAH, THE THIRD NIGHT".

**C7 Chinese New Year** (Spring Festival) · month 1, day 1 (§4.5) · living (Vietnam's Tết in UTC+7, Korea's Seollal
in UTC+9). The reunion dinner on the eve; red couplets and the character *fu* upside down on the doors; door gods;
firecrackers against the Nian; red envelopes; lanterns; lion dances; the year's animal. Pictures: the Qing court's *Activities of the Twelve Months* begins with the first month's lanterns and fireworks (C8); a red string of firecrackers is the commonest New Year sign.
- Face: VILLAGE: a pair of red lanterns at the house door; ANIM: firecrackers at midnight (small red and white pops with smoke at the foot of the house). FLANK: the year's animal (twelve 13×11 silhouettes, one a year) or a lantern (7×9). RED "CHINESE NEW YEAR" / "SPRING FESTIVAL"; long "YEAR OF THE HORSE".

**C8 The Lantern Festival** (Yuanxiao) · month 1, day 15 · living. The first full moon of the year: lanterns hung
and carried, riddles written on them, sweet dumplings, dragon dances; the end of the New Year. The Qing court's *Activities of the Twelve Months* (清院畫十二月令圖, National Palace Museum, Taipei; twelve hanging scrolls, early Qianlong; on Commons as `清畫院畫十二月月令圖N月_軸.jpg`, PD-Art): the first month (故畫003106) has lanterns, fireworks and a great lantern on scaffolding; `ref/` has the fifth month's dragon boats. The Met's lantern panel (44119) is CC0.
- Face: VILLAGE (evening): four red lanterns (2×3 each) on a line between the house and the tree at dx −33. The full Moon is up. FLANK: a lantern. RED "LANTERN FESTIVAL" / "YUANXIAO".

**C9 Qixi and Tanabata** · month 7, day 7 (China, August); 7 Jul in most of Japan, 7 Aug in some places (Sendai) ·
living. The Weaver Girl (Vega) and the Cowherd (Altair), parted by the Silver River (the Milky Way), meet once a year
on a bridge of magpies (Han poetry, the *Nineteen Old Poems*). Tanabata: wishes written on paper strips (*tanzaku*)
and tied to bamboo. Hiroshige, "The Tanabata Festival in the Flourishing City" (*One Hundred Famous Views of Edo*, 1857; the Met, CC0, [36541](https://www.metmuseum.org/art/collection/search/36541); `ref/`): bamboo poles over the roofs hung with paper slips, streamers, a gourd, a fish. The Qing court's seventh month (故畫003112) has needle-threading by moonlight and magpies.
- Face: SKY (night): Vega and Altair named "Weaver" and "Cowherd" in place of their names, and a faint bridge of five to seven magpie dots arched across the Milky Way between them: the most natural effect a sky chart can have. VILLAGE (Tanabata): a bamboo pole rising above the house's roof, its leafy top bent over, two or three paper strips hanging from it, as Hiroshige's poles rise over the roofs of Edo. FLANK: bamboo with paper strips (5×15) or a magpie (11×7). RED "QIXI" / "TANABATA"; long "THE WEAVER MEETS THE COWHERD".

**C10 Mid-Autumn, Tsukimi and the Harvest Moon** · month 8, day 15 (China, Vietnam; Korea's Chuseok); Japan's
*jūgoya* on the same day by its old calendar (UTC+9) and *jūsan'ya* on the 13th of the 9th month; the English Harvest
Moon, the full moon nearest the September equinox · living. Moon-viewing; mooncakes and lanterns; Chang'e and the jade
rabbit pounding the elixir in the Moon (in Japan the rabbit pounds rice cakes); offerings of *susuki* grass and a
pyramid of fifteen *dango*; the Harvest Moon that lit the reapers home. Utamaro, "Moon-Viewing Party" (*Ehon shiki no hana*, 1801; Art Institute of Chicago, CC0, [34789](https://www.artic.edu/artworks/34789); `ref/`): susuki in a vase on a balcony under a plain full moon. The Met's panel of the moon goddess with the jade rabbits (CC0, [44090](https://www.metmuseum.org/art/collection/search/44090)); the Qing court's eighth month ([Commons](https://commons.wikimedia.org/wiki/File:清畫院畫十二月月令圖八月_軸.jpg)): the moon a small globe over a terrace, a cassia tree.
- Face: SKY: the full Moon's face (drawn on every full Moon) gives way for the night to the rabbit in the Moon (a 5–7 px hare in the maria, where East Asian eyes see it). FLANK: *susuki* and the *dango* stand (13×13; Tsukimi), or a mooncake (9×9, a round with a stamped pattern). RED "MID-AUTUMN" / "MOON FESTIVAL", "TSUKIMI", or "HARVEST MOON", by calendar (Chinese, Japan, the sky's year).

**C11 Diwali** · the amavasya ending Ashvin (§4.6); five days · living (Hindu, Jain, Sikh; Nepal's Tihar). Rows of
clay lamps (*diyas*) on thresholds, sills and parapets; *rangoli* at the door; Lakshmi worshipped at dusk; fireworks
(modern). "Royal Women Celebrating Diwali" (Lucknow, c. 1760; Cleveland Museum of Art, CC0, [1971.82](https://clevelandart.org/art/1971.82); `ref/`): rows of lamps, sparklers, fireworks.
- Face: VILLAGE (evening): single gold lamp pixels in a row along the house's eaves and sills and along the ground before it. FLANK: a diya (7×5, a shallow clay lamp with its flame). RED "DIWALI" / "DEEPAVALI". Fireworks optional.

**C12 Holi** · the Phalguna full moon (§4.6) · living. Holika Dahan, the bonfire on the full-moon evening; Holi the
next morning, with coloured powders (*gulal*) and squirted coloured water; Krishna and Radha playing Holi in Pahari
and Rajput painting. "Krishna celebrates Holi" (Pahari, c. 1770; Cleveland, CC0, [2018.104](https://clevelandart.org/art/2018.104); `ref/`): brass syringes (*pichkari*) spraying jets of colour.
- Face: VILLAGE (the eve): the Holika bonfire on the green (FIRE). Holi: one soft cloud of stipple in two colours (red and gold) drifting past the house like smoke; anything more is garish. FLANK: the bonfire, or a puff of powder (11×9 dots). RED "HOLIKA DAHAN" (eve), "HOLI".

**C13 Ramadan and the Eids** · Islamic months by the crescent (§4.7) · living. The month begins at the first sight
of the new crescent (*hilal*); fasting from dawn to sunset; Laylat al-Qadr; Eid al-Fitr at the next crescent; Eid
al-Adha on 10 Dhu al-Hijja. Lanterns (*fanous*) in Egypt since Fatimid times; lamps hung on minarets.
Elihu Vedder, "The End of Ramazan" (1883–84; Smithsonian American Art Museum, CC0, [1978.108.48](https://americanart.si.edu/collections/search/artwork/?id=25631)): a thin crescent seen through an arch. Pieter Coecke van Aelst, "Festival of the New Moon" (woodcut, 1553; the Met, CC0, 422768).
- Face: SKY: on the evening the new crescent may first be seen, "THE NEW MOON MAY BE SEEN" (in any month: it is sky news). Through Ramadan the sunset line can read "IFTAR" for "SUNSET", and before dawn the time of dawn (methods differ: the Sun at about −15° to −18°). FLANK: the crescent with a star, or the *fanous* (7×11). RED "RAMADAN" (its first day), "EID AL-FITR", "EID AL-ADHA".

**C14 Nowruz** · the March equinox, by the Tehran noon rule (§4.8) · living (Iran, Central Asia, the Caucasus,
Kurdistan, Afghanistan). The *haft-sin* table of seven things whose names begin with s (sprouted wheat, *samanu*,
oleaster, garlic, apples, sumac, vinegar), with a mirror, candles, painted eggs and goldfish; *Chaharshanbe Suri*,
jumping over small fires on the eve of the year's last Wednesday; *Sizdah Bedar*, the thirteenth day out of doors.
No public-domain picture of the haft-sin or the fires was found (a Qajar Nowruz still life with narcissus is on Commons).
- Face: VILLAGE: on Chaharshanbe Suri three small fires in a row on the green. FLANK: a dish of sprouted wheat (11×9, tied with a ribbon). RED "NOWRUZ"; long with the year ("NOWRUZ 1405" in 2026: the Solar Hijri year is G − 621 from Nowruz).

**C15 Matariki** · New Zealand's public holiday (set by law) and the Pleiades' first dawn rising (§4.8) ·
living, revived. The Māori year begins with Matariki rising before dawn in midwinter; its stars are read for the
coming year, the year's dead remembered, kites flown, food shared. A public holiday since 2022. Te Ara ([Matariki – Māori New Year](https://teara.govt.nz/en/matariki-maori-new-year/page-1), Paul Meredith; text CC BY-NC): the cluster rises "low on the north-eastern horizon … just before dawn in midwinter"; iwi count seven or nine stars (Matariki, Waitī, Waitā, Tupuānuku, Tupuārangi, Waipunarangi, Ururangi, Pōhutukawa, Hiwa-i-te-rangi); clear bright stars foretold a good season, hazy ones a cold winter; some iwi watch Puanga (Rigel) instead. No public-domain period picture.
- Face: SKY (before dawn): the Pleiades named MATARIKI when up (or Rigel named PUANGA, for the iwi who keep it). Almanac on the computed first-sighting morning "MATARIKI RISES", and on the holiday "MATARIKI". FLANK: the cluster itself (9×7, its stars as dots in their pattern).

**C16 Makar Sankranti and the kite days** · the Sun's entry into sidereal Capricorn (§4.6) · living. Kites over
Gujarat (*Uttarayan*) and Rajasthan; sesame and jaggery sweets; Lohri bonfires the night before (Punjab); Pongal
(Tamil Nadu). Kites also fly at Qingming (China), on Good Friday (Bermuda), at Matariki.
- Face: WINDOW (by day): one to three small diamond kites (5×5 with a three-pixel tail) low over the village. FLANK: a kite. RED "MAKAR SANKRANTI" / "UTTARAYAN".

## 4. Date code

Everything below runs on the watch from the date, the place and the ephemeris it already has (Meeus's Sun and Moon,
`plan_astro.c`). The lunar and solar rules were tested for this file in Python against the prototype's own
`proto/lunar.py` (scratch scripts, not in the repo); the results are quoted with each rule. A float32 Julian Date
steps by about 0.25 day and float32 days since J2000 by about 84 s, so keep an integer day plus a fraction (the
face already keeps its large angles as integer fractions of a turn); the new moons need about a minute, the solar
terms about ten.

### 4.1 Civil rules

Weekday from a day count (Hinnant's `days_from_civil`). `nth(y, m, dow, n)`: the first `dow` on or after the 1st,
plus 7(n − 1); `last(y, m, dow)`: back from the month's last day; `after(d, dow)`: the first `dow` strictly after d.

| Rule | Days it gives | 2026 | 2027 |
| --- | --- | --- | --- |
| first Monday after 6 Jan | Plough Monday | 12 Jan | 11 Jan |
| last Tuesday of January | Up Helly Aa, Lerwick | 27 Jan | 26 Jan |
| first Monday of Feb, or 1 Feb if a Friday | St Brigid's Day holiday, Ireland (since 2023) | 2 Feb | 1 Feb |
| third Monday of February | Washington's Birthday (since 1971; 22 Feb before) | 16 Feb | 15 Feb |
| first Monday of May | UK May Day bank holiday (since 1978) | 4 May | 3 May |
| last Monday of May | Memorial Day (since 1971; 30 May before) | 25 May | 31 May |
| Friday between 19 and 25 Jun | Swedish Midsummer Eve | 19 Jun | 25 Jun |
| first Monday of September | Labor Day (US), Labour Day (Canada) | 7 Sep | 6 Sep |
| second Monday of October | Canadian Thanksgiving (since 1957) | 12 Oct | 11 Oct |
| last Thursday of October | Punkie Night, Hinton St George | 29 Oct | 28 Oct |
| second Sunday of November | Remembrance Sunday (UK) | 8 Nov | 14 Nov |
| fourth Thursday of November | US Thanksgiving (fixed by Congress in 1941) | 26 Nov | 25 Nov |
| Sunday after 26 Nov | Advent Sunday | 29 Nov | 28 Nov |

### 4.2 Easter and the movable feasts

Western Easter is the Sunday after the ecclesiastical full moon falling on or after 21 March. That full moon is a
table value (the epact), not the real Moon, and can differ from the face's Moon by a day or two. The Anonymous
Gregorian algorithm (Meeus, *Astronomical Algorithms*, ch. 8), integers only, any Gregorian year:

```
a = Y % 19;  b = Y / 100;  c = Y % 100;  d = b / 4;  e = b % 4;  f = (b + 8) / 25;  g = (b - f + 1) / 3
h = (19a + b - d - g + 15) % 30;  i = c / 4;  k = c % 4;  l = (32 + 2e + 2i - h - k) % 7
m = (a + 11h + 22l) / 451;  n = h + l - 7m + 114;  month = n / 31;  day = n % 31 + 1
```

Orthodox Easter: the Julian computus, then 13 days added (valid 1900–2099):

```
a = Y % 4;  b = Y % 7;  c = Y % 19;  d = (19c + 15) % 30;  e = (2a + 4b - d + 34) % 7
n = d + e + 114;  Julian (n / 31, n % 31 + 1);  Gregorian = Julian + 13 days
```

(In general the Julian-to-Gregorian offset is Y/100 − Y/400 − 2 days, as `proto/feasts.py` has it.)

Tested: Western 2024–2030 = 31 Mar, 20 Apr, 5 Apr, 28 Mar, 16 Apr, 1 Apr, 21 Apr; Orthodox = 5 May, 20 Apr, 12 Apr,
2 May, 16 Apr, 8 Apr, 28 Apr. All correct.

| Offset from E | Day | 2026 |
| --- | --- | --- |
| −47 | Shrove Tuesday (Pancake Day, Mardi Gras) | 17 Feb |
| −46 | Ash Wednesday | 18 Feb |
| −21 | Mothering Sunday (UK; Laetare) | 15 Mar |
| −7 | Palm Sunday | 29 Mar |
| −3, −2, −1 | Maundy Thursday, Good Friday, Easter Eve | 2–4 Apr |
| 0, +1 | Easter Day, Easter Monday | 5–6 Apr |
| +8, +9 | Hock Monday, Hock Tuesday (the Monday and Tuesday of the second week after Easter; Hungerford's Tutti Day is the Tuesday) | 13–14 Apr |
| +35 | Rogation Sunday; Rogation days +36…+38 | 10 May |
| +39 | Ascension Day (Holy Thursday) | 14 May |
| +49, +50 | Whitsunday (Pentecost), Whit Monday | 24–25 May |
| +56, +60 | Trinity Sunday, Corpus Christi | 31 May, 4 Jun |

### 4.3 Old Style

Customs that kept their day across the 1752 change (2 September was followed by 14 September) now fall 11 days late:
Old New Year's Eve 11 Jan (Burghead's Clavie), Old Twelfth Night 17 Jan (the Carhampton wassail), Old Candlemas 13 Feb,
Old Lady Day 5 Apr (6 Apr after 1800's dropped leap day: the UK tax year still begins then), Old May Day 12 May, Old
Midsummer 5 Jul, Old Lammas 12 Aug, Old Michaelmas 10 or 11 Oct (after which the devil spoils the blackberries), Old
Martinmas 22 Nov, Old Christmas 5 or 6 Jan (when the Glastonbury Thorn was watched for flowers). A true Julian date
is 13 days behind from 1 Mar 1900 to 28 Feb 2100 (Orthodox Christmas 7 Jan; the "Old New Year" of Russia and Serbia,
14 Jan). So: a folk custom's own day (usually +11), a Julian date +13.

### 4.4 Hebrew calendar (exact; integers only)

```
leap(y)          = (7y + 1) % 19 < 7
elapsed(y)       : months = (235y - 234) / 19;  parts = 12084 + 13753 * months
                   day = 29 * months + parts / 25920;  if (3 * (day + 1)) % 7 < 3: day += 1
delay(y)         = 2 if elapsed(y+1) - elapsed(y) == 356;  1 if elapsed(y) - elapsed(y-1) == 382;  else 0
rosh_hashanah(y) = R.D. -1373427 + elapsed(y) + delay(y)      (R.D. 1 = 1 Jan AD 1, proleptic Gregorian)
```

(After Dershowitz and Reingold, *Calendrical Calculations*: the molad of Tishrei and the four postponements.) The
Hebrew year beginning in the autumn of Gregorian year G is y = G + 3761. With RH = rosh_hashanah(y) and
L = rosh_hashanah(y + 1) − RH:
- Yom Kippur = RH + 9; Sukkot = RH + 14 (seven days; Shemini Atzeret RH + 21);
- Hanukkah (25 Kislev) = RH + 54 + H, where H = 30 if L is 355 or 385, else 29; the first light the evening before; night n has n lights;
- Passover (15 Nisan) of year G = rosh_hashanah(G + 3761) − 163; Purim (14 Adar, or Adar II in a leap year) = Passover − 30.

Today's Hebrew date (a converter): find y with rosh_hashanah(y) ≤ today < rosh_hashanah(y + 1), then walk the
months from Tishrei: Tishrei 30, Heshvan 29 (30 if L is 355 or 385), Kislev 30 (29 if L is 353 or 383), Tevet 29,
Shevat 30, Adar I 30 (leap years only), Adar (Adar II in a leap year) 29, Nisan 30, Iyar 29, Sivan 30, Tammuz 29, Av
30, Elul 29. The other days of the Hebrew calendar in §6, as offsets: Simchat Torah RH + 22 (RH + 21 in Israel, with
Shemini Atzeret); Tu BiShvat (15 Shevat) Passover − 59, or − 89 in a leap year; Lag BaOmer (18 Iyar, bonfires)
Passover + 33; Shavuot (6 Sivan) Passover + 50; Tisha B'Av (9 Av) Passover + 112, a day later if that is a Saturday.
For 2026: Tu BiShvat 2 Feb, Lag BaOmer 5 May, Shavuot 22 May, Tisha B'Av 23 Jul.

Every day begins at the previous sunset, so a Jewish feast's effects start at local sunset on the eve (the face knows
it). Tested 2024–2028: Rosh Hashanah 3 Oct 2024, 23 Sep 2025, 12 Sep 2026, 2 Oct 2027, 21 Sep 2028; Passover 23 Apr,
13 Apr, 2 Apr, 22 Apr, 11 Apr; Hanukkah 26 Dec, 15 Dec, 5 Dec, 25 Dec, 13 Dec; Purim 24 Mar, 14 Mar, 3 Mar, 23 Mar,
12 Mar. All correct.

### 4.5 Chinese lunisolar calendar

The rules (true Sun and Moon since 1645; UTC+8 since 1929; published as GB/T 33661-2017):
1. A month begins on the civil day, in UTC+8, that contains the astronomical new moon.
2. The 24 solar terms are the Sun's apparent longitude at multiples of 15°; the 12 principal terms (*zhongqi*) are the multiples of 30°.
3. The month containing the December solstice (270°) is month 11.
4. If 13 months begin from one month 11 up to (not including) the next, the first of them that contains no principal term is the leap month, and repeats the number before it.
5. Otherwise month n contains principal term n: month 1 holds 330° (*Yushui*), month 5 the June solstice, month 7 150°, month 8 the September equinox, month 9 210°.

As code (after Calendrical Calculations; all dates are civil days in UTC+8):

```
starts(y)   = days of the new moons from Nov of year y-1 to Mar of year y+1
terms(y)    = days on which the Sun's apparent longitude passes a multiple of 30 deg (principal terms)
m11(y)      = the last month start on or before the day of the December solstice (270 deg) of year y
months      = [s in starts : m11(y-1) <= s < m11(y)]                 # 12, or 13 in a leap sui
leap        = none if len(months) == 12, else the first s in months[1:] with no principal term in [s, next start)
number      : months[0] is 11; each later start is the previous number + 1 (12 wraps to 1), except that the
              leap month repeats the previous number
New Year(y) = the start numbered 1;  a date's (month, leap?, day) = (number, s == leap, days since s + 1)
```

Days: Lantern Festival 1/15 (New Year + 14), Dragon Boat 5/5, Qixi 7/7, Mid-Autumn 8/15, Double Ninth 9/9, always in
the regular month, never the leap one. Qingming is the UTC+8 day the Sun reaches 15°; Dongzhi the day it reaches 270°
(in 2026 that is 22 Dec in Beijing, 21 Dec in UT). The year's animal, for the year whose New Year falls in Gregorian
year G: rat, ox, tiger, rabbit, dragon, snake, horse, goat, monkey, rooster, dog, pig at index (G − 4) % 12 (2026 horse).

Checks:
- Against the Hong Kong Observatory's tables for every year 1901–2100 (by a helper, with Meeus ch. 49 new moons and JPL Horizons terms): the full rule reproduces every leap month, and the new moons agree on all 2474 month starts but three before 1929 and two that turn on ΔT. The prototype's own ephemeris (`proto/lunar.py`) gives the same New Years for every year checked, the leap 11th month of 2033 included.
- The short cuts: "the second new moon after the December solstice" fails only for 2034 (it gives 20 Jan; 19 Feb is right). "The month holding 330°", which is `proto/feasts.py`'s `chinese_month_start(year, 330)`, fails for 1985, 2034 and 2053 (it gives 21 Jan, 20 Jan, 20 Jan; the right dates are 20 Feb, 19 Feb, 19 Feb). "Month m holds its principal term" never fails for the Dragon Boat or Qixi, but fails for Mid-Autumn and the Double Ninth in 2033 (7 Oct and 31 Oct; 8 Sep and 1 Oct are right). So run the full rule: about 14 new moons and 13 terms a year.
- Ranges over 1901–2100, for sanity checks: New Year 21 Jan–20 Feb, Lantern 4 Feb–6 Mar, Dragon Boat 27 May–26 Jun, Qixi 31 Jul–30 Aug, Mid-Autumn 7 Sep–8 Oct, Double Ninth 1 Oct–1 Nov.

| HKO | 2024 | 2025 | 2026 | 2027 | 2028 |
| --- | --- | --- | --- | --- | --- |
| New Year | 10 Feb | 29 Jan | 17 Feb | 6 Feb | 26 Jan |
| Lantern Festival | 24 Feb | 12 Feb | 3 Mar | 20 Feb | 9 Feb |
| Qingming | 4 Apr | 4 Apr | 5 Apr | 5 Apr | 4 Apr |
| Dragon Boat | 10 Jun | 31 May | 19 Jun | 9 Jun | 28 May (a leap 5th month follows) |
| Qixi | 10 Aug | 29 Aug (after a leap 6th month) | 19 Aug | 8 Aug | 26 Aug |
| Mid-Autumn | 17 Sep | 6 Oct | 25 Sep | 15 Sep | 3 Oct |
| Double Ninth | 11 Oct | 29 Oct | 18 Oct | 8 Oct | 26 Oct |
| Dongzhi | 21 Dec | 21 Dec | 22 Dec | 22 Dec | 21 Dec |

Precision: a new moon falls within a minute of Beijing midnight at 2 of the 2474 month starts (0.08%), within 5
minutes at 0.57%, within 10 at 1.5%. The fragile ones ahead: the 9th month of 2057 (HKO 28 Sep; with ΔT ≈ 80 s the new
moon comes at 00:00:29 on the 29th: the Double Ninth on 6 or 7 Oct), the 8th of 2089 (23:59:09 on 4 Sep), the 7th of
2097 (Qixi on 13 or 14 Aug); and HKO dates the 2084 March equinox 19 Mar where it computes to 00:00:44 on the 20th. The
short solar theory in `proto/lunar.py` (Meeus ch. 25, "about 0.01°") put the 2024–2026 March equinoxes 4 to 12 minutes
early against the published times: use the full solar series for the terms (or Meeus ch. 27's equinox and solstice
formulae), test against the HKO tables as the certificate, and keep a table of month starts (2 bytes a year) as the
fallback.

The same calendar in other zones: Vietnam reckons in UTC+7 (Tết fell a day before China's New Year in 2007, 17 and
18 Feb, and a month before it in 1985), Korea in UTC+9 (Seollal 2027 is 7 Feb, a day after China's New Year: the new
moon came at 23:56 Beijing time on 6 Feb). Japan's old-calendar days follow the National Astronomical Observatory's
rules in JST: *jūgoya*, the 15th day of the lunation holding the September equinox (2033 ambiguous; by the same rules a
day after China's Mid-Autumn in 2040); *jūsan'ya*, the 13th day of the lunation holding 210° (23 Oct 2026, a day after
the Chinese reckoning: the new moon came at 23:50 Beijing time on 10 Oct); traditional Tanabata, the 7th day from the
JST new moon on or before the day the Sun reaches 150° (the same as Qixi in 2024–2028); Sendai keeps its Tanabata on
6–8 Aug. So the zone is a parameter of the rule, chosen by the tradition, not by the watch's own zone.

### 4.6 Hindu lunisolar dates (amanta reckoning)

- Sidereal Sun = apparent tropical longitude − ayanamsa. Lahiri's ayanamsa, fitted to Drik Panchang's: A(T) = 23.8638° + 1.396971° T + 0.000308° T² (T in Julian centuries from J2000; 24.2242° on 20 Oct 2025); with a Meeus Sun it reproduces Drik's Makar Sankranti moments to ±4 min.
- A *sankranti* is the Sun's entry into a sidereal sign (a multiple of 30°). An amanta month runs from new moon to new moon and is named for the sankranti it contains: Chaitra 0° (Mesha), Vaishakha 30°, Jyeshtha 60°, Ashadha 90°, Shravana 120°, Bhadrapada 150°, Ashvin 180°, Kartika 210°, Margashirsha 240°, Pausha 270°, Magha 300°, Phalguna 330°. A month with no sankranti is *adhika* (leap) and borrows the next name, so "the month containing sankranti k" is always the regular one.
- A *tithi* is a thirtieth of the lunar month: tithi = floor(elongation / 12°) + 1. Amavasya (new moon) is 348–360°; purnima (full moon) 168–180°.
- **Diwali** (Lakshmi Puja): the new moon that ends Ashvin, the amanta month containing the Sun's entry into sidereal Libra (about 17 Oct). So in a year with a leap (adhika) Ashvin it is November's new moon, not October's. The day: the IST date whose *pradosh* (sunset to a fifth of the night after it, about 2 h 24 min, at Delhi) overlaps the amavasya; if two evenings do, the later when the amavasya lasts at least one *ghati* (24 min) into its pradosh, else the earlier. Tested over 1990–2060 against 17 known years (1993, 2001, 2003, 2012, 2013, 2015–2026): all right, including 1 Nov 2024 (some almanacs kept 31 Oct) and 20 Oct 2025; it gives 29 Oct 2027, 17 Oct 2028. In two of the 71 years (2046, 2055) no evening's pradosh touches the amavasya: take the evening before the new moon.
  - `proto/feasts.py`'s `diwali()` (the first new moon after 15 October) takes October's new moon in the adhika years 1993, 2001, 2012, 2020, 2031, 2039, 2050, 2058; the real dates for the first four were 13 Nov 1993, 14 Nov 2001, 13 Nov 2012, 14 Nov 2020 (it gives 16 Oct 2020).
  - As code:

    ```
    ayanamsa(t)  = 23.8638 + 1.396971 T + 0.000308 T^2 deg, T = (JD(t) - 2451545) / 36525   # Lahiri (fit)
    tula         = the moment (Sun's apparent longitude - ayanamsa) passes 180 deg  # about 17 Oct
    nm           = the first new moon after tula                                    # Ashvin ends here
    a0           = the moment before nm when the elongation (Moon - Sun) passes 348 deg  # amavasya begins
    pradosh(d)   = [sunset at Delhi (28.61 N, 77.21 E) on IST day d, + (night length) / 5]   # h0 = -0.833 deg
    overlap(d)   = length of pradosh(d) ∩ [a0, nm], for the IST days d around nm
    days         = [d : overlap(d) > 0]
    Lakshmi Puja = none of them: the IST day before nm's;  one: it;
                   two: the later if its overlap >= 24 min, else the earlier
    ```

  - Test years (Lakshmi Puja): 13 Nov 1993, 14 Nov 2001, 25 Oct 2003, 13 Nov 2012, 3 Nov 2013, 11 Nov 2015, 30 Oct 2016, 19 Oct 2017, 7 Nov 2018, 27 Oct 2019, 14 Nov 2020, 4 Nov 2021, 24 Oct 2022, 12 Nov 2023, 1 Nov 2024, 20 Oct 2025, 8 Nov 2026; computed 29 Oct 2027, 17 Oct 2028. Drik Panchang (New Delhi) gives the same for 2024–2028 (the government's 2024 holiday was 31 Oct).
  - Short cut: the IST date of (that new moon − 18 h) is wrong in 3 years of 1900–2100 (1963, 2037, 2056). The place matters: worked for local sunsets, New York's date differs from Delhi's in 39 years of 2000–2099 and Mumbai's in 5 (in 2024 Delhi kept 1 Nov, Mumbai 31 Oct). Diaspora almanacs use the local evening, so offer "India" or "here". Singapore and Tamil Nadu keep Deepavali on Naraka Chaturdashi, often the day before (Singapore 28 Oct 2027).
- **Holi**: the full moon of Phalguna, the month containing the Sun's entry into sidereal Pisces (about 14 Mar). Holika Dahan (the bonfire) is that evening and Holi (the colours) the next day. The almanacs' rule (Drik Panchang): purnima at *pradosh*, avoiding *Bhadra* (the first half of the tithi): after Bhadra ends if it ends before midnight, otherwise in its tail (*Bhadra Punchha*), never in its head; the later day if purnima reaches pradosh on both; and when purnima ends before sunset but has covered at least 7/8 of the day, that evening (2023, 2026). Short cut: the IST date of (the full moon − 17 h): wrong in one year of 1900–2100 (1928) against the reconstructed rule, and right for 2015–2028 against the observed and Drik dates (Holika Dahan 24 Mar 2024, 13 Mar 2025, 3 Mar 2026, 21 Mar 2027, 10 Mar 2028). ("The full moon before the Sun enters sidereal Aries" is wrong in 109 years of 201.)
- **Makar Sankranti**: the Sun's entry into sidereal Capricorn (270°): the IST date, or the next day if it comes after sunset at Delhi ("all Punya Kaal activities are postponed till next day Sunrise": Drik); a moment after midnight counts for that date. 15 Jan 2024 (02:54 IST), 14 Jan 2025 (09:03), 14 Jan 2026 (15:13), 15 Jan 2027 (21:14 on the 14th), 15 Jan 2028 (03:26). Short cut, within ±7.4 min for 2000–2100: 2025-01-14 09:03 IST + 365.256363 days × (year − 2025), the sidereal year.
- **Today's Hindu date** (a converter): the amanta month is named by the sankranti inside it (adhika if none: "Adhika" + the next month's name); the paksha is *shukla* (waxing, tithis 1–15) or *krishna* (waning, 16–30, counted 1–15 again); the day's tithi is the one in force at local sunrise (*udaya tithi*). Most festivals keep that rule; the exceptions are Diwali and Holika Dahan (at dusk), Janmashtami and Maha Shivaratri (at midnight), Rama Navami and Ganesh Chaturthi (at midday). The other days of the Hindu calendar in §6, by (amanta month, tithi): Vasant Panchami (Magha, shukla 5), Maha Shivaratri (Magha, krishna 14), Ugadi and Gudi Padwa, the new year in the Deccan (Chaitra, shukla 1), Rama Navami (Chaitra, shukla 9), Raksha Bandhan (Shravana, purnima), Janmashtami (Shravana, krishna 8), Ganesh Chaturthi (Bhadrapada, shukla 4), Navaratri (Ashvin, shukla 1–9) and Dussehra (Ashvin, shukla 10), Kartik Purnima (Kartika, purnima). Regions differ (the north counts months purnimanta, full moon to full moon, so its krishna fortnights carry the next month's name).

### 4.7 Islamic months (the crescent)

Three ways, from closest to what is kept to roughest:
1. **Umm al-Qura**, Saudi Arabia's computed calendar, in its rule since AH 1423 (2002): "If on the 29th day of the lunar month … the geocentric conjunction occurs before sunset [and] the moon sets after the sun, then the next day is the first day of the new lunar month … Otherwise … 30 days", reckoned for the Kaaba (21.4225° N, 39.8262° E) ([van Gent](https://webspace.science.uu.nl/~gent0113/islam/ummalqura_rules.htm); earlier versions differed). Implemented here with the face's ephemeris (the Moon's topocentric centre above −0.83° at sunset), it gave every 2024–2026 start checked: 1 Ramadan 11 Mar 2024, 1 Mar 2025, 18 Feb 2026; Eid al-Fitr 10 Apr 2024, 30 Mar 2025, 20 Mar 2026; Eid al-Adha 16 Jun 2024, 6 Jun 2025, 27 May 2026; 1 Muharram 7 Jul 2024, 26 Jun 2025 ([van Gent's tables](https://webspace.science.uu.nl/~gent0113/islam/ummalqura_principal.htm)). A helper's version (Meeus Moon, truncated VSOP87 Sun) matched 932 of 935 official month starts for AH 1423–1500; the three misses had moonset within 7 s of sunset (1.4% of months are decided by under 30 s; a table of month lengths, 2 bytes a year, is the safe fallback). The announced Saudi dates rest on sightings accepted by the Supreme Court, but matched Umm al-Qura in 65 of 78 cases over 2001–2026 (every miss one day) and in all 24 since 2019. Next: 1 Ramadan 8 Feb 2027 and 28 Jan 2028; Eid al-Fitr 9 Mar 2027, 26 Feb 2028; Eid al-Adha 16 May 2027, 5 May 2028. Many countries keep their own sighting, often a day later (Eid al-Fitr 2025: 30 Mar in the Gulf and Turkey, 31 Mar in Egypt, Morocco, Indonesia, Pakistan, India); North America's FCNA/ISNA uses a computed rule (elongation ≥ 8° and altitude ≥ 5° somewhere on Earth), as does Turkey's Diyanet (the 2016 Istanbul rule).
2. **Local first visibility** (Yallop 1997, HM Nautical Almanac Office Technical Note 69): at the best time (sunset + 4/9 of the Moon's lag after the Sun), q = (ARCV − (11.8371 − 6.3226 W + 0.7319 W² − 0.1018 W³)) / 10, with ARCV the airless topocentric altitude of the Moon minus the Sun's (degrees) and W the topocentric crescent width (arcminutes). q > +0.216 easily seen; > −0.014 seen in perfect conditions; > −0.160 may need optical aid to find; > −0.232 needs optical aid; > −0.293 not seen even with a telescope. Odeh (2004) uses V = ARCV − (−0.1018 W³ + 0.7319 W² − 6.3226 W + 7.1651): V ≥ 5.65 seen by eye, ≥ 2 perhaps by eye, ≥ −0.96 only with optical aid. The face has every input. It also gives sky news for any month: "THE NEW MOON MAY BE SEEN".
3. **Tabular**: a 30-year cycle with leap years 2, 5, 7, 10, 13, 16, 18, 21, 24, 26, 29; 1 Muharram AH 1 = 16 July 622 (Julian; the "civil" or Friday epoch; 15 July is the "astronomical" or Thursday epoch, used with this cycle by the "Kuwaiti" scheme). As integers, the Julian Day of (y, m, d) is (11y + 3)/30 + 354y + 30m − (m − 1)/2 + d + 1948440 − 385. Against Umm al-Qura for Ramadan, Shawwal and Dhu al-Hijja 2024–2026 it agreed in six months of nine and was a day late in three. A fallback, and the converter's first guess.

Today's Islamic date (a converter): the tabular calendar gives the month's number and year; the chosen rule (1 or
2) moves its first day to the computed one, which is never more than two days away. Days: New Year 1 Muharram (month
1); Ashura 10 Muharram; Mawlid 12 Rabi' al-Awwal (3), where kept; Ramadan is month 9 (from the evening its 1st
begins); Laylat al-Qadr traditionally the 27th night; Eid al-Fitr 1 Shawwal (10); the Day of Arafah 9 Dhu al-Hijja
and Eid al-Adha 10 Dhu al-Hijja (12). The Islamic day also begins at sunset.

### 4.8 The Sun's places

- Solstices and equinoxes: the Sun's apparent longitude 0°, 90°, 180°, 270°. Astronomical cross-quarter days: 315°, 45°, 135°, 225° (3–4 Feb, 5 May, 7 Aug, 7 Nov). History kept the fixed days instead (1 Feb, 1 May, 1 Aug, 1 Nov).
- Nowruz: "If the exact moment of astronomical equinox occurs before noon (Tehran time), that day is deemed to be 1 Farvardin", otherwise the next day ([Solar Hijri calendar](https://en.wikipedia.org/wiki/Solar_Hijri_calendar); Borkowski 1996 says 12:00 Tehran mean time, Iran's calendar council true noon: the three agree for every year 1925–2101 but 2091, which falls 1.5 min after true noon). The equinox in Tehran time (JPL Horizons): 06:36 on 20 Mar 2024, 12:31 on 20 Mar 2025, 18:16 on 20 Mar 2026, 23:55 on 20 Mar 2027, 05:47 on 20 Mar 2028, so Nowruz falls on 20 Mar 2024, 21 Mar 2025, 21 Mar 2026, 21 Mar 2027, 20 Mar 2028 (margins of at least 22 minutes through 2090: an equinox good to ten minutes is enough). The arithmetic leap rule, year Y leap if (25Y + 11) mod 33 < 8, agrees with the astronomical rule for 1925–2100. Chaharshanbe Suri is the Tuesday evening before the year's last Wednesday: 18 Mar 2025, 17 Mar 2026, 16 Mar 2027.
- Inti Raymi: staged in Cusco every 24 June since 1944 (fixed, with the Day of Cusco); historically at the June solstice.
- French Republican New Year (1793–1805): 1 Vendémiaire was the day on which the autumnal equinox fell at the Paris Observatory.
- Matariki (New Zealand's holiday): the Friday nearest the Tangaroa nights (the waning moon's last-quarter nights) of the lunar month Pipiri, as the Matariki Advisory Committee chose; the dates for 2022–2052 are fixed in the Te Kāhui o Matariki Public Holiday Act 2022 ([MBIE's list](https://www.mbie.govt.nz/assets/matariki-dates-2022-to-2052-matariki-advisory-group.pdf)): 20 Jun 2025, 10 Jul 2026, 25 Jun 2027, 14 Jul 2028. Store the table (it is the law); the computed first dawn rising (below) is a separate sky event.

  | | | | | | | | | | | |
  | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
  | 2022 24 Jun | 2023 14 Jul | 2024 28 Jun | 2025 20 Jun | 2026 10 Jul | 2027 25 Jun | 2028 14 Jul | 2029 6 Jul | 2030 21 Jun | 2031 11 Jul | 2032 2 Jul |
  | 2033 24 Jun | 2034 7 Jul | 2035 29 Jun | 2036 18 Jul | 2037 10 Jul | 2038 25 Jun | 2039 15 Jul | 2040 6 Jul | 2041 19 Jul | 2042 11 Jul | 2043 3 Jul |
  | 2044 24 Jun | 2045 7 Jul | 2046 29 Jun | 2047 19 Jul | 2048 3 Jul | 2049 25 Jun | 2050 15 Jul | 2051 30 Jun | 2052 21 Jun | | |

  (A short cut, the Friday nearest the four days from the first last-quarter Moon on or after 18 June, NZ time, matches 28 of the 31.)
- Harvest Moon: the full moon nearest the September equinox (18 Sep 2024, 7 Oct 2025, 26 Sep 2026); the Hunter's Moon is the one after.
- Heliacal rising (a star's first sight at dawn): a simple arcus-visionis test, the first morning the star stands at least 1° up when the Sun is 8° below the horizon. Run here for 2026: Sirius 3 Aug at 30° N (Memphis), 13 Aug at New York, 25 Aug at London; the Pleiades 5 Jun at Wellington. The almanacs' Dog Days are fixed instead (3 Jul–11 Aug in the Old Farmer's Almanac; makers varied).

### 4.9 Test vectors: the year 2026

Computed with the rules above (the lunar and solar ones with `proto/lunar.py`); §4 says which were checked against published dates.

| Date | Days |
| --- | --- |
| Jan | 1 New Year · 5 Twelfth Night (eve) · 6 Epiphany · 7 St Distaff · 12 Plough Monday · 14 Makar Sankranti · 17 Old Twelfth Night · 27 Up Helly Aa |
| Feb | 1 Imbolc / St Brigid (Irish holiday Mon 2) · 2 Candlemas; Tu BiShvat · 3 Setsubun · 14 St Valentine · 15 Lupercalia · 17 Shrove Tuesday and Chinese New Year (horse) · 18 Ash Wednesday and 1 Ramadan (Umm al-Qura) |
| Mar | 3 Lantern Festival, Purim, Holika Dahan (total lunar eclipse) · 4 Holi · 17 St Patrick; Chaharshanbe Suri (evening) · 20 Eid al-Fitr; equinox 14:46 UT · 21 Nowruz (1405) · 25 Lady Day · 29 Palm Sunday |
| Apr | 2 Passover (seder the evening of 1 Apr) · 3 Good Friday · 5 Easter; Qingming · 12 Orthodox Easter · 13–14 Hocktide · 23 St George |
| May | 1 May Day, Beltane; Vesak in India (Sri Lanka 30 May, Thailand and Singapore 31 May) · 4 UK May bank holiday · 5 Lag BaOmer · 10 Rogation Sunday · 14 Ascension · 22 Shavuot · 24 Whitsunday · 27 Eid al-Adha · 29 Oak Apple Day |
| Jun | 4 Corpus Christi · 16 Islamic New Year (1448) · 19 Dragon Boat; Swedish Midsummer Eve · 21 solstice 08:24 UT · 23 Midsummer Eve · 24 Midsummer Day; Inti Raymi · 25 Ashura |
| Jul | 1 Canada Day · 3 Dog Days begin · 4 Independence Day · 7 Tanabata · 10 Matariki (NZ) · 14 Bastille Day · 23 Tisha B'Av |
| Aug | 1 Lammas · 11 Dog Days end · 13 Sirius's first dawn rising at New York (by the §4.8 test) · 19 Qixi · 25 Mawlid (Umm al-Qura) |
| Sep | 12 Rosh Hashanah 5787 (eve 11) · 21 Yom Kippur · 23 equinox 00:05 UT · 25 Mid-Autumn · 26 Harvest Moon; Sukkot · 29 Michaelmas |
| Oct | 10 Old Michaelmas · 12 Canadian Thanksgiving · 18 Double Ninth · 23 *Jūsan'ya* · 29 Punkie Night · 31 All Hallows' Eve |
| Nov | 1 All Saints · 2 All Souls · 5 Guy Fawkes · 8 Diwali · 11 Martinmas · 23 St Clement · 25 St Catherine · 26 US Thanksgiving · 29 Advent Sunday · 30 St Andrew |
| Dec | 5 Hanukkah (first light the evening of 4 Dec) · 6 St Nicholas · 13 St Lucy · 17 Saturnalia · 21 solstice 20:50 UT · 22 Dongzhi (the solstice is already the 22nd in Beijing) · 24 Christmas Eve · 25 Christmas, N Invicti |

## 5. A starter set of twelve

The owner's two examples, five lapsed days with strong small pictures, two great living feasts, and three set by
the sky. One a month or so, so the year always has something coming.

| # | Day | Why this one |
| --- | --- | --- |
| 1 | Christmas and Yule (A12), 24 Dec–6 Jan | The owner's example, with the most pictures (holly and ivy, the Yule log's smoke, the church lit at midnight), and it begins Herrick's year of greenery in the corners. |
| 2 | Independence Day (A6), 4 Jul | The owner's other example; the 1777 newspaper gives the whole design (thirteen rockets and an illuminated town), and the fireworks then serve New Year, Bonfire Night and national days. For British places, Guy Fawkes Night (A8) on the same machinery. |
| 3 | Twelfth Night and the wassail (B4), 5–6 Jan, 17 Jan | A lost custom with a clear emblem (the wassail bowl), and Old Twelfth Night shows how the 1752 calendar change left marks that are still kept. |
| 4 | Plough Monday and St Distaff's Day (B5), 7–13 Jan | The best pair of emblems in the list (plough and distaff, one each side of the time), lapsed, and the labours' best feast-day scene. |
| 5 | Candlemas (B6), 2 Feb | One candle and a lit church; the day the Christmas greens come down (Herrick); and a weather rhyme the face can actually judge. |
| 6 | Easter (A5), E | The great movable feast, set by the Moon through the computus; willow "palms" in the corners and the Sun dancing at sunrise. |
| 7 | May Day (B10), 1 May | A maypole on the green is the most village-like picture of all, and Stubbes (1583) describes exactly how it was dressed. |
| 8 | Midsummer Eve (B13), 23 Jun | Beacons on the far hills: fire at night in the village's own landscape; lapsed in England, alive in the north. |
| 9 | Halloween and All Hallows (A7), 31 Oct–2 Nov | Living, and the turnip lantern is older and quieter than the pumpkin; the owl and the bat are already drawn. |
| 10 | The solstices and equinoxes (C1) | Pure astronomy, four days a year, only the almanac line: the ring already shows the longest and shortest nights. |
| 11 | Mid-Autumn, Tsukimi, the Harvest Moon (C10) | One small sprite changes the full Moon's face to the rabbit: three cultures' festival on a real object. |
| 12 | Qixi and Tanabata (C9) | The sky chart's own festival: two named stars and the Milky Way the face already draws, with a bridge of magpies between them. |

Next in line: Guy Fawkes Night (A8, British places), Thanksgiving (A9), Oak Apple Day (B12), Martinmas (B17),
Hanukkah (C6: the lamp the face computes), St Lucy (A11), Matariki (C15, New Zealand), Chinese New Year (C7).

## 6. Regions and settings

### Which days belong where

- **By country.** Independence Day: the US (Canada Day 1 Jul and Bastille Day 14 Jul for Canada and France). Guy Fawkes Night: Britain and New Zealand. Thanksgiving: the US (fourth Thursday of November) and Canada (second Monday of October), a month and a half apart. Hogmanay and the first-foot: Scotland. St Patrick: Ireland and the diaspora (much of the US). St David, St George, St Andrew: Wales, England, Scotland. Plough Monday, Hocktide, Rogation, Oak Apple Day, Clementing: England. Imbolc, Beltane, Lughnasadh, Samhain: Gaelic Ireland, Scotland, Man. St Lucy: Scandinavia, Finland, Sicily. St Nicholas and Martinmas lanterns: the Netherlands, Belgium, Germany, Central Europe. Midsummer Eve fires: Scandinavia, Finland, the Baltic, Spain, Portugal, Brazil (and revived in Cornwall).
- **By community, not country.** The Jewish, Islamic, Hindu, Chinese, Japanese and Persian festivals belong to calendars the owner chooses, wherever they live (below).
- **The southern hemisphere.** The dates stay (Christmas is 25 Dec) but the season does not. The corners keep the local season, so no holly or snow in a Sydney Christmas; the flank and the red letters carry the feast. Midsummer Eve's June fires are midwinter fires there (which is what Brazil's *festas juninas* are). Easter falls in autumn. The solstice wording flips ("THE SHORTEST DAY" in June). Matariki and Inti Raymi are southern midwinter feasts. Modern pagans in the south swap Beltane and Samhain; the historical calendars did not.
- **Time zones.** A festival's date belongs to the calendar that keeps it: Chinese dates in UTC+8 (Vietnam UTC+7, Korea UTC+9), Hindu dates in IST, Umm al-Qura at Mecca. Jewish and Islamic days begin at local sunset wherever the wearer is; Western days at local midnight, their eves at local sunset.

### The calendars (opt-in, for the settings page)

Twelve calendars the owner can turn on one by one; each day belongs to one of them (a few are cross-listed, and the
engine keeps one feast a day). Rules: §4. Pictures: §3.

| # | Calendar | Its days (rule) |
| --- | --- | --- |
| 1 | **The sky's year** | the solstices and equinoxes (the Sun at 0°, 90°, 180°, 270°; worded by hemisphere: "THE LONGEST DAY"), the cross-quarter days (45°, 135°, 225°, 315°), the Harvest Moon and the Hunter's Moon (the full moons nearest and next after the September equinox), the Dog Days (3 Jul to 11 Aug) and Sirius's first dawn rising, the Pleiades' first dawn rising (Matariki), the new crescent each month (Yallop); beside the face's existing news of eclipses, planets meeting and meteor showers |
| 2 | **The Christian year** (Western) | Advent Sunday (Sunday after 26 Nov); Christmas Eve and Day, St Stephen, St John, the Holy Innocents (24–28 Dec); the Circumcision (1 Jan), Epiphany (6 Jan), Candlemas (2 Feb), Lady Day (25 Mar); Shrove Tuesday E − 47, Ash Wednesday E − 46, Palm Sunday E − 7, Maundy Thursday E − 3, Good Friday E − 2, Easter E, Ascension E + 39, Whitsunday E + 49, Trinity E + 56, Corpus Christi E + 60; St John the Baptist (24 Jun), Michaelmas (29 Sep), All Saints and All Souls (1–2 Nov); the saints whose days carry pictures: Valentine (14 Feb), Martin (11 Nov), Nicholas (6 Dec), Lucy (13 Dec). Red dates on the BCP's red-letter days |
| 3 | **The Eastern churches** | Pascha by the Julian computus (§4.2), with Clean Monday P − 48, Palm Sunday P − 7, Holy Friday P − 2, Ascension P + 39, Pentecost P + 49; the fixed feasts on their Julian dates, 13 days later in the Gregorian calendar: Christmas 7 Jan, the Old New Year 14 Jan, Theophany 19 Jan, the Meeting of the Lord 15 Feb, the Annunciation 7 Apr, St George 6 May, the Transfiguration 19 Aug, the Dormition 28 Aug, the Exaltation of the Cross 27 Sep, St Nicholas 19 Dec. The Revised Julian churches (Constantinople, Greece, Romania, Bulgaria, Cyprus; Ukraine's since 2023) keep the fixed feasts on the Gregorian dates and Pascha by the Julian computus: an option. Pictures: red eggs at Pascha, the blessing of the waters at Theophany, the first star on Christmas Eve (below) |
| 4 | **Old English customs** | Twelfth Night (5 Jan) and Old Twelfth Night (17 Jan) wassails; St Distaff's Day (7 Jan); Plough Monday (Monday after 6 Jan); Candlemas customs (the greenery down, the weather rhyme); Shrovetide (the pancake bell, football); Hocktide (E + 8, E + 9); Rogationtide (E + 35 to E + 39); May Day (the maypole, bringing in the May); Oak Apple Day (29 May); Lammas (1 Aug); the Michaelmas goose (29 Sep) and Old Michaelmas (10 Oct); Martinmas (11 Nov); Clementing and Catterning (23 and 25 Nov); the Boy Bishop (6 to 28 Dec) and the Lord of Misrule, with France's Feast of Fools (1 Jan); the quarter days (25 Mar, 24 Jun, 29 Sep, 25 Dec). Most of these are lapsed: this is the "old customs" calendar |
| 5 | **The fire festivals** | Burning the Clavie (11 Jan, Old New Year's Eve), Up Helly Aa (last Tuesday of January), the Easter fires (at dusk on Holy Saturday, E − 1, or on Easter Day, by place: northern Germany, the eastern Netherlands, Sweden, Finland), Walpurgis Night (30 Apr), Beltane (30 Apr from sunset), Midsummer Eve (23 Jun from sunset; Sweden the Friday between 19 and 25 Jun), Samhain (31 Oct from sunset), Bonfire Night (5 Nov, when calendar 8 is off). Holika Dahan, Lag BaOmer, Lohri and Chaharshanbe Suri bring the same fire in their own calendars |
| 6 | **Ancient Rome** | the Kalends of January (1 Jan: Janus, gifts), Lupercalia (15 Feb), Matronalia (1 Mar), Parilia (21 Apr: Rome's birthday, when shepherds leapt through burning straw), Floralia (28 Apr to 3 May), Vestalia (9 Jun), Saturnalia (17 to 23 Dec), N Invicti (25 Dec). On their nominal days (the Romans' own calendar was the Julian) |
| 7 | **The United States** | New Year's Day (in every civil calendar); Groundhog Day (2 Feb); Washington's Birthday (third Monday of February; 22 Feb until 1971); St Patrick's Day (17 Mar); Memorial Day (last Monday of May; Decoration Day, 30 May, until 1971); Juneteenth (19 Jun); Independence Day (4 Jul); Labor Day (first Monday of September); Halloween (31 Oct); Veterans Day (11 Nov); Thanksgiving (fourth Thursday of November). Lapsed: Pope Night (5 Nov, colonial New England, until 1775), Evacuation Day (25 Nov, New York, from 1783 into the 1910s), Pinkster (Whitsun, Dutch New York and Albany, until 1811). For Canada: Canada Day (1 Jul), Thanksgiving (second Monday of October) |
| 8 | **Britain and Ireland** | Hogmanay (31 Dec); Burns Night (25 Jan); St Brigid's Day (1 Feb; the Irish holiday is the first Monday of February, or 1 Feb if a Friday); St David (1 Mar); St Patrick (17 Mar); Mothering Sunday (E − 21); St George (23 Apr); the May Day bank holiday (first Monday of May); Bonfire Night (5 Nov); Halloween (31 Oct); Remembrance Sunday (second Sunday of November) and Armistice Day (11 Nov); St Andrew (30 Nov); Boxing Day, St Stephen's Day (26 Dec: Ireland's wren boys) |
| 9 | **Hebrew** | Rosh Hashanah, Yom Kippur, Sukkot, Simchat Torah, Hanukkah, Tu BiShvat, Purim, Passover, Lag BaOmer, Shavuot, Tisha B'Av (§4.4); Israel or diaspora days; every day from the sunset before |
| 10 | **Chinese** (and East Asian) | New Year (1/1), the Lantern Festival (1/15), Qingming (the Sun at 15°), the Dragon Boat Festival (5/5), Qixi (7/7), the Ghost Festival (7/15), Mid-Autumn (8/15), the Double Ninth (9/9), Dongzhi (the December solstice), all in UTC+8 (§4.5). Japan: Setsubun (the day before the Sun reaches 315°), Tanabata (7 Jul), Tsukimi (8/15 and 9/13 of the old calendar, UTC+9). Korea: Seollal and Chuseok (UTC+9). Vietnam: Tết and Trung Thu (UTC+7) |
| 11 | **Islamic** | New Year (1 Muharram), Ashura (10 Muharram), Mawlid (12 Rabi' al-Awwal, where kept), Ramadan, Laylat al-Qadr (27 Ramadan), Eid al-Fitr (1 Shawwal), the Day of Arafah and Eid al-Adha (9 and 10 Dhu al-Hijja); by Umm al-Qura, local sighting, or the tabular calendar (§4.7) |
| 12 | **Hindu** | Makar Sankranti (with Lohri the evening before, and Pongal), Vasant Panchami, Maha Shivaratri, Holika Dahan and Holi, Ugadi and Gudi Padwa, Rama Navami, Raksha Bandhan, Janmashtami, Ganesh Chaturthi, Navaratri and Dussehra, Diwali (five days), Kartik Purnima (§4.6) |

Three small calendars could join them: **Persian** (Chaharshanbe Suri, Nowruz, Sizdah Bedar on 13 Farvardin, Yalda
on the longest night); **Māori** (the Matariki holiday on its legislated dates; its star is already in the sky's
year); and **the primstav**, the Norse year as the calendar sticks cut it, all pictograms (§7.2): the drinking horn
turned upside down on *Tjugendedagen* (13 Jan), the candlestick on Candlemas, the leafy tree on *Sommardag* (14 Apr,
the first day of summer), the cuckoo on 1 May, the sun on *Jonsok*, Olaf's axe on *Olsok* (29 Jul), the gridiron on
*Larsok* (10 Aug), the scales at Michaelmas, the mitten on *Vinternatt* (14 Oct, the first winter night), the goose at
Martinmas, the wheel for St Catherine, the torch for St Lucy's long night, the barrel when the Christmas ale is
brewed (21 Dec), the horn at Yule.

On Christmas Eve the Polish *Wigilia* and the Ukrainian *Sviat Vechir* suppers begin when the first star is seen. The
face can name it: the brightest star or planet more than 5° up as civil twilight ends (for New York on 24 Dec 2026,
at 17:05, Vega, 37° up: "THE FIRST STAR: VEGA"), a true sky effect for calendars 2 and 3.

### The settings page

- **Feast days**: off / on, then the twelve calendars as switches, with a drag order for clashes.
- **Lapsed days**: show the days no longer kept, in every calendar (Pope Night and Evacuation Day, the Feast of Fools, Oak Apple Day; on for the owner, perhaps off by default in the store). **Old Style**: keep the 1752 customs on their old days (17 Jan wassail, 11 Jan Clavie, 10 Oct Old Michaelmas).
- **Choices inside a calendar**: Hebrew, Israel or diaspora; Islamic, Umm al-Qura, local sighting or tabular; Eastern churches, Julian or Revised Julian fixed feasts; Hindu, amanta or purnimanta month names.
- **Defaults from the country the phone already names**: the US: the sky's year, the Christian year, the United States. Canada: the same, with Canada's days. The UK: the sky's year, the Christian year, Britain and Ireland (Old English customs for the owner). Ireland: the sky's year, the Christian year, Britain and Ireland, the fire festivals. Australia and New Zealand: the sky's year, the Christian year (Māori in New Zealand). The Nordic countries, Germany, the Netherlands: the sky's year, the Christian year, the fire festivals. Russia, Serbia, Georgia: the Eastern churches. Greece, Romania, Bulgaria: the Eastern churches, Revised Julian. China, Taiwan, Hong Kong, Singapore, Korea, Vietnam, Japan: the sky's year, Chinese (with the country's variant). India and Nepal: the sky's year, Hindu. Israel: the sky's year, Hebrew. Iran: the sky's year, Persian, Islamic. Muslim-majority countries: the sky's year, Islamic. A default is only a starting point; anyone can add any calendar.
- **Clashes**: one feast a day, chosen by the calendars' order, then by rank (principal over lesser, living over lapsed); a second feast the same day may take the odd hours' flank pieces. Eclipses always keep the almanac line. Clashes to expect: 1 Jan New Year and the Feast of Fools; 1 May May Day and Beltane; 11 Nov Martinmas and Remembrance; 17 Feb 2026 Shrove Tuesday and Chinese New Year; 18 Feb 2026 Ash Wednesday and 1 Ramadan; 3 Mar 2026 Holika Dahan, Purim and the Lantern Festival, under a total eclipse of the Moon (the eclipse keeps the line).
- **Quarter days** (an optional black-letter line, "QUARTER DAY"): England's Lady Day 25 Mar (New Year's Day in law until 1752), Midsummer 24 Jun, Michaelmas 29 Sep, Christmas 25 Dec; Scotland's Candlemas, Whitsunday, Lammas and Martinmas, since 1991 on 28 Feb, 28 May, 28 Aug and 28 Nov (Term and Quarter Days (Scotland) Act 1990). The eightfold "wheel of the year" that joins the solstices and equinoxes to the Gaelic quarter days is a 20th-century Wiccan arrangement (Hutton).

### Cost on the watch

About 16 bytes a feast (rule code and parameters, set, rank, wordings, emblem, effects) for some 60 feasts, and
about 32 bytes per 16×16 one-bit emblem for some 40 emblems: under 3 KB of resources. The rules run when the date
changes and at sunset. The lunar calendars need about 14 new moons and 13 solar terms a year: work them out once a
year (or once a month) and keep them.

## 7. Sources and reference images

### 7.1 The English calendar-custom books (public domain)

| Work | Scans | Notes |
| --- | --- | --- |
| Robert Chambers, *The Book of Days* (1863–64) | [vol 1](https://archive.org/details/bookofdaysmiscel01chamuoft) (Jan–Jun), [vol 2](https://archive.org/details/bookofdaysmiscel02chamuoft) (Jul–Dec); Cornell copies `cu31924014604627`, `cu31924014604635`; a day-by-day transcription with the cuts at [thebookofdays.com](https://www.thebookofdays.com/indexes/illustrations.htm) (its home page carries spam links) | archive.org page n = printed page + 13 (vol 1), + 11 (vol 2). Each volume opens with a list of its illustrations. Not on Gutenberg |
| William Hone, *The Every-Day Book* (1826–27), *The Table Book* (1827), *The Year Book* (1832) | *Every-Day Book* [I](https://archive.org/details/b29326072_0001), [II](https://archive.org/details/b29326072_0002) (Wellcome); Gutenberg [#53275](https://www.gutenberg.org/ebooks/53275), [#53276](https://www.gutenberg.org/ebooks/53276), *Table Book* [#53277](https://www.gutenberg.org/ebooks/53277); *Table Book* [I](https://archive.org/details/tablebook01honeuoft), [II](https://archive.org/details/tablebook02hone); *Year Book* [scan](https://archive.org/details/cu31924029752791) | The Gutenberg HTML has every woodcut as a clean 550–600 px image (`/cache/epub/<n>/images/illoNNNN.jpg`): the best drawing references |
| John Brand, *Observations on Popular Antiquities* | Ellis ed. 1813: `observationsonpo01branuoft`, `…02branuoft`; Bohn ed. 1849: `b29328561_0001`–`_0003`; Hazlitt ed. 1870: `popularantiquiti01bran`–`03bran` (all archive.org) | the customs by day, with the older sources quoted |
| *The Kalender of Shepherdes* (Paris, 1503; Sommer's facsimile, 1892) | [archive.org](https://archive.org/details/kalenderofshephe00pyns) (Getty colour scan); the calendar is n136 (January) to n147 ([December](https://archive.org/details/kalenderofshephe00pyns/page/n147/mode/1up)) | Each month: the feasts printed in red, the month's labour and zodiac roundel, and a strip of little saint figures down the margin, each holding the thing that names him. December: St Barbara with her tower, St Nicholas, the Nativity, pig-killing, Capricorn. November ([n146](https://archive.org/details/kalenderofshephe00pyns/page/n146/mode/1up)): All Saints, the souls in the flames on All Souls, St Martin as a bishop, Sagittarius, St Clement with his anchor, St Catherine with her wheel, St Andrew with his saltire. February ([n137](https://archive.org/details/kalenderofshephe00pyns/page/n137/mode/1up)): St Brigid, the Purification, St Valentine, St Peter's Chair and St Matthias in red. January ([n136](https://archive.org/details/kalenderofshephe00pyns/page/n136/mode/1up)): the feaster by the fire, the Circumcision and the Epiphany in red, the Three Kings crowned in the saints' strip, St Paul with his sword. June ([n141](https://archive.org/details/kalenderofshephe00pyns/page/n141/mode/1up)): sheep-shearing, St John the Baptist pointing to the Lamb with its cross-banner, St Peter with his keys. September ([n144](https://archive.org/details/kalenderofshephe00pyns/page/n144/mode/1up)): the sower, the Holy Cross on its mound, Libra's balance, St Michael; and "Dies caniculares" written against 6 Sep. All six in `ref/`. A note under February explains the golden numbers that give each month's new moons. The 1493 Paris *Compost* is at Gallica ([unverified](https://gallica.bnf.fr/ark:/12148/btv1b86267664)) |
| Robert Herrick, *Hesperides* (1648) | Gutenberg [#22421](https://www.gutenberg.org/ebooks/22421) (Pollard, 1898): anchors `#id_1.p178` Corinna's Going A-Maying, `#id_1.p250` The Hock-Cart, `#id_1.p476` The Wassail, `#id_2.p784` Ceremonies for Christmas, `#id_2.p892` Ceremonies for Candlemas Eve (and 893, 894, 980), `#id_2.p1026` Saint Distaff's Day, `#id_2.p1035` Twelfth Night | the year's house customs in verse; poem 695 is The May-pole |
| Philip Stubbes, *The Anatomie of Abuses* (1583) | Furnivall's edition, 1877–82, at the [Wellcome Collection](https://wellcomecollection.org/works/ktk2h4wd) | the maypole, the Lord of Misrule |
| John Stow, *A Survey of London* (1598, 1603) | Gutenberg [#42959](https://www.gutenberg.org/ebooks/42959) | Midsummer's bonfires, birch and lamps; the Midsummer Watch |
| Joseph Strutt, *Sports and Pastimes of the People of England* (1801) | 1810 ed. `gliggamenaangeld00stru`; Cox's 1903 ed. [archive.org](https://archive.org/details/sportspastimesof00struuoft) | |
| Thomas Tusser, *Five Hundred Points of Good Husbandry* (1573) | English Dialect Society 1878: `fivehundredpoint08tussuoft`; Gutenberg [#51764](https://www.gutenberg.org/ebooks/51764) | Plough Monday, Christmas husbandry |
| T. F. Thiselton-Dyer, *British Popular Customs* (1876) | [archive.org](https://archive.org/details/cu31924027939309); Gutenberg #58809 (1911 reprint) | |
| Clement A. Miles, *Christmas in Ritual and Tradition* (1912) | Gutenberg [#19098](https://www.gutenberg.org/ebooks/19098) | Saturnalia, Yule, the Twelve Days, Lucy, Nicholas, the Feast of Fools |
| J. G. Frazer, *The Golden Bough* (abridged, 1922) | Gutenberg [#3623](https://www.gutenberg.org/ebooks/3623) | the fire festivals (Beltane, Midsummer, Halloween), maypoles |
| Bede, *De temporum ratione* (725), ch. 15 "De mensibus Anglorum" | [Latin](https://la.wikisource.org/wiki/De_ratione_temporum) (Giuli, Eosturmonath, "Modranicht, id est, matrum noctem"); partial English in Kemble, *The Saxons in England* (1849) I p. 374 ([scan](https://archive.org/details/saxonsinenglandh01kembiala/page/n389/mode/1up)) | Wallis's translation (1999) is in copyright |
| The Calendar of 354 (Chronograph of Filocalus) | [Commons category](https://commons.wikimedia.org/wiki/Category:Chronography_of_354) (17th-century copies of the months, PD-Art); [calendar text](https://www.tertullian.org/fathers/chronography_of_354_06_calendar.htm) | December's dice, dice tower, torch and mask; SATVRNALIA on 17 Dec, N·INVICTI on 25 Dec |
| *The Book of Common Prayer* (1662 text, London printing of 1669) | [archive.org](https://archive.org/details/bookofcommonpray00chur_14): January n40, December n51, the tables for the movable feasts n52–54 ("To find Easter for ever") | January: the Circumcision, the Epiphany, the Conversion of St Paul and King Charles the Martyr in red; Lucian, Hilary, Agnes in black. December: St Thomas, Christmas, St Stephen, St John, the Innocents in red; Nicolas, Lucy, O Sapientia, Silvester in black. The left column's golden numbers mark the new moons (`ref/`) |
| Calendar sticks: Plot (1686), Worm (1626/1643), Olaus Magnus (1555) | §7.2 | |

### 7.2 The calendar sticks' pictograms

The sticks mark the feast days with tiny cut pictograms beside the day notches: the best period models for 10–20 px
emblems. They vary from stick to stick (Plot: the minor ones "almost upon every Clogg"); the commonest forms are given
first. Primstav sources: Norwegian Wikipedia's table ([Primstav](https://no.wikipedia.org/wiki/Primstav), largely after
Juel Lund 1983; CC BY-SA text), Store norske leksikon ([primstav](https://snl.no/primstav), a survey of 319 staves;
restricted reuse), Amund Helland, *Bratsberg amt* I (1900) pp. 476–501 ([Wikisource](https://no.wikisource.org/wiki/Topografisk-statistisk_beskrivelse_over_Bratsberg_amt/1/95),
public domain; his numbered figure by Øde and Rygh, `ref/stick-helland1900-*`), Ole Worm, *Fasti Danici* (1643: the
symbol key in Book II pp. 109–118, "De Festorum Signis" in Book I pp. 61–62), and J. Barnard Davis, *Archaeologia* 41
(1868) pp. 453–478 ([archive.org](https://archive.org/details/archaeologiaopt241sociuoft)). Clog: Robert Plot, *The
Natural History of Stafford-shire* (1686) ch. X §§ 59–60, pp. 429–430, and his plate, Tab. XXXV (`ref/stick-plot1686-clog-tab35.png`).

| Date | Feast | Primstav | Clog almanac (Plot) |
| --- | --- | --- | --- |
| 1 Jan | New Year, the Circumcision | a sun-wheel, an hourglass or a church; Worm: a dish heaped with New Year cakes | an eye: an almond outline round a ring and a dot, on a short stem |
| 6 Jan | Epiphany (*trettende dag*) | three crowns (Worm), three men (Helland), three crosses on one bar | a six-armed star with flared tips (Plot's "Starr") |
| 7 Jan | St Knut | a cross; Worm: a hunting spear ("Knut drives Yule out") | — |
| 13 Jan | *Tjugendedagen* (the 20th day); St Hilary | a bell ("rings Christmas out"), or a drinking horn upside down (the ale is drunk), an axe, a barrel | a double-barred cross on its side (Hilary a bishop) |
| 25 Jan | Conversion of St Paul | a bow ("Pål skyttar"), a sword | an axe: a long diagonal shaft with a bow-tie head |
| 2 Feb | Candlemas (*kyndelsmesse*) | a candlestick of many arms; a lily or a crowned head | a heart with a dot (every Lady Day); a vigil mark on 1 Feb |
| 14 Feb | St Valentine | — | a true lover's knot (on the plate a ring round a six-petalled rosette) |
| 22 Feb | St Peter's Chair (*Per varmestein*) | a key, or a stone (Peter throws a warm stone in the water and the ice loosens) | — |
| 24 Feb | St Matthias | an axe; Worm: three goose eggs (the geese start laying) | a long-handled axe |
| 1 Mar | St David | — | a harp, triangular, with upright strings |
| 2 Mar | St Chad | — | a bough: an upright stem with three pairs of down-slanting branches |
| 12 Mar | St Gregory | a bird (a dove or a crow); Worm: a schoolmaster with ferule and rods | a square with an X and flared corner prongs |
| 17 Mar | St Gertrude (not Patrick) | a spindle-whorl, a lily, a birch twig | — |
| 25 Mar | Lady Day (*marimesse*) | a crown, a woman, a tree (a tree is the commonest Marian sign on Norwegian staves) | a heart with a dot; a vigil dot on 24 Mar |
| 14 Apr | *Sommardag*, the first day of summer | a tree in leaf, a bush; Worm: a rose | — |
| 23 Apr | St George | a cross, a horse | a tall narrow spearhead |
| 1 May | SS Philip and James (*Gauksmesse*), May Day | a cuckoo; Worm: a beech coming into leaf | a bough "as set up for May Day": a fan of straight strokes from one point |
| 3 May | Invention of the Cross | a large cross | a cross pattée |
| 24 Jun | Midsummer (*jonsok*) | a sun, often a hatched disc; an hourglass; Worm: a lamb | a broadsword, point up |
| 29 Jun | SS Peter and Paul | Peter's key | two keys side by side |
| 25 Jul | St James (*Jakob våthatt*) | a dripping hat (Helland); a pilgrim's staff (Worm) | (an obscure device) |
| 29 Jul | *Olsok*, St Olaf | Olaf's axe | — |
| 1 Aug | Lammas, St Peter's Chains | a key with a chain | a strung bow with arrows (unexplained) |
| 10 Aug | St Lawrence (*larsok*) | a gridiron | a gridiron: parallel bars on a handle |
| 15 Aug | Assumption | a crown, a woman | a heart |
| 24 Aug | St Bartholomew | a knife (the billy-goats are slaughtered), an axe | a pointed oval with a dot (unexplained) |
| 8 Sep | Nativity of Mary | a crown; Helland: sheep shears | a heart |
| 14 Sep | Holy Cross | a cross | a shaft through a cross pattée ending in an arrowhead |
| 29 Sep | Michaelmas | scales (Worm), a horn, the archangel's head | a stylised balance: two open triangles hung from a stepped upright |
| 14 Oct | *Vinternatt*, the first winter night | a mitten or glove; a bare tree | — |
| 18 Oct | St Luke | an ox; a cross | a lute (unexplained) |
| 25 Oct | St Crispin | — | a pair of shoes (the shoemakers' patron): two long figure-of-eight soles |
| 28 Oct | SS Simon and Jude | a ship (Worm: they were fishermen), a sledge (Helland: the sledging season) | an S-shaped hook (uncertain) |
| 1 Nov | All Saints | a church (Worm), an upturned boat (the sailing season over) | a square lattice knot; a vigil dot on 31 Oct |
| 11 Nov | Martinmas | a goose (Worm; Hone's "Norway clogs"), a pig, a mitre | an H with two bars (unexplained); one English clog a notch ending in a beak |
| 23 Nov | St Clement | an anchor, a church, a papal crown | a pot: a handled jug, round-bellied, narrow-necked |
| 25 Nov | St Catherine | a wheel (said to be Kari's spinning wheel) | a spoked wheel (about 12 spokes) |
| 30 Nov | St Andrew | a saltire, a fish-hook (the Christmas fishing begins) | a saltire with flared ends; a vigil dot on 29 Nov |
| 6 Dec | St Nicholas | a crozier, a mitre | an interlaced double loop (unexplained) |
| 13 Dec | St Lucy (*Lussi*) | a torch or candle (Helland: the long nights), a bonfire; Worm: a cow's hoof with sun rays (the solstice) | a tall lamp- or flask-like shape |
| 21 Dec | St Thomas (*Tomas brygger*) | a barrel (the Christmas ale is brewed); Worm: a hand with two fingers out | three rays fanning to a bar; two vigil dots |
| 25 Dec | Christmas | a drinking horn (*jolehonne*), a candelabrum, a barrel, a sun | a curled horn, a spiral ending in a flared bell, on 25–28 Dec; a vigil dot on 24 Dec |

Conventions: Plot's great feasts have a large dot set in the middle of their sign, and a second dot against the day
before when there was a vigil; his signs show "the saint's office, the manner of martyrdom, or the work or sport of
that season". On Worm's boards a line with three inverted hooks before a feast marks a fast, and ticked lines give
the length of day and night. The primstav's two faces are the year's two halves: the summer side from 14 April, the
winter side from 14 October.

Scans: Plot, [archive.org](https://archive.org/details/the-natural-history-of-stafford-shire-by-robert-plot) (Public
Domain Mark; a PDF in a zip, the plate on PDF page 560) and an [EEBO microfilm copy](https://archive.org/details/bim_early-english-books-1641-1700_the-natural-history-of-s_plot-robert_1686)
(the plate at n552, the text at n562–563); the clog discussion runs §§ 42–62, pp. 418–432. Hone's *Every-Day Book* II
(dated 1827) has Plot's clog redrawn as its frontispiece ([large image](https://www.gutenberg.org/cache/epub/53276/images/illo0002lg.jpg));
Chambers I p. 9 has another copy (`ref/`). Worm, *Fasti Danici* 1643, [archive.org](https://archive.org/details/bub_gb_6X2ZKMQBcvIC)
(Public Domain Mark): the runic staff at p. 87, and the two pictogram boards "Facies prior" p. 100 and "Facies
posterior" p. 102 (n119, n121; `ref/`). Olaus Magnus (1555), Book I ch. 34 "De baculis", p. 54
([archive.org](https://archive.org/details/ARes38216/page/n141)): his woodcut shows staves cut with runes only, no
pictograms (`ref/`). The Folkemuseum's labelled 18th-century drawing "Den norske Prim-stav" names the saint beside
each sign ([DigitaltMuseum](https://digitaltmuseum.no/011013375064), Public Domain Mark; `ref/`). The richest single
sheet is the Swedish printed runic calendar from Malma ([Commons](https://commons.wikimedia.org/wiki/File:Runstav_från_Malma.tif),
`ref/stick-malma-runstav-pd.jpg`): a row a month under its zodiac sign, each feast a small engraving: the Yule horns
and the star in January, the candelabrum and a heart in February, keys, a ship, a tree, a barrel; in November the
goose, a church, Clement's anchor, Catherine's wheel and Andrew's saltire; in December a tower, a tankard and the
horns again. Its pictures sit at about the scale of the face's flank pieces.

Licences elsewhere: of the 704 primstav images on DigitaltMuseum only 5 carry the Public Domain Mark (about 473 are
CC BY-SA); the Commons "Primstav NF.*" photos are CC BY-SA 4.0. The British Museum's clogs (e.g. OA.230) are CC
BY-NC-SA 4.0 by report; the Science Museum's clog (1986-613) has no image online; the Ashmolean's clogs and its runic
almanac of boxwood leaves are probably non-commercial only (unverified); Pitt Rivers images are © with educational
use only.

### 7.3 Books of Hours: the red-letter (and gold-letter) pages

- Walters W.99 (CC0): [fol. 1r, January](https://www.thedigitalwalters.org/Data/WaltersManuscripts/W99/data/W.99/sap/W99_000005_sap.jpg): the month's title, the Circumcision and the Epiphany in gold, the other saints alternating blue and red; [fol. 12v, December](https://www.thedigitalwalters.org/Data/WaltersManuscripts/W99/data/W.99/sap/W99_000028_sap.jpg): "Jour de noel" in gold, with St Thomas, St Stephen, St John, the Innocents and Thomas Becket; "Vegile" in red (`ref/`). The Walters catalogue describes graded calendars also in W.281, W.262, W.240, W.225 and, English (Sarum), W.79 and W.34.
- The Met, *Belles Heures* of Jean de France (Open Access CC0, object 470306): [fol. 2v, January 16–31](https://images.metmuseum.org/CRDImages/cl/original/DP252983.jpg) (St Vincent and the Conversion of St Paul in gold), [fol. 13r, December 1–16](https://images.metmuseum.org/CRDImages/cl/original/DP252990.jpg) (St Eloi, St Nicholas, the Conception in gold; pig-killing in a quatrefoil above, Capricorn below).
- The Met, Hours of Jeanne d'Evreux (CC0, object 470309): [December](https://images.metmuseum.org/CRDImages/cl/original/DP233156.jpg), [January](https://images.metmuseum.org/CRDImages/cl/original/DP233128.jpg): entries in red, blue and a brownish gold; grisaille labours.
- *Très Riches Heures* (Chantilly, MS 65; Commons, public domain): [fol. 13r, December](https://commons.wikimedia.org/wiki/File:029_MS_65_F13.jpg): "Le iour de noel" in gold, with day-length and golden-number columns; [fol. 2r, January](https://commons.wikimedia.org/wiki/File:007_MS_65_F2.jpg): the major feasts' lines are blank, the gold never added; miniatures [January](https://commons.wikimedia.org/wiki/File:006_MS_65_F1_V.jpg), [December](https://commons.wikimedia.org/wiki/File:028_MS_65_F12_V.jpg).

### 7.4 The rest of the world

- **Chinese**: the Qing court's *Activities of the Twelve Months* (清院畫十二月令圖; National Palace Museum, Taipei; twelve
  hanging scrolls, early Qianlong), on Commons as `清畫院畫十二月月令圖N月_軸.jpg` (PD-Art; use the 1920 px thumbnails,
  the originals are 20–26 MB): the 1st month the Lantern Festival (故畫003106), the 5th the dragon boats (故畫003110,
  `ref/`), the 7th Qixi's needle-threading by moonlight with magpies (故畫003112), the [8th](https://commons.wikimedia.org/wiki/File:清畫院畫十二月月令圖八月_軸.jpg)
  Mid-Autumn (故畫003113), the 9th chrysanthemums and hill-climbing (故畫003114). The NPM's own open data: 1-megapixel
  images CC0, 6-megapixel CC BY 4.0 (from a 2024 copy of its terms). Also CC0: the Met's moon goddess with the jade
  rabbits ([44090](https://www.metmuseum.org/art/collection/search/44090)) and lantern panel (44119); the Art Institute
  of Chicago's Duanwu plate of the five poisons ([42344](https://www.artic.edu/artworks/42344)); Cleveland's "Waiting for
  the Moon in the Mid Autumn Festival" (1973.72). Emblems the scrolls suggest: a string of firecrackers, a tasselled
  lantern, a willow sprig for Qingming, a dragon-prowed boat, a chrysanthemum on a hill, a plum branch of nine
  blossoms filled in day by day through the "nine nines" after Dongzhi.
- **Japanese** (CC0): Hiroshige's Tanabata ([Met 36541](https://www.metmuseum.org/art/collection/search/36541), `ref/`);
  Utamaro's moon-viewing party ([AIC 34789](https://www.artic.edu/artworks/34789), `ref/`); Hiroshige's "Moon-Viewing
  Promontory" (Cleveland 1985.320); an Utamaro tsukimi arrangement (Met 56798). No verified picture of the dango.
- **Hindu** (CC0, Cleveland): "Krishna celebrates Holi", Pahari, c. 1770 ([2018.104](https://clevelandart.org/art/2018.104), `ref/`);
  "Royal Women Celebrating Diwali", Lucknow, c. 1760 ([1971.82](https://clevelandart.org/art/1971.82), `ref/`); kite
  flying (1973.237); a silver pichkari at the Met (823285).
- **Jewish**: the Golden Haggadah (BL Add MS 27210), [fol. 15r](https://commons.wikimedia.org/wiki/File:Dance_of_Marian._Full_F15_from_Golden_Haggadah.jpg)
  (`ref/`) and [fol. 14v](https://upload.wikimedia.org/wikipedia/commons/f/f8/Exodus_golden_haggadah.jpg) (Commons, PD-Art;
  the BL's own viewer has been offline); the Baraffael Hanukkah lamp ([Met 751313](https://www.metmuseum.org/art/collection/search/751313),
  CC0, `ref/`; other CC0 lamps: Met 889186, 912984, 192064, 928696); shofars in the Met's open-access list (e.g. 500994).
- **Islamic**: Vedder's "The End of Ramazan" ([SAAM 1978.108.48](https://americanart.si.edu/collections/search/artwork/?id=25631), CC0);
  Coecke van Aelst's "Festival of the New Moon" (Met 422768, CC0); Jahangir at the Eid gathering (Berlin, I 4596 fol.
  13r, PD on Commons). Lane's fanous on Commons is CC BY-SA, not public domain.
- **Persian**: a Qajar Nowruz still life with narcissus and an 1893 photograph of Naser al-Din Shah's Nowruz
  reception, both on Commons; no public-domain haft-sin or Chaharshanbe Suri picture found.
- **Inca**: Guaman Poma, *Nueva corónica y buen gobierno* (1615), Royal Danish Library GKS 2232 4º, drawing 95, page 246
  [248], "IVNIO, HAVCAI CVSQVI", the facing text naming "Ynti Raymi" ([poma.kb.dk](https://poma.kb.dk/permalink/2006/poma/248/en/text/),
  Public Domain Mark; `ref/`).
- **Māori**: Te Ara, [Matariki – Māori New Year](https://teara.govt.nz/en/matariki-maori-new-year/page-1) (text CC BY-NC
  3.0 NZ); the Matariki Advisory Committee's [dates and method](https://www.mbie.govt.nz/assets/matariki-dates-2022-to-2052-matariki-advisory-group.pdf)
  (Rangi Matamua, 2021); Te Papa's [page](https://www.tepapa.govt.nz/node/4867).
- **Buddhist** (if wanted): Vesak is the full moon of Vesākha by each country's calendar, and countries split when a
  leap month falls near it: in 2026 India kept 1 May, Sri Lanka moved to 30 May, Thailand and Singapore kept 31 May;
  Hong Kong and Korea keep the Buddha's birthday on the 8th of the 4th Chinese month. Cleveland's "Birth of the
  Buddha" (1959.349) and the AIC's "Buddha Calling the Earth to Witness" (109469) are CC0. Emblem: a lotus, or the
  wheel under the full Moon.
- **Date sources**: the [HKO tables](https://www.hko.gov.hk/en/gts/time/calendar/text/files/T2026e.txt) (one file a year,
  `T{YYYY}e.txt`, 1901–2100); NAOJ's koyomi pages on [Tanabata](https://eco.mtk.nao.ac.jp/koyomi/wiki/BCB7CDBC.html) and
  [the mid-autumn moon](https://eco.mtk.nao.ac.jp/koyomi/wiki/C3E6BDA9A4CECCBEB7EEA4C8A4CF.html); [Drik Panchang](https://www.drikpanchang.com/festivals/lakshmipuja/festivals-lakshmipuja-timings.html?year=2025&geoname-id=1261481)
  (add `&geoname-id=1261481` for New Delhi, or it guesses the city from the reader's address); [hebcal](https://www.hebcal.com/hebcal?v=1&cfg=json&maj=on&year=2026&month=x&geo=none);
  van Gent's [Umm al-Qura pages](https://webspace.science.uu.nl/~gent0113/islam/ummalqura_principal.htm); [Andina](https://andina.pe/agencia/noticia-en-consiste-inti-raymi-cual-es-su-historia-y-que-lugares-cusco-ocurre-989247.aspx)
  on Inti Raymi.

### 7.5 Other primary sources quoted

- John Adams to Abigail Adams, 3 July 1776: [Founders Online](https://founders.archives.gov/documents/Adams/04-02-02-0016). The 1777 Philadelphia fireworks: *Pennsylvania Evening Post*, 5 July 1777, quoted by the [Smithsonian](https://www.smithsonianmag.com/smart-news/why-we-set-off-fireworks-on-the-fourth-of-july-470334/). The flag resolution of 14 June 1777: *Journals of the Continental Congress* vol. 8.
- Chaucer, *The Parlement of Foules*, lines 309–10; Donne, "A Nocturnall upon S. Lucies Day"; Burns, "Halloween" (1785); Caleb Threlkeld, *Synopsis Stirpium Hibernicarum* (1726) on the shamrock; Cormac's Glossary (O'Donovan and Stokes, 1868) on Beltane; Snorri, *Heimskringla*, the saga of Hákon the Good, on Yule.
- Statutes and rules: [Term and Quarter Days (Scotland) Act 1990, s. 1](https://www.legislation.gov.uk/ukpga/1990/22/section/1); [the Irish St Brigid's Day holiday, S.I. 50/2022](https://www.irishstatutebook.ie/eli/2022/si/50/made/en/pdf); [Anniversary Days Observance Act 1859](https://en.wikipedia.org/wiki/Anniversary_Days_Observance_Act_1859); Shulchan Arukh, Orach Chaim [631:3](https://www.sefaria.org/Shulchan_Arukh%2C_Orach_Chayim.631.3) (the sukkah's stars); Talmud, [Shabbat 21b](https://www.sefaria.org/Shabbat.21b) (the Hanukkah lamp in the window).
- Customs pages: [Hocktide](https://en.wikipedia.org/wiki/Hocktide); [Plough Monday](https://en.wikipedia.org/wiki/Plough_Monday); [Oak Apple Day](https://en.wikipedia.org/wiki/Oak_Apple_Day); [the Carhampton wassail](https://calendarcustoms.com/?p=1449); [the Burning of the Clavie](https://calendarcustoms.com/articles/burning-the-clavie/); [red-letter days](https://en.wikipedia.org/wiki/Red_letter_day) and [the Church of England's calendar](https://en.wikipedia.org/wiki/Calendar_of_saints_(Church_of_England)); the Dog Days in [Webster's 1913](https://gcide.gnu.org.ua/define/Dog%20days) and the [Old Farmer's Almanac](https://www.almanac.com/fact/dog-days-begin-the-phrase-dog-days-holiday).

### 7.6 Modern references (in copyright: cite, do not copy)

Ronald Hutton, *The Stations of the Sun: A History of the Ritual Year in Britain* (Oxford, 1996), the standard history
of nearly every British day above, and *The Triumph of the Moon* (1999) on the modern eightfold year; Steve Roud, *The
English Year* (2006); Edward M. Reingold and Nachum Dershowitz, *Calendrical Calculations* (4th ed., 2018) for the
Hebrew, Chinese, Hindu and Islamic algorithms; Jean Meeus, *Astronomical Algorithms* (2nd ed., 1998); Bernard Yallop,
NAO Technical Note 69 (1997) and Mohammad Odeh, *Experimental Astronomy* 18 (2004) on crescent visibility; Jack B.
Oruch, "St. Valentine, Chaucer, and Spring in February", *Speculum* 56 (1981); Máire MacNeill, *The Festival of
Lughnasa* (1962).

### 7.7 Reference images in `ref/`

Downloaded for drawing; all public domain or CC0, checked on their source pages.

| File | What it shows | Source | Licence |
| --- | --- | --- | --- |
| `book-chambers-clog-almanac-vol1-p9.jpg` | the clog almanac's four faces, with Plot's key to its signs | Chambers, *Book of Days* I p. 9 ([archive.org](https://archive.org/details/bookofdaysmiscel01chamuoft/page/n22/mode/1up)) | public domain (1863) |
| `book-hone-plough-monday.jpg` | the plough hauled through the street, the Bessy, the Fool, a drummer | Hone, *Every-Day Book* I, cols 71–2 ([Gutenberg](https://www.gutenberg.org/cache/epub/53275/images/illo0103.jpg)) | public domain (1826) |
| `book-hone-twelfth-day-cake-shop.jpg` | a pastrycook's window of Twelfth cakes | Hone I, cols 47–8 ([Gutenberg](https://www.gutenberg.org/cache/epub/53275/images/illo0075.jpg)) | public domain |
| `book-hone-wassail-bowl-headpiece.jpg` | the two-handled wassail bowl, "Wass heil / Drinc heile" | Hone II ([Gutenberg](https://www.gutenberg.org/cache/epub/53276/images/illo0023.jpg)) | public domain |
| `book-hone-may-day-sweeps-jack-in-the-green.jpg` | the sweeps' May Day with the leafy Jack-in-the-Green | Hone I, cols 583–4 ([Gutenberg](https://www.gutenberg.org/cache/epub/53275/images/illo0780.jpg)) | public domain |
| `book-hone-boars-head.jpg` | the boar's head on its dish | Hone I, cols 1619–20 ([Gutenberg](https://www.gutenberg.org/cache/epub/53275/images/illo2093.jpg)) | public domain |
| `book-chronograph354-december.png` | December of the Calendar of 354: dice and dice tower, torch, mask | [Commons](https://commons.wikimedia.org/wiki/File:Chronography_of_354_Mensis_December.png) (17th-century copy, Barberini lat. 2154) | PD-Art |
| `book-walters-w99-f12v-december-noel-gold.jpg` | a French Book of Hours' December: "Jour de noel" and the great feasts in gold among red and blue saints | Walters Art Museum W.99, fol. 12v ([digital Walters](https://www.thedigitalwalters.org/Data/WaltersManuscripts/W99/data/W.99/sap/W99_000028_sap.jpg)) | CC0 |
| `book-bcp1669-january-red-letter-days.jpg` | the Prayer Book's January: red-letter and black-letter days, the golden numbers | BCP (1669 printing), [archive.org](https://archive.org/details/bookofcommonpray00chur_14/page/n40/mode/1up) | public domain |
| `book-kalender-shepherdes-1503-december.jpg` | the Kalender's December: feasts in red, the saints' figures, pig-killing, Capricorn | Sommer's facsimile (1892), [archive.org](https://archive.org/details/kalenderofshephe00pyns/page/n147/mode/1up) | public domain |
| `book-kalender-shepherdes-1503-january.jpg`, `…-february.jpg`, `…-june.jpg`, `…-september.jpg`, `…-november.jpg` | the Kalender's January (the feaster, the Three Kings), February (Brigid, Candlemas, Valentine in red), June (the Baptist with the Lamb), September (the Holy Cross, Libra's balance, "Dies caniculares") and November (Clement's anchor, Catherine's wheel, Andrew's saltire) | Sommer's facsimile, archive.org [n136](https://archive.org/details/kalenderofshephe00pyns/page/n136/mode/1up), [n137](https://archive.org/details/kalenderofshephe00pyns/page/n137/mode/1up), [n141](https://archive.org/details/kalenderofshephe00pyns/page/n141/mode/1up), [n144](https://archive.org/details/kalenderofshephe00pyns/page/n144/mode/1up), [n146](https://archive.org/details/kalenderofshephe00pyns/page/n146/mode/1up) | public domain |
| `stick-plot1686-clog-tab35.png` | Plot's Tab. XXXV, "The Clog, or Stafford-shire Perpetuall Almanack": the four faces with every sign (4386×7432) | Plot (1686), from the Public Domain Mark PDF on [archive.org](https://archive.org/details/the-natural-history-of-stafford-shire-by-robert-plot) | public domain |
| `stick-worm1643-board-facies-prior-p100.jpg`, `…-posterior-p102.jpg` | Worm's two runic calendar boards with their pictograms (saints' heads, keys, a ship, a gridiron, a dog for the hunting season) | *Fasti Danici* (1643), [archive.org](https://archive.org/details/bub_gb_6X2ZKMQBcvIC) n119, n121 | Public Domain Mark |
| `stick-olausmagnus1555-de-baculis.jpg` | people reading runic calendar staves, faced suns in the corners | [Commons](https://upload.wikimedia.org/wikipedia/commons/d/d4/Olaus_Magnus_-_On_Runestaffs.jpg) | public domain |
| `stick-helland1900-primstav-vinterside.png`, `…-sommerside.png` | a primstav's two faces as a strip of tiny signs, numbered as in Helland's text (winter #1–29, summer #30–57) | Commons: [winter](https://upload.wikimedia.org/wikipedia/commons/f/f8/Norges_land_og_folk_-_Bratsberg_amt_1_-_Primstav_vinterside.png), [summer](https://upload.wikimedia.org/wikipedia/commons/0/0a/Norges_land_og_folk_-_Bratsberg_amt_1_-_Primstav_sommerside.png) | public domain |
| `stick-nf-primstav-drawing-NF05709-187-pdm.jpg` | "Den norske Prim-stav", an 18th-century drawing with each sign named | Norsk Folkemuseum NF.05709-187, [DigitaltMuseum](https://digitaltmuseum.no/011013375064) | Public Domain Mark |
| `stick-malma-runstav-pd.jpg` | a Swedish printed runic calendar rich in pictograms: drinking horns, a star, a candelabrum, a heart, keys, a wheel, a saltire, a ship | [Commons](https://commons.wikimedia.org/wiki/File:Runstav_från_Malma.tif) (National Archives of Sweden) | public domain |
| `stick-commons-primstav-detail-pd.jpg` | a photograph of a carved stick at the start of its summer side | [Commons](https://upload.wikimedia.org/wikipedia/commons/b/bd/Primstav-detail.jpg) | public domain (released by its author) |
| `world-qing-twelve-months-5th-month-dragon-boats.jpg` (991×1800) | the Qing court's fifth month: dragon boats on a river | [Commons](https://commons.wikimedia.org/wiki/File:清畫院畫十二月月令圖五月_軸.jpg) (NPM 故畫003110) | PD-Art |
| `world-hiroshige-tanabata-1857.jpg` (1253×1800) | Hiroshige, "The Tanabata Festival in the Flourishing City" | [Met 36541](https://www.metmuseum.org/art/collection/search/36541) | CC0 |
| `world-utamaro-moon-viewing-party-1801.jpg` | Utamaro, "Moon-Viewing Party": susuki in a vase, the full moon | [AIC 34789](https://www.artic.edu/artworks/34789) | CC0 |
| `world-krishna-celebrates-holi-c1770.jpg` (1800×1327) | "Krishna celebrates Holi", Pahari: the pichkari's jets | [Cleveland 2018.104](https://clevelandart.org/art/2018.104) | CC0 |
| `world-royal-women-celebrating-diwali-c1760.jpg` | "Royal Women Celebrating Diwali", Lucknow: rows of lamps | [Cleveland 1971.82](https://clevelandart.org/art/1971.82) | CC0 |
| `world-golden-haggadah-f15r-passover-preparations.jpg` | the Golden Haggadah, fol. 15r: round matzot, Miriam's dance | [Commons](https://commons.wikimedia.org/wiki/File:Dance_of_Marian._Full_F15_from_Golden_Haggadah.jpg) | PD-Art |
| `world-baraffael-hanukkah-lamp-1773.jpg` (1226×1800) | the Baraffael family Hanukkah lamp, Rome, 1773–75: eight spouts below a menorah | [Met 751313](https://www.metmuseum.org/art/collection/search/751313) | CC0 |
| `world-guaman-poma-june-inti-raymi-1615.jpg` | Guaman Poma's June: the Inca drinks with the Sun | [Royal Danish Library](https://poma.kb.dk/permalink/2006/poma/248/en/text/) | Public Domain Mark |

The four images marked with a size were scaled down to 1800 px from the museums' originals.
