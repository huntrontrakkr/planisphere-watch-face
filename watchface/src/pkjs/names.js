// The place's names for the ring, as ladders of ever shorter forms (the watch shows the longest that fits the room
// beside MIDNIGHT, which moves with the latitude): each form engraved (capitals, A-Z 0-9 . ' -), the forms joined by
// "|", longest first. The same rules are in proto/names.py; tools/check_names.py holds the two to the same answers.
//
// A city: its name; its generic words abbreviated as a gazetteer does (SAINT ST., FORT FT., MOUNT MT., PORT PT.,
// NORTH N. ...); its leading words cut to their initials (N. YORK); its last word cut back a syllable at a time, as
// atlases and library catalogues abbreviate (NORFOLK NORF., PHILADELPHIA PHILAD. PHIL.: after the consonants that
// close a syllable, a cluster of three or more leaving its last to the next, never under four letters, never to save
// less than two letters with its full stop); then its initials alone (N.Y.).
// The region beside it: in the United States, Canada and Australia the state or province, in the old newspaper style
// (VA., N.Y., CALIF., ONT., N.S.W.) and then its postal code (VA, NY, CA); elsewhere the country, cut back the same
// way (SWITZERLAND SWITZ.) and then its two-letter code. A hyphened name tries its first part alone first.

var CITY_CAP = 39, REGION_CAP = 27;                 // the watch keeps a ladder in 40 and 28 bytes

function engrave(s) {
  s = String(s || '');
  if (s.normalize) s = s.normalize('NFD').replace(/[̀-ͯ]/g, '');
  return s.toUpperCase().replace(/[^A-Z0-9 .'-]/g, '').replace(/\s+/g, ' ').replace(/^ | $/g, '');
}

var GENERIC = {SAINT: 'ST.', SAINTE: 'STE.', FORT: 'FT.', MOUNT: 'MT.', PORT: 'PT.', POINT: 'PT.', NORTH: 'N.',
               SOUTH: 'S.', EAST: 'E.', WEST: 'W.', SANTA: 'STA.'};

function vowel(c) { return 'AEIOUY'.indexOf(c) >= 0; }

// where a word may be cut: after the consonants closing each syllable (a cluster of three or more also after its
// first), keeping four letters at least and cutting three at least (the full stop takes one back)
function cuts(w) {
  var out = [], i = 0;
  while (i < w.length) {
    while (i < w.length && !vowel(w[i])) i++;
    while (i < w.length && vowel(w[i])) i++;
    var j = i;
    while (j < w.length && !vowel(w[j])) j++;
    if (j >= w.length) break;
    var at = j - i >= 3 ? [i + 1, j - 1] : [j];
    at.forEach(function (k) { if (k >= 4 && w.length - k >= 3 && out.indexOf(k) < 0) out.push(k); });
    i = j;
  }
  return out.sort(function (a, b) { return a - b; });
}

function initial(w) { return w[0] + '.'; }

// the forms joined, longest first, within `cap` characters: the longest left out first (no ring has room for a dozen
// letters), the shortest always kept
function join(forms, cap) {
  var seen = [], out = [];
  forms.forEach(function (f) {
    if (f && seen.indexOf(f) < 0 && (!out.length || f.length < out[out.length - 1].length)) { seen.push(f); out.push(f); }
  });
  if (out.length && out[0].length > cap) out[0] = out[0].slice(0, cap).replace(/ $/, '');
  while (out.length > 1 && out.join('|').length > cap) out.shift();
  return out.join('|');
}

function cityLadder(name) {
  name = engrave(name).replace(/\|/g, '');
  if (!name) return '';
  var words = name.split(' ');
  var forms = [name];
  var gen = words.length > 1 ? words.map(function (w) { return GENERIC[w] || w; }) : words;
  forms.push(gen.join(' '));
  for (var k = 1; k < gen.length; k++)
    forms.push(gen.slice(0, k).map(function (w) { return /\.$/.test(w) ? w : initial(w); }).concat(gen.slice(k)).join(' '));
  var lead = gen.slice(0, -1).map(function (w) { return /\.$/.test(w) ? w : initial(w); });
  var last = gen[gen.length - 1];
  if (/-/.test(last)) {                             // a hyphened name: its first part alone (STRATFORD-UPON-AVON)
    last = last.split('-')[0];
    forms.push(lead.concat([last]).join(' '));
  }
  if (!/\.$/.test(last))
    cuts(last).reverse().forEach(function (c) { forms.push(lead.concat([last.slice(0, c) + '.']).join(' ')); });
  if (words.length > 1) forms.push(words.map(initial).join(''));
  return join(forms, CITY_CAP);
}

// the states and provinces, as the old newspapers and the post give them
var REGIONS = {
  US: {ALABAMA: ['ALA.', 'AL'], ALASKA: ['ALASKA', 'AK'], ARIZONA: ['ARIZ.', 'AZ'], ARKANSAS: ['ARK.', 'AR'],
       CALIFORNIA: ['CALIF.', 'CA'], COLORADO: ['COLO.', 'CO'], CONNECTICUT: ['CONN.', 'CT'], DELAWARE: ['DEL.', 'DE'],
       'DISTRICT OF COLUMBIA': ['D.C.', 'DC'], FLORIDA: ['FLA.', 'FL'], GEORGIA: ['GA.', 'GA'], HAWAII: ['HAWAII', 'HI'],
       IDAHO: ['IDAHO', 'ID'], ILLINOIS: ['ILL.', 'IL'], INDIANA: ['IND.', 'IN'], IOWA: ['IOWA', 'IA'],
       KANSAS: ['KANS.', 'KS'], KENTUCKY: ['KY.', 'KY'], LOUISIANA: ['LA.', 'LA'], MAINE: ['MAINE', 'ME'],
       MARYLAND: ['MD.', 'MD'], MASSACHUSETTS: ['MASS.', 'MA'], MICHIGAN: ['MICH.', 'MI'], MINNESOTA: ['MINN.', 'MN'],
       MISSISSIPPI: ['MISS.', 'MS'], MISSOURI: ['MO.', 'MO'], MONTANA: ['MONT.', 'MT'], NEBRASKA: ['NEBR.', 'NE'],
       NEVADA: ['NEV.', 'NV'], 'NEW HAMPSHIRE': ['N.H.', 'NH'], 'NEW JERSEY': ['N.J.', 'NJ'],
       'NEW MEXICO': ['N.MEX.', 'NM'], 'NEW YORK': ['N.Y.', 'NY'], 'NORTH CAROLINA': ['N.C.', 'NC'],
       'NORTH DAKOTA': ['N.DAK.', 'ND'], OHIO: ['OHIO', 'OH'], OKLAHOMA: ['OKLA.', 'OK'], OREGON: ['OREG.', 'OR'],
       PENNSYLVANIA: ['PA.', 'PA'], 'RHODE ISLAND': ['R.I.', 'RI'], 'SOUTH CAROLINA': ['S.C.', 'SC'],
       'SOUTH DAKOTA': ['S.DAK.', 'SD'], TENNESSEE: ['TENN.', 'TN'], TEXAS: ['TEX.', 'TX'], UTAH: ['UTAH', 'UT'],
       VERMONT: ['VT.', 'VT'], VIRGINIA: ['VA.', 'VA'], WASHINGTON: ['WASH.', 'WA'], 'WEST VIRGINIA': ['W.VA.', 'WV'],
       WISCONSIN: ['WIS.', 'WI'], WYOMING: ['WYO.', 'WY'], 'PUERTO RICO': ['P.R.', 'PR']},
  CA: {ALBERTA: ['ALTA.', 'AB'], 'BRITISH COLUMBIA': ['B.C.', 'BC'], MANITOBA: ['MAN.', 'MB'],
       'NEW BRUNSWICK': ['N.B.', 'NB'], 'NEWFOUNDLAND AND LABRADOR': ['NFLD.', 'NL'], 'NOVA SCOTIA': ['N.S.', 'NS'],
       ONTARIO: ['ONT.', 'ON'], 'PRINCE EDWARD ISLAND': ['P.E.I.', 'PE'], QUEBEC: ['QUE.', 'QC'],
       SASKATCHEWAN: ['SASK.', 'SK'], YUKON: ['YUKON', 'YT'], 'NORTHWEST TERRITORIES': ['N.W.T.', 'NT'],
       NUNAVUT: ['NUNAVUT', 'NU']},
  AU: {'NEW SOUTH WALES': ['N.S.W.', 'NSW'], VICTORIA: ['VIC.', 'VIC'], QUEENSLAND: ['QLD.', 'QLD'],
       'SOUTH AUSTRALIA': ['S.A.', 'SA'], 'WESTERN AUSTRALIA': ['W.A.', 'WA'], TASMANIA: ['TAS.', 'TAS'],
       'NORTHERN TERRITORY': ['N.T.', 'NT'], 'AUSTRALIAN CAPITAL TERRITORY': ['A.C.T.', 'ACT']}
};

// the countries whose names are long, as a map's border would give them
var SHORT = {US: 'U.S.A.', AE: 'U.A.E.', RU: 'RUSSIA', KR: 'KOREA', KP: 'KOREA', IR: 'IRAN', VN: 'VIETNAM', TW: 'TAIWAN',
             BO: 'BOLIVIA', VE: 'VENEZUELA', TZ: 'TANZANIA', SY: 'SYRIA', LA: 'LAOS', MD: 'MOLDOVA', CZ: 'CZECHIA',
             NL: 'NETHERLANDS', PH: 'PHILIPPINES', DO: 'DOMINICAN REP.', CD: 'CONGO', CG: 'CONGO', GB: 'U.K.'};

// the region beside the city: `code` the country's ISO code, `region` the state's or province's name (or its own
// code: "US-VA"), `country` the country's name as it should read (or whatever the owner typed; none: the code's own)
function regionLadder(code, region, country) {
  code = String(code || '').toUpperCase();
  var states = REGIONS[code], r = engrave(region);
  if (states) {
    var sub = r.replace(/^[A-Z]{2}-/, '');
    for (var name in states)
      if (name === r || states[name][1] === sub) return join(states[name], REGION_CAP);
  }
  var c = engrave(String(country || '').split(/[(,]/)[0]) || engrave(SHORT[code] || '');
  if (!c) return '';
  var forms = cityLadder(c).split('|');
  if (/^[A-Z]{2}$/.test(code) && forms[forms.length - 1].length > 2) forms.push(code);
  return join(forms, REGION_CAP);
}

module.exports = {engrave: engrave, cityLadder: cityLadder, regionLadder: regionLadder, cuts: cuts, REGIONS: REGIONS,
                  SHORT: SHORT};
