/* Hero decoration: cartoon moments from Karnataka's history, Kadambas to
 * Wodeyars, drawn as inline SVG and cycled automatically. Independent of the
 * search (app.js). Captions and speech bubbles carry data-en/data-kn, so
 * app.js's language switch translates them like any other text.
 *
 * Every person is drawn with the same kit (figure/head below) so faces,
 * skin tones and dress stay consistent: South Indian skin tones; kings in a
 * kirita crown and dhoti (early dynasties), a kullayi cap (Vijayanagara) or a
 * Mysore peta and coat (Wodeyars); women in sarees with jasmine in the hair.
 */
(() => {
  const stage = document.getElementById('stage');
  if (!stage) return;

  // ------------------------------------------------------------------ kit
  const P = {
    skin: { light: '#d8a679', wheat: '#c98b5f', brown: '#b07650', deep: '#8e5636', euro: '#f1c9a7' },
    hair: '#221812', ink: '#221812', lip: '#7a3b2a', mouth: '#6b2d22',
    gold: '#f2b632', goldD: '#cf951a', red: '#d94a3d', maroon: '#8a2f2a', white: '#f7f1e3', cream: '#fbf6ea',
    saffron: '#ef8a22', green: '#2e8b57', blue: '#4f7fc0', wood: '#8a5a3b', steel: '#9aa6b5',
  };
  const svg = (w, body) => `<svg viewBox="0 0 ${w} ${w}" aria-hidden="true">${body}</svg>`;
  const at = (x, y, s, body, sx) => `<g transform="translate(${x} ${y}) scale(${sx ?? s} ${s})">${body}</g>`;
  const anim = (cls, body, origin) => (cls ? `<g class="${cls}"${origin ? ` style="transform-origin:${origin}"` : ''}>${body}</g>` : body);
  const rect = (x, y, w, h, fill, rx = 0) => `<rect x="${x}" y="${y}" width="${w}" height="${h}"${rx ? ` rx="${rx}"` : ''} fill="${fill}"/>`;

  const WEAR = {
    kirita: () => `<path d="M-26 -20 L-21 -58 L-9 -46 L0 -82 L9 -46 L21 -58 L26 -20Z" fill="${P.gold}" stroke="${P.goldD}" stroke-width="2" stroke-linejoin="round"/>${rect(-31, -28, 62, 11, '#e8a317', 4)}<circle cy="-22.5" r="3.6" fill="${P.red}"/><circle cy="-52" r="4.4" fill="${P.red}"/>`,
    crown: () => `<path d="M-27 -18 L-23 -44 L-12 -35 L0 -54 L12 -35 L23 -44 L27 -18Z" fill="${P.gold}" stroke="${P.goldD}" stroke-width="2" stroke-linejoin="round"/>${rect(-30, -26, 60, 10, '#e8a317', 4)}<circle cy="-21" r="3.4" fill="${P.red}"/>`,
    kullayi: () => `<path d="M-25 -16 q25 -112 50 0z" fill="#fbf6ea" stroke="#e2d6bd" stroke-width="2"/>${rect(-29, -24, 58, 10, P.gold, 4)}<circle cy="-19" r="3.4" fill="${P.red}"/>`,
    peta: (c) => `<path d="M-39 -4 q-6 -42 39 -46 q45 4 39 46 q-39 -14 -78 0z" fill="${c || '#f1e6cf'}"/><path d="M-37 -14 q37 -14 74 0 M-33 -28 q33 -12 66 0" stroke="${P.gold}" stroke-width="3.5" fill="none"/><path d="M2 -44 q-8 -14 2 -24 q0 12 4 24z" fill="${P.gold}"/><circle cx="2" cy="-37" r="4" fill="${P.red}"/>`,
    turban: (c) => `<path d="M-36 -6 q0 -34 36 -36 q36 2 36 34 q-36 -14 -72 2z" fill="${c || '#efe8d6'}"/><path d="M-28 -18 q28 -14 56 0" stroke="rgba(0,0,0,.13)" stroke-width="3" fill="none"/>`,
    maratha: (c) => `<path d="M-36 -6 q-2 -36 36 -38 q38 2 36 36 q-36 -12 -72 2z" fill="${c || '#e0782a'}"/><path d="M32 -12 q14 6 10 22" stroke="${c || '#e0782a'}" stroke-width="7" fill="none" stroke-linecap="round"/><path d="M-30 -20 q30 -12 60 0" stroke="${P.gold}" stroke-width="3" fill="none"/>`,
    tiara: () => `<path d="M-22 -22 l6 -14 l7 8 l9 -15 l9 15 l7 -8 l6 14z" fill="${P.gold}" stroke="${P.goldD}" stroke-width="1.4" stroke-linejoin="round"/><path d="M0 -20 v4" stroke="${P.gold}" stroke-width="1.6"/><circle cy="-14" r="2.6" fill="${P.red}"/>`,
    morion: () => `<path d="M-42 -8 q8 -6 16 -6 q2 -32 26 -34 q24 2 26 34 q8 0 16 6 q-42 -8 -84 0z" fill="#b8c0cc" stroke="#8d96a3" stroke-width="2"/><path d="M0 -48 q-2 -10 6 -14" stroke="#8d96a3" stroke-width="4" fill="none" stroke-linecap="round"/>`,
  };
  const MARK = {
    vibhuti: `<path d="M-11 -18 h22 M-11 -14 h22 M-11 -10 h22" stroke="#fff" stroke-width="2" stroke-linecap="round"/><circle cy="-14" r="2" fill="${P.red}"/>`,
    namam: `<path d="M-6 -19 v7 q6 6 12 0 v-7" stroke="#fff" stroke-width="2.4" fill="none" stroke-linecap="round"/><path d="M0 -19 v9" stroke="${P.red}" stroke-width="2.4" stroke-linecap="round"/>`,
    bindi: `<circle cy="-3" r="2.6" fill="${P.red}"/>`,
    tilak: `<path d="M0 -18 v9" stroke="${P.red}" stroke-width="3" stroke-linecap="round"/>`,
  };
  const BROWS = {
    calm: 'M-18 -7 q6 -4 12 0 M6 -7 q6 -4 12 0', fierce: 'M-19 -10 l12 5 M19 -10 l-12 5',
    worried: 'M-18 -6 l11 -4 M18 -6 l-11 -4', up: 'M-18 -11 q6 -4 12 0 M6 -11 q6 -4 12 0',
  };
  const STACHE = {
    handlebar: `<path d="M0 14 c-5 -5 -15 -5 -18 2 c-2 3 2 7 5 5 c-3 -1 -2 -4 0 -4 c5 0 8 2 13 -1 c5 3 8 1 13 1 c2 0 3 3 0 4 c3 2 7 -2 5 -5 c-3 -7 -13 -7 -18 -2z" fill="${P.ink}"/>`,
    thin: `<path d="M-11 15 q11 -6 22 0" stroke="${P.ink}" stroke-width="3.6" fill="none" stroke-linecap="round"/>`,
    full: `<path d="M-15 17 q15 -11 30 0 q-15 4 -30 0z" fill="${P.ink}"/>`,
  };

  function head(o) {
    const sk = o.skin, hr = o.hairColor || P.hair, hair = o.hair || 'short';
    let s = '';
    if (hair === 'long') s += `<path d="M-37 -2 a37 37 0 0 1 74 0 v62 q-37 10 -74 0z" fill="${hr}"/>`;
    if (hair === 'bun') s += `<circle cx="-31" cy="-14" r="14" fill="${hr}"/><g fill="#fff"><circle cx="-39" cy="-24" r="3.2"/><circle cx="-43" cy="-14" r="3.2"/><circle cx="-40" cy="-4" r="3.2"/></g>`;
    if (hair === 'jata') s += `<circle cy="-42" r="15" fill="${hr}"/><circle cy="-42" r="15" fill="none" stroke="#6b3a24" stroke-width="3.4" stroke-dasharray=".1 5.4" stroke-linecap="round"/>`;
    if (hair === 'sage') s += `<circle cy="-42" r="14" fill="${hr}"/>`;
    s += `<circle cx="-33" cy="2" r="7" fill="${sk}"/><circle cx="33" cy="2" r="7" fill="${sk}"/><circle r="34" fill="${sk}"/>`;
    if (o.studs !== false) s += `<circle cx="-34" cy="12" r="3.6" fill="${P.gold}"/><circle cx="34" cy="12" r="3.6" fill="${P.gold}"/>`;
    if (hair !== 'shikha' && hair !== 'bald') s += `<path d="M-34 -2 a34 34 0 0 1 68 0 q-12 -18 -34 -18 q-22 0 -34 18z" fill="${hr}"/>`;
    if (hair === 'bun' || hair === 'long') s += `<path d="M0 -33 v13" stroke="${sk}" stroke-width="2.2" stroke-linecap="round"/>`;
    if (hair === 'shikha') s += `<path d="M-4 -33 q4 -16 14 -8 q-6 -1 -8 8z" fill="${hr}"/>`;
    if (o.wear) s += WEAR[o.wear](o.wearColor);
    if (o.mark) s += MARK[o.mark];
    s += `<path d="${BROWS[o.brows || 'calm']}" stroke="${hair === 'sage' ? '#cfc8bb' : P.ink}" stroke-width="2.8" fill="none" stroke-linecap="round"/>`;
    s += o.eyes === 'closed'
      ? `<path d="M-16 3 q4 3 8 0 M8 3 q4 3 8 0" stroke="${P.ink}" stroke-width="2.4" fill="none" stroke-linecap="round"/>`
      : o.eyes === 'dizzy'
        ? `<path d="M-15 0 l6 6 M-9 0 l-6 6 M9 0 l6 6 M15 0 l-6 6" stroke="${P.ink}" stroke-width="2.2" stroke-linecap="round"/>`
        : `<g class="a-blink"><ellipse cx="-12" cy="3" rx="3.4" ry="4.3" fill="${P.ink}"/><ellipse cx="12" cy="3" rx="3.4" ry="4.3" fill="${P.ink}"/></g>`;
    s += `<path d="M-1 7 q4 4 -1 8" stroke="rgba(60,25,10,.28)" stroke-width="2" fill="none" stroke-linecap="round"/>`;
    if (o.nosering) s += `<circle cx="5" cy="14" r="3" fill="none" stroke="${P.gold}" stroke-width="1.5"/>`;
    if (o.beard) s += `<path d="M-27 6 q27 56 54 0 q-2 36 -27 44 q-25 -8 -27 -44z" fill="${hr}"/>`;
    if (o.stache) s += o.beard ? `<path d="M-14 16 q14 -9 28 0" stroke="${hr}" stroke-width="5" fill="none" stroke-linecap="round"/>` : STACHE[o.stache];
    const my = o.stache ? 25 : 23;
    const mouth = {
      smile: `<path d="M-7 ${my} q7 6 14 0" stroke="${P.lip}" stroke-width="2.6" fill="none" stroke-linecap="round"/>`,
      open: `<ellipse cy="${my + 2}" rx="5.5" ry="4.5" fill="${P.mouth}"/>`,
      talk: `<ellipse class="a-talk" cy="${my + 2}" rx="5" ry="4" fill="${P.mouth}"/>`,
      o: `<ellipse cy="${my + 2}" rx="3.2" ry="3.8" fill="${P.mouth}"/>`,
      grin: `<path d="M-9 ${my - 1} q9 11 18 0z" fill="#fff" stroke="${P.lip}" stroke-width="2" stroke-linejoin="round"/>`,
      flat: `<path d="M-6 ${my + 1} h12" stroke="${P.lip}" stroke-width="2.6" stroke-linecap="round"/>`,
    }[o.mouth || 'smile'];
    return s + mouth;
  }

  // Arms are drawn from the shoulder at (0,0) so the CSS rotation turns about it.
  const ARM = {
    down: ['M0 0 q10 22 8 46', 8, 46], hip: ['M0 0 q22 18 4 40', 4, 40], up: ['M0 0 q20 -20 24 -56', 24, -56],
    raise: ['M0 0 q20 -6 22 -42', 22, -42], fwd: ['M0 0 q22 8 44 -4', 44, -4], out: ['M0 0 q16 22 38 26', 38, 26],
    chest: ['M0 0 q16 24 -8 32', -8, 32], point: ['M0 0 q24 -4 42 -22', 42, -22], side: ['M0 0 q26 8 46 -16', 46, -16],
  };
  const ITEM = {
    sword: (x, y) => [`<path d="M${x - 3} ${y - 6} l4 -76 l6 6 l-2 70z" fill="#e6ecf2" stroke="${P.steel}" stroke-width="1.5"/>${rect(x - 11, y - 9, 22, 5, P.gold, 2.5)}`, ''],
    flag: (x, y, o) => [`<path d="M${x} ${y + 46} V${y - 98}" stroke="#7a5232" stroke-width="4"/><path class="a-flag" d="M${x + 2} ${y - 98} h52 l-9 14 l9 14 h-52z" fill="${o.flag || P.saffron}"/>`, ''],
    pestle: (x, y) => [`<path d="M${x - 30} ${y + 50} L${x + 24} ${y - 76}" stroke="#7a4a2e" stroke-width="9" stroke-linecap="round"/><path d="M${x + 18} ${y - 62} l7 -15" stroke="#5d6470" stroke-width="12" stroke-linecap="round"/>`, ''],
    linga: (x, y) => ['', `<ellipse cx="${x}" cy="${y - 9}" rx="5" ry="7" fill="#3a3a48"/>`],
    leaf: (x, y) => ['', `<rect x="${x - 24}" y="${y - 6}" width="48" height="11" rx="3" fill="#e8d7a3" stroke="#bfa86e"/><path d="M${x - 18} ${y - 1} h36" stroke="#9c8650" stroke-width="1.2"/>`],
    tambura: (x, y) => [`<path d="M${x + 4} ${y + 30} L${x + 16} ${y - 96}" stroke="${P.wood}" stroke-width="6" stroke-linecap="round"/><circle cx="${x + 2}" cy="${y + 40}" r="19" fill="#b07a4c"/><circle cx="${x + 2}" cy="${y + 40}" r="9" fill="#8a5a3b"/>`, ''],
    bow: (x, y) => ['', `<path d="M${x - 4} ${y - 52} q34 52 0 104" stroke="#7a4a2e" stroke-width="5" fill="none" stroke-linecap="round"/><path d="M${x - 4} ${y - 52} V${y + 52}" stroke="#e8e0cc" stroke-width="1.4"/>`],
    hammer: (x, y) => [`${rect(x - 3, y - 30, 6, 30, P.wood, 3)}${rect(x - 12, y - 40, 24, 12, '#6b7280', 3)}`, ''],
    kalasha: (x, y) => ['', `<path d="M${x - 13} ${y - 8} q13 -18 26 0 q5 16 -13 22 q-18 -6 -13 -22z" fill="${P.gold}" stroke="${P.goldD}" stroke-width="1.5"/>`],
    staff: (x, y) => [`<path d="M${x} ${y + 64} V${y - 70}" stroke="${P.wood}" stroke-width="5" stroke-linecap="round"/>`, ''],
    goad: (x, y) => [`<path d="M${x} ${y + 30} V${y - 40} q0 -10 8 -10" stroke="#6b7280" stroke-width="4" fill="none" stroke-linecap="round"/>`, ''],
    drumstick: (x, y) => [`<path d="M${x} ${y} l18 -18" stroke="${P.wood}" stroke-width="4" stroke-linecap="round"/>`, ''],
    // A Jain monk's peacock-feather whisk.
    pichhi: (x, y) => [`<path d="M${x} ${y + 8} L${x + 2} ${y - 26}" stroke="${P.wood}" stroke-width="3" stroke-linecap="round"/><path d="M${x - 11} ${y - 24} q13 -32 26 0 q-13 8 -26 0z" fill="#2f7d6a"/><circle cx="${x + 2}" cy="${y - 31}" r="5" fill="#1f4f9a"/><circle cx="${x + 2}" cy="${y - 31}" r="2.2" fill="${P.gold}"/>`, ''],
  };
  const SLEEVE = { robe: 'cloth', coat: 'cloth', monk: 'cloth', soldier: 'cloth', euro: 'cloth' };

  function arm(side, o) {
    const type = o['arm' + side];
    if (!type) return '';
    const [d, hx, hy] = ARM[type];
    const col = SLEEVE[o.attire] ? o.cloth : o.skin;
    const [behind, front] = o['hold' + side] ? ITEM[o['hold' + side]](hx, hy, o) : ['', ''];
    let s = `${behind}<path d="${d}" stroke="${col}" stroke-width="12" stroke-linecap="round" fill="none"/>`;
    if (o.attire === 'saree') s += `<circle cx="2" cy="5" r="8.5" fill="${o.blouse}"/>`;
    if (o.attire === 'king') s += `<path d="M2 14 l10 2" stroke="${P.gold}" stroke-width="4" stroke-linecap="round"/>`;
    s += `<circle cx="${hx}" cy="${hy}" r="7" fill="${o.skin}"/>${front}`;
    s = anim(o['anim' + side] ? `${o['anim' + side]} o0` : '', s);
    s = `<g transform="translate(28 -108)">${s}</g>`;
    return side === 'L' ? `<g transform="scale(-1 1)">${s}</g>` : s;
  }

  function upper(o) {
    const sk = o.skin, neck = rect(-9, -132, 18, 20, sk);
    const torso = 'M-30 -116 q30 -12 60 0 l7 62 h-74z';
    switch (o.attire) {
      case 'king': return `${neck}<path d="${torso}" fill="${sk}"/><path d="M-28 -112 l58 50 l-4 8 l-56 -48z" fill="${o.sash || P.red}"/><path d="M-14 -114 q14 22 28 0" stroke="${P.gold}" stroke-width="5" fill="none"/>${rect(-36, -62, 72, 10, P.gold, 4)}`;
      case 'commoner': return `${neck}<path d="${torso}" fill="${sk}"/>${o.thread ? `<path d="M-22 -114 l46 58" stroke="#fff" stroke-width="2"/>` : ''}<path d="M-28 -114 l16 -2 l40 56 l-12 4z" fill="${o.shawl || P.white}"/>${rect(-34, -60, 68, 8, o.sash || P.white, 3)}`;
      case 'robe': return `${neck}<path d="${torso}" fill="${o.cloth}"/><path d="M-14 -114 q14 18 28 0" stroke="#f3eee2" stroke-width="3.5" stroke-dasharray=".1 5" stroke-linecap="round" fill="none"/>${o.shawl ? `<path d="M-30 -114 q30 26 60 0 l3 12 q-33 30 -66 0z" fill="${o.shawl}"/>` : ''}${rect(-34, -64, 68, 9, o.sash || P.red, 3)}`;
      case 'monk': return `${neck}<path d="${torso}" fill="${o.cloth}"/><path d="M-26 -112 l52 56" stroke="rgba(255,255,255,.25)" stroke-width="6"/>`;
      case 'saree': return `${neck}<path d="M-26 -116 q26 -10 52 0 l4 46 h-60z" fill="${o.blouse}"/><path d="M-24 -114 l50 46 l-6 10 l-48 -42z" fill="${o.cloth}"/><path d="M-22 -116 l50 46" stroke="${o.border || P.gold}" stroke-width="3"/><path d="M-12 -114 q12 16 24 0" stroke="${P.gold}" stroke-width="3.5" fill="none"/>`;
      case 'coat': return `${neck}<path d="M-30 -118 q30 -10 60 0 l6 64 h-72z" fill="${o.cloth}"/>${rect(-12, -120, 24, 7, P.gold, 3)}<path d="M-28 -114 l56 52" stroke="${o.sash || P.green}" stroke-width="8"/><g fill="${P.gold}">${[-104, -92, -80, -68].map((y) => `<circle cx="0" cy="${y}" r="2.4"/>`).join('')}</g>`;
      case 'soldier': return `${neck}<path d="${torso}" fill="${o.cloth}"/>${rect(-36, -64, 72, 9, '#5a3a24', 3)}<path d="M-26 -112 l52 50" stroke="#e8dcc0" stroke-width="4"/>`;
      case 'euro': return `${rect(-9, -132, 18, 20, sk)}<path d="${torso}" fill="${o.cloth}"/><path d="M-26 -112 l52 52 M26 -112 l-52 52" stroke="#f4f1ea" stroke-width="4"/>`;
      default: return neck;
    }
  }

  function lower(o) {
    const feet = `<ellipse cx="-24" cy="-2" rx="12" ry="4.5" fill="#6b4128"/><ellipse cx="24" cy="-2" rx="12" ry="4.5" fill="#6b4128"/>`;
    switch (o.attire) {
      case 'king': return `${feet}<path d="M-32 -56 h64 l8 50 h-30 l-10 -30 l-10 30 h-30z" fill="${o.lower || P.white}"/><path d="M-40 -11 h30 v6 h-30z M10 -11 h30 v6 h-30z" fill="${o.hem || P.red}"/>`;
      case 'commoner':
      case 'soldier': return `${feet}${rect(-22, -30, 11, 28, o.skin, 4)}${rect(11, -30, 11, 28, o.skin, 4)}<path d="M-31 -58 h62 l4 32 h-26 l-9 -14 l-9 14 h-26z" fill="${o.lower || P.white}"/>`;
      case 'robe':
      case 'monk': return `${feet}<path d="M-37 -58 h74 l8 52 h-90z" fill="${o.cloth}"/>${o.attire === 'robe' ? rect(-45, -12, 90, 7, P.gold, 2) : ''}`;
      case 'saree': return `${feet}<path d="M-34 -72 h68 l12 66 h-92z" fill="${o.cloth}"/>${rect(-46, -14, 92, 9, o.border || P.gold, 2)}`;
      case 'coat': return `<ellipse cx="-14" cy="-3" rx="11" ry="5" fill="#1d1d24"/><ellipse cx="14" cy="-3" rx="11" ry="5" fill="#1d1d24"/>${rect(-22, -36, 18, 33, '#f7f3ea', 3)}${rect(4, -36, 18, 33, '#f7f3ea', 3)}<path d="M-37 -56 h74 l4 24 h-82z" fill="${o.cloth}"/>`;
      case 'euro': return `${rect(-22, -24, 18, 22, '#1d1d24', 3)}${rect(4, -24, 18, 22, '#1d1d24', 3)}${rect(-22, -58, 18, 36, '#f4f1ea', 3)}${rect(4, -58, 18, 36, '#f4f1ea', 3)}`;
      default: return '';
    }
  }

  /** A person, feet at (x, y). */
  function figure(o) {
    o = { s: 1, skin: P.skin.wheat, attire: 'king', cloth: P.cream, blouse: P.red, ...o };
    const top = upper(o) + (o.mala ? `<path d="M-17 -116 q17 30 34 0" stroke="#6b3a24" stroke-width="3.6" stroke-dasharray=".1 5" stroke-linecap="round" fill="none"/>` : '') +
      arm('L', o) + arm('R', o) + `<g transform="translate(0 -160)">${anim(o.nod ? 'a-nod' : '', head(o))}</g>`;
    const body = o.seated
      ? `<ellipse cy="-12" rx="48" ry="15" fill="${o.legs || (o.attire === 'saree' ? o.cloth : o.attire === 'robe' || o.attire === 'monk' ? o.cloth : P.white)}"/><g transform="translate(0 50)">${top}</g>`
      : lower(o) + top;
    return at(o.x, o.y, o.s, anim(o.move || '', body), o.flip ? -o.s : o.s);
  }

  // ------------------------------------------------------------ props
  const sun = (x, y, r, c = '#ffc55a') => `<circle class="a-pulse" cx="${x}" cy="${y}" r="${r}" fill="${c}"/>`;
  const cloud = (x, y, s = 1, slow) => anim(`a-drift${slow ? ' slow' : ''}`, at(x, y, s, `<g fill="#fff"><circle cx="0" cy="0" r="14"/><circle cx="18" cy="-8" r="18"/><circle cx="38" cy="1" r="12"/>${rect(-14, 0, 64, 13, '#fff', 6.5)}</g>`));
  const birds = (x, y, c = '#7a4a2a', slow) => anim(`a-birds${slow ? ' slow' : ''}`, `<g stroke="${c}" stroke-width="2.4" fill="none" stroke-linecap="round"><path class="a-flap" d="M${x} ${y} q6 -6 12 0 q6 -6 12 0"/><path class="a-flap" style="animation-delay:-.2s" d="M${x + 30} ${y + 16} q5 -5 10 0 q5 -5 10 0"/><path class="a-flap" style="animation-delay:-.1s" d="M${x - 18} ${y + 22} q4 -4 8 0 q4 -4 8 0"/></g>`);
  const ground = (y, c, c2) => `<path d="M0 ${y} Q200 ${y - 14} 400 ${y + 2} V400 H0Z" fill="${c}"/>${c2 ? `<path d="M0 ${y + 66} Q200 ${y + 46} 400 ${y + 70} V400 H0Z" fill="${c2}"/>` : ''}`;
  const water = (y, h, c = '#7db7de') => `${rect(0, y, 400, h, c)}<g class="a-flow" stroke="#fff" stroke-opacity=".7" stroke-width="3" stroke-linecap="round"><path d="M-40 ${y + h * 0.3} H440" stroke-dasharray="16 24"/><path d="M-40 ${y + h * 0.7} H440" stroke-dasharray="24 16"/></g>`;
  const boulder = (x, y, rx, ry, c) => `<ellipse cx="${x}" cy="${y}" rx="${rx}" ry="${ry}" fill="${c}"/>`;
  const palm = (x, y, s = 1, lean = 14) => at(x, y, s, `<path d="M0 0 q${lean / 2} -70 ${lean} -140" stroke="#8a5a3b" stroke-width="9" fill="none" stroke-linecap="round"/>${anim('a-sway', `<g transform="translate(${lean} -140)"><g fill="#4f9a4a">${[-150, -110, -60, -20, 20].map((a) => `<path d="M0 0 q${Math.cos(a * Math.PI / 180) * 30} ${Math.sin(a * Math.PI / 180) * 30 - 10} ${Math.cos(a * Math.PI / 180) * 58} ${Math.sin(a * Math.PI / 180) * 58 + 14} q${-Math.cos(a * Math.PI / 180) * 26} ${-Math.sin(a * Math.PI / 180) * 18} ${-Math.cos(a * Math.PI / 180) * 58} ${-Math.sin(a * Math.PI / 180) * 58 - 14}z"/>`).join('')}</g><circle cx="-5" cy="6" r="6" fill="#6f4a2a"/><circle cx="6" cy="7" r="6" fill="#7d5532"/></g>`, '50% 100%')}`);
  const areca = (x, y, s = 1) => at(x, y, s, `<path d="M0 0 V-150" stroke="#9c8a6a" stroke-width="5"/>${anim('a-sway', `<g transform="translate(0 -150)" fill="#5a9a4c">${[-140, -100, -40, 0, -70].map((a) => `<path d="M0 0 q${Math.cos(a * Math.PI / 180) * 18} ${Math.sin(a * Math.PI / 180) * 18 - 6} ${Math.cos(a * Math.PI / 180) * 36} ${Math.sin(a * Math.PI / 180) * 36 + 10} q${-Math.cos(a * Math.PI / 180) * 16} -4 ${-Math.cos(a * Math.PI / 180) * 36} ${-Math.sin(a * Math.PI / 180) * 36 - 10}z"/>`).join('')}<circle cx="0" cy="8" r="5" fill="#e0a43a"/></g>`, '50% 100%')}`);
  const tree = (x, y, s = 1, c = '#5f9e4f', flowers) => at(x, y, s, `<path d="M0 0 V-80 M0 -50 l-18 -22 M0 -60 l16 -18" stroke="#7a5232" stroke-width="9" stroke-linecap="round"/><g fill="${c}"><circle cx="0" cy="-104" r="40"/><circle cx="-34" cy="-82" r="28"/><circle cx="34" cy="-84" r="28"/></g>${flowers ? `<g fill="#f6a21a">${flowers.map(([fx, fy], i) => `<circle class="a-twinkle" style="animation-delay:-${(i * 0.37).toFixed(2)}s" cx="${fx}" cy="${fy}" r="6"/>`).join('')}</g>` : ''}`);
  const stars = (pts) => `<g fill="#fff">${pts.map(([x, y], i) => `<circle class="a-twinkle" style="animation-delay:-${(i * 0.41).toFixed(2)}s" cx="${x}" cy="${y}" r="2"/>`).join('')}</g>`;
  const crenel = (x0, x1, y, c, w = 12) => `<path d="M${x0} ${y} H${x1}" stroke="${c}" stroke-width="${w}" stroke-dasharray="${w + 2} ${w - 2}"/>`;
  const banner = (x, y, h, c, emblem, ec = '#8a3a2b') => `${rect(x - 2.5, y, 5, h, '#7a5232')}<circle cx="${x}" cy="${y - 2}" r="5" fill="${P.gold}"/>${anim('a-flag', `<path d="M${x + 2} ${y + 4} h66 l-11 19 l11 19 h-66z" fill="${c}"/>${emblem ? at(x + 32, y + 24, 1, `<g fill="${ec}" color="${ec}">${EMBLEM[emblem]}</g>`) : ''}`)}`;
  const EMBLEM = {
    boar: '<path d="M-22 4 q4 -12 20 -12 q10 0 16 6 l7 -2 l-2 6 q2 6 -4 8 h-4 v6 h-4 v-6 h-14 v6 h-4 v-6 q-8 -2 -11 -6z"/>',
    lion: '<circle cx="12" cy="-4" r="9"/><rect x="-16" y="-6" width="28" height="11" rx="5"/><rect x="-14" y="2" width="4" height="9"/><rect x="5" y="2" width="4" height="9"/><path d="M-16 -2 q-9 -3 -6 -12" stroke="currentColor" stroke-width="2.5" fill="none"/>',
    elephant: '<ellipse cx="-3" cy="0" rx="14" ry="9"/><circle cx="11" cy="-3" r="7"/><path d="M16 -1 q4 7 0 11" stroke="currentColor" stroke-width="3.5" fill="none" stroke-linecap="round"/><rect x="-13" y="4" width="5" height="8"/><rect x="3" y="4" width="5" height="8"/>',
  };
  function dravida(x, y, s, c1 = '#d9a87a', c2 = '#c48d5f') {
    return at(x, y, s, `${rect(-64, -22, 128, 22, c2)}${rect(-50, -84, 100, 62, c1)}<path d="M-38 -84 v62 M-14 -84 v62 M14 -84 v62 M38 -84 v62" stroke="${c2}" stroke-width="3"/><path d="M-12 -22 v-36 q12 -14 24 0 v36z" fill="#6e4a32"/><path d="M-60 -84 h120 l-12 -18 h-96z" fill="${c2}"/><path d="M-44 -102 h88 l-10 -18 h-68z" fill="${c1}"/><path d="M-30 -120 h60 l-9 -16 h-42z" fill="${c2}"/><path d="M-20 -136 q20 -34 40 0z" fill="${c1}"/>${rect(-3, -176, 6, 10, P.gold, 2)}`);
  }
  function elephant(o) {
    const c = o.color || '#9aa3b8', d = o.dark || '#8690a6', w = o.walk ? ' slow' : '';
    const leg = (x, col, cls) => anim(o.walk ? cls + w : '', rect(x, -36, 18, 36, col, 6));
    let s = leg(-46, d, 'a-legb') + leg(18, d, 'a-legf') + `<path d="M-60 -64 q-12 10 -10 26" stroke="${c}" stroke-width="4" fill="none" stroke-linecap="round"/>` +
      `<ellipse cx="0" cy="-62" rx="62" ry="40" fill="${c}"/>` + leg(-26, c, 'a-legf') + leg(38, c, 'a-legb') +
      `<circle cx="56" cy="-74" r="30" fill="${c}"/><ellipse cx="40" cy="-72" rx="16" ry="25" fill="${d}"/>` +
      anim('a-trunk', `<path d="M80 -66 q16 22 6 50 q-3 8 -10 4" stroke="${c}" stroke-width="13" fill="none" stroke-linecap="round"/>`, '0% 0%') +
      `<path d="M74 -52 q14 6 20 -4" stroke="#fffaf0" stroke-width="5" fill="none" stroke-linecap="round"/><circle cx="66" cy="-82" r="3" fill="#2b2b38"/>`;
    if (o.cloth) s += `<path d="M-36 -100 h68 v42 q-34 12 -68 0z" fill="${o.cloth}"/><path d="M-36 -58 q34 12 68 0" stroke="${P.gold}" stroke-width="4" fill="none"/><path d="M50 -104 q12 14 26 2 l-6 30 q-8 4 -14 -2z" fill="${P.gold}"/>`;
    if (o.ambari) s += `<circle class="a-pulse" cx="0" cy="-130" r="44" fill="#ffd36b" opacity=".35"/><path d="M-30 -100 v-34 h60 v34z" fill="${P.gold}" stroke="${P.goldD}" stroke-width="2"/><path d="M-36 -134 h72 l-8 -10 h-56z" fill="${P.goldD}"/><path d="M-22 -144 q22 -36 44 0z" fill="${P.gold}" stroke="${P.goldD}" stroke-width="2"/><circle cy="-182" r="5" fill="${P.gold}"/><path d="M-20 -128 h40 M-20 -116 h40" stroke="${P.goldD}" stroke-width="2"/>`;
    return at(o.x, o.y, o.s || 1, anim(o.walk ? 'a-plod' : '', s), o.flip ? -(o.s || 1) : (o.s || 1));
  }
  function horse(o) {
    const c = o.color || '#8b5a3c';
    const leg = (x, col, cls) => anim(cls, rect(x, -54, 12, 54, col, 5));
    const s = anim('a-tail', `<path d="M-60 -76 q-34 -6 -46 26 q18 -12 46 -16z" fill="#3b2418"/>`) + leg(-46, '#74472f', 'a-legb') + leg(-26, '#7a4d33', 'a-legf') + leg(24, '#74472f', 'a-legb') + leg(42, '#7a4d33', 'a-legf') +
      `<ellipse cx="0" cy="-68" rx="62" ry="28" fill="${c}"/><path d="M34 -76 l30 -52 l24 10 l-20 52z" fill="${c}"/><path d="M60 -130 q22 -10 42 8 l6 12 q-4 9 -15 7 l-33 -6z" fill="${c}"/><path d="M66 -130 l4 -14 l8 12z" fill="${c}"/><circle cx="82" cy="-124" r="2.6" fill="#1f1712"/><path d="M58 -128 q-16 22 -26 54 l9 -2 q8 -30 24 -48z" fill="#3b2418"/><path d="M-36 -94 h64 l-6 36 h-52z" fill="${o.cloth || P.red}"/><path d="M-32 -62 h50" stroke="${P.gold}" stroke-width="4"/>`;
    return at(o.x, o.y, o.s || 1, anim(o.gallop ? 'a-gallop' : '', s + (o.rider || '')), o.flip ? -(o.s || 1) : (o.s || 1));
  }
  // A tiger rearing up on its hind legs, facing left, feet at (0,0).
  function tiger(x, y, s) {
    const O = '#f08a24', D = '#cf6a14', K = '#2e1c12', W = '#fff4e2';
    const tail = 'M30 -38 q46 -4 46 -54 q0 -14 -10 -18';
    // Stripes start at the back edge of the tilted body and curl inward.
    const stripes = [-34, -12, 10, 32].map((t) => {
      const w = 30 * Math.sqrt(1 - (t / 62) ** 2) - 1;
      return `M${(10 - t * 0.423 + w * 0.906).toFixed(1)} ${(-80 - t * 0.906 - w * 0.423).toFixed(1)} q-8 -2 -17 7`;
    }).join(' ');
    return at(x, y, s, anim('a-pounce', `${anim('a-tail', `<path d="${tail}" stroke="${O}" stroke-width="11" fill="none" stroke-linecap="round"/><path d="${tail}" stroke="${K}" stroke-width="11" fill="none" stroke-dasharray="4 11"/>`, '0% 100%')}
    <path d="M18 -40 q10 18 9 36" stroke="${D}" stroke-width="18" stroke-linecap="round" fill="none"/><ellipse cx="29" cy="-3" rx="12" ry="5.5" fill="${D}"/>
    <path d="M-4 -116 q-30 -14 -54 -22" stroke="${D}" stroke-width="15" stroke-linecap="round" fill="none"/><circle cx="-60" cy="-139" r="10" fill="${D}"/>
    <ellipse cx="10" cy="-80" rx="30" ry="62" fill="${O}" transform="rotate(-25 10 -80)"/><ellipse cx="-4" cy="-76" rx="14" ry="48" fill="${W}" transform="rotate(-25 -4 -76)"/>
    <path d="${stripes}" stroke="${K}" stroke-width="5.5" fill="none" stroke-linecap="round"/>
    <path d="M-2 -42 q-4 20 -8 38" stroke="${O}" stroke-width="20" stroke-linecap="round" fill="none"/><ellipse cx="-14" cy="-3" rx="13" ry="6" fill="${O}"/>
    <path d="M-15 -28 h10 M-16 -16 h10" stroke="${K}" stroke-width="4" stroke-linecap="round"/>
    <path d="M-2 -104 q-30 4 -54 0" stroke="${O}" stroke-width="16" stroke-linecap="round" fill="none"/><circle cx="-57" cy="-104" r="10.5" fill="${O}"/>
    <path d="M-24 -111 v13 M-37 -110 v12" stroke="${K}" stroke-width="4" stroke-linecap="round"/>
    <path d="M-66 -110 l-6 -3 M-68 -104 h-6 M-66 -98 l-6 3 M-68 -144 l-6 -2 M-69 -137 h-6" stroke="#fff" stroke-width="2.4" stroke-linecap="round"/>
    <circle cx="-16" cy="-172" r="9" fill="${O}"/><circle cx="-16" cy="-172" r="4.5" fill="${K}"/><circle cx="-43" cy="-174" r="9" fill="${O}"/><circle cx="-43" cy="-174" r="4.5" fill="${K}"/>
    <circle cx="-30" cy="-150" r="27" fill="${O}"/>
    <ellipse cx="-19" cy="-135" rx="11" ry="9" fill="${W}"/><ellipse cx="-45" cy="-138" rx="16" ry="12" fill="${W}"/>
    <path d="M-30 -176 v10 M-38 -175 l2 8 M-22 -175 l-2 8 M-4 -157 h-8 M-4 -147 h-8" stroke="${K}" stroke-width="3.4" stroke-linecap="round"/>
    <ellipse cx="-43" cy="-153" rx="4.6" ry="3.8" fill="#f6e04b"/><ellipse cx="-24" cy="-153" rx="4.6" ry="3.8" fill="#f6e04b"/><circle cx="-44" cy="-153" r="2.2" fill="${K}"/><circle cx="-25" cy="-153" r="2.2" fill="${K}"/>
    <path d="M-50 -161 l11 4 M-17 -161 l-11 4" stroke="${K}" stroke-width="3.2" stroke-linecap="round"/>
    <path d="M-55 -146 h11 l-5.5 7z" fill="${K}"/>
    <path d="M-60 -135 q11 16 24 2z" fill="#7a2b22"/><path d="M-56 -134 l2.2 6 l2.2 -6 M-43 -134 l2.2 6 l2.2 -6" fill="#fff"/>`));
  }
  const hound = (x, y, s, delay) => at(x, y, s, anim('a-run', `<g class="a-legf"><rect x="-22" y="-24" width="6" height="24" rx="3" fill="#8a5a33"/></g><g class="a-legb"><rect x="14" y="-24" width="6" height="24" rx="3" fill="#8a5a33"/></g>
    <path d="M26 -34 q12 -6 12 -20" stroke="#a0703f" stroke-width="5" fill="none" stroke-linecap="round"/><ellipse cx="0" cy="-32" rx="30" ry="12" fill="#a0703f"/>
    <g class="a-legb"><rect x="-14" y="-24" width="6" height="24" rx="3" fill="#a0703f"/></g><g class="a-legf"><rect x="20" y="-24" width="6" height="24" rx="3" fill="#a0703f"/></g>
    <circle cx="-30" cy="-44" r="12" fill="#a0703f"/><ellipse cx="-42" cy="-40" rx="9" ry="6" fill="#a0703f"/><circle cx="-50" cy="-41" r="2.6" fill="#2b2118"/>
    <path d="M-26 -54 q8 4 6 16" stroke="#7a4f2a" stroke-width="7" fill="none" stroke-linecap="round"/><circle cx="-34" cy="-47" r="3.4" fill="#fff"/><circle cx="-35" cy="-47" r="1.8" fill="#2b2118"/>`, '').replace('class="a-run"', `class="a-run" style="animation-delay:${delay || 0}s"`));
  const hare = (x, y, s) => at(x, y, s, anim('a-hop', `<ellipse cx="-12" cy="-52" rx="4.5" ry="15" fill="#cfc8ba" transform="rotate(-20 -12 -52)"/><ellipse cx="-4" cy="-52" rx="4.5" ry="15" fill="#d8d2c6" transform="rotate(10 -4 -52)"/>
    <ellipse cx="4" cy="-20" rx="20" ry="13" fill="#d8d2c6"/><circle cx="-12" cy="-30" r="10" fill="#d8d2c6"/><circle cx="22" cy="-22" r="5" fill="#fff"/>
    <circle cx="-16" cy="-32" r="2" fill="#2b2118"/><path d="M-16 -38 l5 3" stroke="#2b2118" stroke-width="2" stroke-linecap="round"/><path d="M-6 -8 l-12 6 M10 -8 l12 4" stroke="#cfc8ba" stroke-width="6" stroke-linecap="round"/>`));
  const stoneSlab = (lines, label, bg = '#efe4d0') => `${rect(0, 0, 200, 200, bg)}${rect(0, 156, 200, 44, '#d8c7a6')}<path d="M46 160 V60 q0 -26 48 -26 q48 0 48 26 V160z" fill="#b8ab95"/><path d="M52 156 V62 q0 -20 42 -20 q42 0 42 20 V156z" fill="#cdc1ac"/>
    <g stroke="#6e6252" stroke-width="4" stroke-linecap="round" fill="none">${lines.map((w, i) => `<path class="a-draw" style="--i:${i}" pathLength="1" d="M62 ${68 + i * 16} h${w}"/>`).join('')}</g>
    <path d="M124 132 l18 -20 l5 5 l-18 20z" fill="#6b7280"/><circle cx="146" cy="116" r="8" fill="${P.skin.wheat}"/>
    <g class="a-spark"><path d="M120 136 l-8 -2 M122 142 l-8 6 M126 144 l0 8" stroke="#f5b301" stroke-width="2.5" stroke-linecap="round"/></g>
    <g class="a-tap" style="transform-origin: 100% 50%">${rect(146, 88, 18, 12, '#6b7280', 3)}${rect(162, 91, 28, 6, P.wood, 3)}</g>
    <text x="96" y="184" text-anchor="middle" font-family="Inter, sans-serif" font-size="13" font-weight="800" fill="#8a7a62">${label}</text>`;
  const notes = (x, y) => `<g fill="#7a4a9a">${[0, 1, 2].map((i) => `<g class="a-note" style="animation-delay:-${i * 1.1}s"><path d="M${x + i * 14} ${y} v-16 l10 -3 v14" stroke="#7a4a9a" stroke-width="2.2" fill="none"/><ellipse cx="${x + i * 14 - 2}" cy="${y}" rx="4" ry="3"/><ellipse cx="${x + i * 14 + 8}" cy="${y - 3}" rx="4" ry="3"/></g>`).join('')}</g>`;

  // ------------------------------------------------------------- scenes
  const LEGACY = {"pulakeshiBig": "<rect width=\"400\" height=\"400\" fill=\"#fdecd8\"/><circle class=\"a-pulse\" cx=\"292\" cy=\"92\" r=\"32\" fill=\"#ffc55a\"/><g class=\"a-drift\" fill=\"#fff\"><circle cx=\"86\" cy=\"96\" r=\"14\"/><circle cx=\"104\" cy=\"88\" r=\"18\"/><circle cx=\"124\" cy=\"97\" r=\"12\"/><rect x=\"72\" y=\"96\" width=\"64\" height=\"13\" rx=\"6.5\"/></g><g class=\"a-drift slow\" fill=\"#fff\" opacity=\".8\"><circle cx=\"196\" cy=\"146\" r=\"10\"/><circle cx=\"210\" cy=\"140\" r=\"13\"/><circle cx=\"224\" cy=\"147\" r=\"9\"/><rect x=\"186\" y=\"146\" width=\"46\" height=\"10\" rx=\"5\"/></g><path d=\"M0 212 Q60 168 128 196 T262 186 T400 182 V230 H0Z\" fill=\"#efd3aa\"/><rect y=\"222\" width=\"400\" height=\"40\" fill=\"#dccf94\"/><rect y=\"258\" width=\"400\" height=\"44\" fill=\"#7db7de\"/><g class=\"a-flow\" stroke=\"#fff\" stroke-opacity=\".75\" stroke-width=\"3\" stroke-linecap=\"round\"><path d=\"M-40 270 H440\" stroke-dasharray=\"16 24\"/><path d=\"M-40 288 H440\" stroke-dasharray=\"24 16\"/></g><path d=\"M0 298 Q200 284 400 300 V400 H0Z\" fill=\"#acd07c\"/><path d=\"M0 366 Q200 344 400 370 V400 H0Z\" fill=\"#95bf64\"/><!-- Harshavardhana's elephant, far bank, turning for home --><g transform=\"translate(250 196)\"><g class=\"a-puff\"><circle cx=\"-2\" cy=\"56\" r=\"7\" fill=\"#efe4bd\"/></g><g class=\"a-puff p2\"><circle cx=\"-12\" cy=\"50\" r=\"5\" fill=\"#efe4bd\"/></g><g class=\"a-trot\"><g class=\"a-legb\"><rect x=\"14\" y=\"44\" width=\"10\" height=\"16\" rx=\"3\" fill=\"#7f899f\"/></g><g class=\"a-legf\"><rect x=\"28\" y=\"44\" width=\"10\" height=\"16\" rx=\"3\" fill=\"#7f899f\"/></g><g class=\"a-legf\"><rect x=\"46\" y=\"44\" width=\"10\" height=\"16\" rx=\"3\" fill=\"#8690a6\"/></g><g class=\"a-legb\"><rect x=\"58\" y=\"44\" width=\"10\" height=\"16\" rx=\"3\" fill=\"#8690a6\"/></g><path d=\"M8 34 q-8 2 -10 12\" stroke=\"#9aa3b8\" stroke-width=\"3\" fill=\"none\" stroke-linecap=\"round\"/><ellipse cx=\"38\" cy=\"36\" rx=\"32\" ry=\"20\" fill=\"#9aa3b8\"/><circle cx=\"70\" cy=\"28\" r=\"15\" fill=\"#9aa3b8\"/><path d=\"M80 32 q14 -4 12 -22\" stroke=\"#9aa3b8\" stroke-width=\"7\" fill=\"none\" stroke-linecap=\"round\"/><ellipse cx=\"62\" cy=\"30\" rx=\"8\" ry=\"11\" fill=\"#8690a6\"/><circle cx=\"74\" cy=\"24\" r=\"2\" fill=\"#2b2b38\"/><path d=\"M20 18 h36 v16 q-18 8 -36 0z\" fill=\"#d94a3d\"/><path d=\"M20 32 q18 8 36 0\" stroke=\"#f2b632\" stroke-width=\"3\" fill=\"none\"/><path d=\"M30 19 q9 -16 18 0z\" fill=\"#f3e3b5\"/><circle cx=\"39\" cy=\"2\" r=\"10\" fill=\"#d39a6c\"/><path d=\"M30 -4 l3 -9 l3 6 l3 -8 l3 8 l3 -6 l3 9z\" fill=\"#f2b632\"/><circle cx=\"35\" cy=\"2\" r=\"1.6\" fill=\"#2b2118\"/><circle cx=\"43\" cy=\"2\" r=\"1.6\" fill=\"#2b2118\"/><path d=\"M32 -1 l4 -2 M46 -1 l-4 -2\" stroke=\"#2b2118\" stroke-width=\"1.4\" stroke-linecap=\"round\"/><ellipse cx=\"39\" cy=\"7.5\" rx=\"2\" ry=\"2.4\" fill=\"#7a3b2a\"/></g><g class=\"a-tumble\"><path d=\"M14 -24 q14 -14 28 0z\" fill=\"#fff6dc\" stroke=\"#f2b632\" stroke-width=\"2\"/><path d=\"M28 -24 v14\" stroke=\"#7a5232\" stroke-width=\"2\"/></g></g><!-- Chalukya boar banner --><rect x=\"41\" y=\"118\" width=\"5\" height=\"282\" fill=\"#7a5232\"/><circle cx=\"43.5\" cy=\"116\" r=\"6\" fill=\"#f2b632\"/><g class=\"a-flag\"><path d=\"M46 126 h72 l-12 22 l12 22 h-72z\" fill=\"#f2b632\"/><path d=\"M56 156 q4 -12 20 -12 q10 0 16 6 l7 -2 l-2 6 q2 6 -4 8 h-4 v6 h-4 v-6 h-14 v6 h-4 v-6 q-8 -2 -11 -6z\" fill=\"#8a3a2b\"/></g><!-- Pulakeshi II --><g class=\"a-bob\"><path d=\"M108 326 h66 l8 58 h-30 l-7 -36 -7 36 h-30z\" fill=\"#f6efe0\"/><path d=\"M100 378 h30 v6 h-30z M152 378 h30 v6 h-30z\" fill=\"#d94a3d\"/><ellipse cx=\"116\" cy=\"390\" rx=\"14\" ry=\"5\" fill=\"#8a5a3b\"/><ellipse cx=\"166\" cy=\"390\" rx=\"14\" ry=\"5\" fill=\"#8a5a3b\"/><path d=\"M110 262 q31 -12 62 0 l6 58 h-74z\" fill=\"#c68a5e\"/><path d=\"M112 266 l64 46 l-4 8 l-62 -44z\" fill=\"#d94a3d\"/><path d=\"M122 262 q19 22 38 0\" fill=\"none\" stroke=\"#f2b632\" stroke-width=\"5\"/><rect x=\"104\" y=\"318\" width=\"74\" height=\"12\" rx=\"4\" fill=\"#f2b632\"/><path d=\"M114 270 q-18 14 -14 30\" stroke=\"#c68a5e\" stroke-width=\"13\" stroke-linecap=\"round\" fill=\"none\"/><circle cx=\"98\" cy=\"304\" r=\"26\" fill=\"#a8473b\" stroke=\"#f2b632\" stroke-width=\"4\"/><circle cx=\"98\" cy=\"304\" r=\"7\" fill=\"#f2b632\"/><g class=\"a-swing\" style=\"transform-origin: 0% 100%\"><path d=\"M170 272 q22 -20 26 -54\" stroke=\"#c68a5e\" stroke-width=\"13\" stroke-linecap=\"round\" fill=\"none\"/><path d=\"M193 208 l4 -84 l6 6 l-2 78z\" fill=\"#e6ecf2\" stroke=\"#9aa6b5\" stroke-width=\"1.5\"/><rect x=\"186\" y=\"206\" width=\"22\" height=\"6\" rx=\"3\" fill=\"#f2b632\"/><circle cx=\"196\" cy=\"218\" r=\"8\" fill=\"#c68a5e\"/></g><rect x=\"130\" y=\"248\" width=\"20\" height=\"16\" fill=\"#b67c52\"/><circle cx=\"100\" cy=\"226\" r=\"7\" fill=\"#b67c52\"/><circle cx=\"180\" cy=\"226\" r=\"7\" fill=\"#b67c52\"/><circle cx=\"140\" cy=\"222\" r=\"40\" fill=\"#c68a5e\"/><circle cx=\"100\" cy=\"238\" r=\"4\" fill=\"#f2b632\"/><circle cx=\"180\" cy=\"238\" r=\"4\" fill=\"#f2b632\"/><path d=\"M102 214 q38 -28 76 0 v-10 q-38 -24 -76 0z\" fill=\"#2b2118\"/><path d=\"M108 206 L114 168 L126 180 L140 140 L154 180 L166 168 L172 206 Z\" fill=\"#f2b632\" stroke=\"#d69a1c\" stroke-width=\"2\" stroke-linejoin=\"round\"/><rect x=\"104\" y=\"198\" width=\"72\" height=\"12\" rx=\"4\" fill=\"#e8a317\"/><circle cx=\"140\" cy=\"204\" r=\"4\" fill=\"#d94a3d\"/><circle cx=\"140\" cy=\"168\" r=\"5\" fill=\"#d94a3d\"/><path d=\"M118 214 l14 4 M162 214 l-14 4\" stroke=\"#2b2118\" stroke-width=\"4\" stroke-linecap=\"round\"/><g class=\"a-blink\"><ellipse cx=\"126\" cy=\"226\" rx=\"4\" ry=\"5\" fill=\"#2b2118\"/><ellipse cx=\"154\" cy=\"226\" rx=\"4\" ry=\"5\" fill=\"#2b2118\"/></g><path d=\"M140 241 c-6 -6 -18 -6 -22 2 c-2 4 2 8 6 6 c-4 -1 -3 -5 0 -5 c6 0 10 2 16 -1 c6 3 10 1 16 1 c3 0 4 4 0 5 c4 2 8 -2 6 -6 c-4 -8 -16 -8 -22 -2z\" fill=\"#2b2118\"/><path d=\"M132 253 q8 6 16 0\" stroke=\"#7a3b2a\" stroke-width=\"3\" fill=\"none\" stroke-linecap=\"round\"/></g>", "pulakeshiSmall": "<rect width=\"200\" height=\"200\" fill=\"#efe4d0\"/><rect y=\"156\" width=\"200\" height=\"44\" fill=\"#d8c7a6\"/><rect x=\"46\" y=\"36\" width=\"96\" height=\"124\" rx=\"10\" fill=\"#b8ab95\"/><rect x=\"52\" y=\"42\" width=\"84\" height=\"112\" rx=\"7\" fill=\"#cdc1ac\"/><g stroke=\"#6e6252\" stroke-width=\"4\" stroke-linecap=\"round\" fill=\"none\"><path class=\"a-draw\" style=\"--i:0\" pathLength=\"1\" d=\"M62 60 h64\"/><path class=\"a-draw\" style=\"--i:1\" pathLength=\"1\" d=\"M62 76 h56\"/><path class=\"a-draw\" style=\"--i:2\" pathLength=\"1\" d=\"M62 92 h64\"/><path class=\"a-draw\" style=\"--i:3\" pathLength=\"1\" d=\"M62 108 h48\"/><path class=\"a-draw\" style=\"--i:4\" pathLength=\"1\" d=\"M62 124 h60\"/></g><path d=\"M124 132 l18 -20 l5 5 l-18 20z\" fill=\"#6b7280\"/><circle cx=\"146\" cy=\"116\" r=\"8\" fill=\"#c68a5e\"/><g class=\"a-spark\"><path d=\"M120 136 l-8 -2 M122 142 l-8 6 M126 144 l0 8\" stroke=\"#f5b301\" stroke-width=\"2.5\" stroke-linecap=\"round\"/></g><g class=\"a-tap\" style=\"transform-origin: 100% 50%\"><rect x=\"146\" y=\"88\" width=\"18\" height=\"12\" rx=\"3\" fill=\"#6b7280\"/><rect x=\"162\" y=\"91\" width=\"28\" height=\"6\" rx=\"3\" fill=\"#8a5a3b\"/></g><text x=\"96\" y=\"182\" text-anchor=\"middle\" font-family=\"Inter, sans-serif\" font-size=\"13\" font-weight=\"700\" fill=\"#8a7a62\">AIHOLE · 634</text>", "basavaBig": "<rect width=\"400\" height=\"400\" fill=\"#f8ead5\"/><path d=\"M193 76 q7 -28 14 0z\" fill=\"#f2b632\"/><path d=\"M74 112 h252 l-26 -38 h-200z\" fill=\"#b07a4c\"/><path d=\"M30 150 h340 l-34 -40 h-272z\" fill=\"#8f603b\"/><rect x=\"30\" y=\"148\" width=\"340\" height=\"10\" fill=\"#7a5232\"/><g fill=\"#d6b88b\"><rect x=\"58\" y=\"158\" width=\"20\" height=\"150\"/><rect x=\"128\" y=\"158\" width=\"20\" height=\"150\"/><rect x=\"252\" y=\"158\" width=\"20\" height=\"150\"/><rect x=\"322\" y=\"158\" width=\"20\" height=\"150\"/></g><g fill=\"#c39e6c\"><rect x=\"52\" y=\"158\" width=\"32\" height=\"10\" rx=\"2\"/><rect x=\"122\" y=\"158\" width=\"32\" height=\"10\" rx=\"2\"/><rect x=\"246\" y=\"158\" width=\"32\" height=\"10\" rx=\"2\"/><rect x=\"316\" y=\"158\" width=\"32\" height=\"10\" rx=\"2\"/><rect x=\"52\" y=\"296\" width=\"32\" height=\"12\" rx=\"2\"/><rect x=\"122\" y=\"296\" width=\"32\" height=\"12\" rx=\"2\"/><rect x=\"246\" y=\"296\" width=\"32\" height=\"12\" rx=\"2\"/><rect x=\"316\" y=\"296\" width=\"32\" height=\"12\" rx=\"2\"/></g><rect y=\"306\" width=\"400\" height=\"94\" fill=\"#d9b98c\"/><rect y=\"306\" width=\"400\" height=\"8\" fill=\"#c9a676\"/><g class=\"a-hang\"><path d=\"M200 158 L190 190 M200 158 L210 190\" stroke=\"#7a5232\" stroke-width=\"1.6\"/><path d=\"M184 190 h32 l-6 10 h-20z\" fill=\"#f2b632\"/><path class=\"a-flicker\" d=\"M200 174 q-6 8 0 15 q6 -7 0 -15z\" fill=\"#ff8a3d\"/></g><!-- a vachanakara --><ellipse cx=\"100\" cy=\"332\" rx=\"36\" ry=\"11\" fill=\"#d99a4e\"/><path d=\"M72 332 q4 -48 28 -52 q24 4 28 52z\" fill=\"#e8b468\"/><circle cx=\"100\" cy=\"306\" r=\"6.5\" fill=\"#c08458\"/><g class=\"a-nod\" style=\"animation-delay:-1.2s\"><path d=\"M76 258 a24 24 0 0 1 48 0 v44 q-24 8 -48 0z\" fill=\"#2b2118\"/><circle cx=\"100\" cy=\"258\" r=\"23\" fill=\"#c08458\"/><path d=\"M77 258 a23 23 0 0 1 46 0 q-10 -12 -23 -12 q-13 0 -23 12z\" fill=\"#2b2118\"/><circle cx=\"100\" cy=\"252\" r=\"2.4\" fill=\"#d94a3d\"/><g class=\"a-blink\"><circle cx=\"92\" cy=\"261\" r=\"2.6\" fill=\"#2b2118\"/><circle cx=\"108\" cy=\"261\" r=\"2.6\" fill=\"#2b2118\"/></g><path d=\"M95 270 q5 4 10 0\" stroke=\"#7a3b2a\" stroke-width=\"2\" fill=\"none\" stroke-linecap=\"round\"/></g><!-- Basavanna --><ellipse cx=\"200\" cy=\"332\" rx=\"50\" ry=\"13\" fill=\"#efe6d4\"/><path d=\"M162 332 q6 -60 38 -64 q32 4 38 64z\" fill=\"#fbf7ee\"/><path d=\"M176 278 q24 22 48 0 l5 10 q-29 26 -58 0z\" fill=\"#f08a24\"/><path d=\"M188 276 q12 22 24 0\" stroke=\"#7a3b2a\" stroke-width=\"3.2\" stroke-dasharray=\"0.1 5\" stroke-linecap=\"round\" fill=\"none\"/><ellipse cx=\"200\" cy=\"300\" rx=\"4\" ry=\"5\" fill=\"#3a3a48\"/><path d=\"M190 322 q10 -16 20 0 q-10 6 -20 0z\" fill=\"#b9825a\"/><g class=\"a-nod\"><rect x=\"192\" y=\"256\" width=\"16\" height=\"16\" fill=\"#a8734d\"/><circle cx=\"200\" cy=\"236\" r=\"30\" fill=\"#b9825a\"/><circle cx=\"200\" cy=\"202\" r=\"11\" fill=\"#2b2118\"/><path d=\"M170 236 a30 30 0 0 1 60 0 q-12 -16 -30 -16 q-18 0 -30 16z\" fill=\"#2b2118\"/><path d=\"M176 246 q24 34 48 0 q-2 22 -24 26 q-22 -4 -24 -26z\" fill=\"#2b2118\"/><path d=\"M189 226 h22 M189 230.5 h22 M189 235 h22\" stroke=\"#fff\" stroke-width=\"2\" stroke-linecap=\"round\"/><circle cx=\"200\" cy=\"230.5\" r=\"2\" fill=\"#d94a3d\"/><g class=\"a-blink\"><circle cx=\"190\" cy=\"243\" r=\"3\" fill=\"#2b2118\"/><circle cx=\"210\" cy=\"243\" r=\"3\" fill=\"#2b2118\"/></g><path d=\"M194 257 q6 4 12 0\" stroke=\"#e8c4a0\" stroke-width=\"2\" fill=\"none\" stroke-linecap=\"round\"/></g><!-- a farmer speaking up --><ellipse cx=\"300\" cy=\"332\" rx=\"36\" ry=\"11\" fill=\"#d7d0bf\"/><path d=\"M272 332 q4 -48 28 -52 q24 4 28 52z\" fill=\"#5f8fc9\"/><circle cx=\"288\" cy=\"306\" r=\"6.5\" fill=\"#a86b45\"/><g class=\"a-wave\" style=\"transform-origin: 0% 100%\"><path d=\"M318 298 q14 -20 12 -50\" stroke=\"#5f8fc9\" stroke-width=\"11\" stroke-linecap=\"round\" fill=\"none\"/><circle cx=\"330\" cy=\"244\" r=\"7.5\" fill=\"#a86b45\"/></g><g class=\"a-nod\" style=\"animation-delay:-2s\"><circle cx=\"300\" cy=\"258\" r=\"23\" fill=\"#a86b45\"/><path d=\"M276 256 q0 -28 24 -30 q24 2 24 30 q-24 -12 -48 0z\" fill=\"#ece5d3\"/><path d=\"M282 246 q18 -10 36 0\" stroke=\"#d6cdb6\" stroke-width=\"2.5\" fill=\"none\"/><g class=\"a-blink\"><circle cx=\"292\" cy=\"262\" r=\"2.6\" fill=\"#2b2118\"/><circle cx=\"308\" cy=\"262\" r=\"2.6\" fill=\"#2b2118\"/></g><path d=\"M290 269 q10 -5 20 0\" stroke=\"#2b2118\" stroke-width=\"3.5\" fill=\"none\" stroke-linecap=\"round\"/><ellipse class=\"a-talk\" cx=\"300\" cy=\"275\" rx=\"3.2\" ry=\"2.6\" fill=\"#6b2d22\"/></g>", "basavaSmall": "<rect width=\"200\" height=\"200\" fill=\"#e6ecfb\"/><g fill=\"#f5b301\"><path class=\"a-twinkle\" d=\"M40 50 l3 8 l8 3 l-8 3 l-3 8 l-3 -8 l-8 -3 l8 -3z\"/><path class=\"a-twinkle\" style=\"animation-delay:-.7s\" d=\"M160 118 l2.5 6 l6 2.5 l-6 2.5 l-2.5 6 l-2.5 -6 l-6 -2.5 l6 -2.5z\"/><path class=\"a-twinkle\" style=\"animation-delay:-1.4s\" d=\"M48 112 l2 5 l5 2 l-5 2 l-2 5 l-2 -5 l-5 -2 l5 -2z\"/></g><g class=\"a-lift\"><rect x=\"78\" y=\"44\" width=\"28\" height=\"96\" rx=\"14\" fill=\"#c68a5e\"/><rect x=\"83\" y=\"48\" width=\"18\" height=\"22\" rx=\"8\" fill=\"#e8b896\"/><path d=\"M92 50 v30\" stroke=\"#4b2a7a\" stroke-width=\"5\" stroke-linecap=\"round\"/><path d=\"M62 210 v-70 q0 -14 14 -14 h56 q14 0 14 14 v70z\" fill=\"#c68a5e\"/><path d=\"M106 130 q24 -2 32 14 M108 150 h30 M108 168 h30\" stroke=\"#b07650\" stroke-width=\"3\" fill=\"none\" stroke-linecap=\"round\"/><path d=\"M66 156 q-4 -22 18 -24\" stroke=\"#b07650\" stroke-width=\"3\" fill=\"none\" stroke-linecap=\"round\"/></g><g class=\"a-bob\"><circle cx=\"150\" cy=\"66\" r=\"18\" fill=\"#0f8a5f\"/><path d=\"M142 66 l6 6 l11 -12\" stroke=\"#fff\" stroke-width=\"4\" fill=\"none\" stroke-linecap=\"round\" stroke-linejoin=\"round\"/></g>", "hampiBig": "<rect width=\"400\" height=\"400\" fill=\"#fde3c4\"/><rect y=\"150\" width=\"400\" height=\"140\" fill=\"#fbd2a4\"/><circle class=\"a-pulse\" cx=\"124\" cy=\"118\" r=\"30\" fill=\"#ffb547\"/><g class=\"a-birds\" stroke=\"#7a4a2a\" stroke-width=\"2.5\" fill=\"none\" stroke-linecap=\"round\"><path class=\"a-flap\" d=\"M260 80 q6 -6 12 0 q6 -6 12 0\"/><path class=\"a-flap\" style=\"animation-delay:-.2s\" d=\"M292 98 q5 -5 10 0 q5 -5 10 0\"/><path class=\"a-flap\" style=\"animation-delay:-.1s\" d=\"M240 104 q4 -4 8 0 q4 -4 8 0\"/></g><path d=\"M0 250 q30 -70 80 -60 q20 -40 60 -20 q30 -30 70 0 q40 -20 70 10 q40 -30 120 20 V300 H0z\" fill=\"#d7a06d\"/><ellipse cx=\"60\" cy=\"244\" rx=\"44\" ry=\"28\" fill=\"#c58a57\"/><ellipse cx=\"44\" cy=\"208\" rx=\"22\" ry=\"18\" fill=\"#d29864\"/><ellipse cx=\"338\" cy=\"238\" rx=\"42\" ry=\"30\" fill=\"#c58a57\"/><ellipse cx=\"356\" cy=\"198\" rx=\"24\" ry=\"20\" fill=\"#d29864\"/><ellipse cx=\"334\" cy=\"170\" rx=\"13\" ry=\"11\" fill=\"#c58a57\"/><rect y=\"288\" width=\"400\" height=\"112\" fill=\"#e9c58f\"/><path d=\"M0 340 Q200 324 400 344 V400 H0Z\" fill=\"#dfb57b\"/><!-- the stone chariot --><rect x=\"186\" y=\"262\" width=\"128\" height=\"40\" rx=\"4\" fill=\"#b9a58a\"/><path d=\"M194 272 h112 M194 282 h112 M194 292 h112\" stroke=\"#a6927a\" stroke-width=\"2\"/><rect x=\"204\" y=\"214\" width=\"92\" height=\"50\" fill=\"#c7b398\"/><path d=\"M238 264 v-30 q12 -14 24 0 v30z\" fill=\"#7d6a52\"/><path d=\"M196 214 h108 l-10 -14 h-88z\" fill=\"#b9a58a\"/><path d=\"M210 200 h80 l-10 -16 h-60z\" fill=\"#c7b398\"/><path d=\"M224 184 h52 l-10 -16 h-32z\" fill=\"#b9a58a\"/><path d=\"M244 168 q6 -20 12 0z\" fill=\"#f2b632\"/><g class=\"a-spin\"><circle cx=\"214\" cy=\"300\" r=\"22\" fill=\"#a99377\" stroke=\"#7d6a52\" stroke-width=\"4\"/><path d=\"M214 280 v40 M194 300 h40 M200 286 l28 28 M228 286 l-28 28\" stroke=\"#7d6a52\" stroke-width=\"3\"/><circle cx=\"214\" cy=\"300\" r=\"6\" fill=\"#7d6a52\"/></g><g class=\"a-spin\"><circle cx=\"286\" cy=\"300\" r=\"22\" fill=\"#a99377\" stroke=\"#7d6a52\" stroke-width=\"4\"/><path d=\"M286 280 v40 M266 300 h40 M272 286 l28 28 M300 286 l-28 28\" stroke=\"#7d6a52\" stroke-width=\"3\"/><circle cx=\"286\" cy=\"300\" r=\"6\" fill=\"#7d6a52\"/></g><!-- Krishnadevaraya --><g class=\"a-bob\"><path d=\"M82 284 q28 -12 56 0 l14 100 h-84z\" fill=\"#fbf6ea\"/><rect x=\"68\" y=\"376\" width=\"84\" height=\"8\" fill=\"#f2b632\"/><rect x=\"80\" y=\"318\" width=\"62\" height=\"10\" rx=\"3\" fill=\"#d94a3d\"/><path d=\"M86 292 q-10 30 -4 52\" stroke=\"#fbf6ea\" stroke-width=\"13\" stroke-linecap=\"round\" fill=\"none\"/><circle cx=\"82\" cy=\"346\" r=\"7\" fill=\"#c68a5e\"/><g class=\"a-point\" style=\"transform-origin: 0% 100%\"><path d=\"M134 300 q24 -6 40 -22\" stroke=\"#fbf6ea\" stroke-width=\"13\" stroke-linecap=\"round\" fill=\"none\"/><circle cx=\"178\" cy=\"274\" r=\"7\" fill=\"#c68a5e\"/></g><rect x=\"102\" y=\"268\" width=\"16\" height=\"18\" fill=\"#b67c52\"/><path d=\"M98 286 q12 12 24 0\" stroke=\"#f3eee2\" stroke-width=\"3.5\" stroke-dasharray=\"0.1 5\" stroke-linecap=\"round\" fill=\"none\"/><circle cx=\"110\" cy=\"250\" r=\"32\" fill=\"#c68a5e\"/><circle cx=\"78\" cy=\"256\" r=\"4\" fill=\"#f2b632\"/><circle cx=\"142\" cy=\"256\" r=\"4\" fill=\"#f2b632\"/><path d=\"M84 240 q26 -110 52 0z\" fill=\"#fbf6ea\" stroke=\"#e7dcc4\" stroke-width=\"2\"/><rect x=\"80\" y=\"230\" width=\"60\" height=\"10\" rx=\"4\" fill=\"#f2b632\"/><circle cx=\"110\" cy=\"235\" r=\"3.5\" fill=\"#d94a3d\"/><g class=\"a-blink\"><circle cx=\"100\" cy=\"252\" r=\"3.2\" fill=\"#2b2118\"/><circle cx=\"120\" cy=\"252\" r=\"3.2\" fill=\"#2b2118\"/></g><path d=\"M96 266 q7 -6 14 -1 q7 -5 14 1\" stroke=\"#2b2118\" stroke-width=\"4\" fill=\"none\" stroke-linecap=\"round\"/><path d=\"M104 272 q6 4 12 0\" stroke=\"#7a3b2a\" stroke-width=\"2.5\" fill=\"none\" stroke-linecap=\"round\"/></g>", "hampiSmall": "<rect width=\"200\" height=\"200\" fill=\"#d5e9f4\"/><ellipse cx=\"34\" cy=\"98\" rx=\"52\" ry=\"20\" fill=\"#c58a57\"/><ellipse cx=\"172\" cy=\"100\" rx=\"42\" ry=\"15\" fill=\"#d29864\"/><rect y=\"100\" width=\"200\" height=\"100\" fill=\"#7db7de\"/><ellipse class=\"a-ripple\" cx=\"100\" cy=\"150\" rx=\"60\" ry=\"14\" fill=\"none\" stroke=\"#fff\" stroke-width=\"2\"/><ellipse class=\"a-ripple r2\" cx=\"100\" cy=\"150\" rx=\"60\" ry=\"14\" fill=\"none\" stroke=\"#fff\" stroke-width=\"2\"/><g class=\"a-rock\"><g class=\"a-paddle\" style=\"transform-origin: 0% 0%\"><path d=\"M112 118 L146 166\" stroke=\"#8a5a3b\" stroke-width=\"4\" stroke-linecap=\"round\"/><ellipse cx=\"146\" cy=\"168\" rx=\"5\" ry=\"10\" fill=\"#8a5a3b\" transform=\"rotate(-35 146 168)\"/></g><path d=\"M90 140 v-24 q10 -6 20 0 v24z\" fill=\"#f6efe0\"/><circle cx=\"100\" cy=\"100\" r=\"12\" fill=\"#a86b45\"/><path d=\"M88 98 q12 -16 24 0 q-12 -5 -24 0z\" fill=\"#d94a3d\"/><circle cx=\"105\" cy=\"101\" r=\"1.8\" fill=\"#2b2118\"/><path d=\"M108 120 l6 -2\" stroke=\"#a86b45\" stroke-width=\"6\" stroke-linecap=\"round\"/><ellipse cx=\"100\" cy=\"140\" rx=\"48\" ry=\"13\" fill=\"#8a5a3b\"/><path d=\"M52 140 q48 36 96 0z\" fill=\"#6f4529\"/><path d=\"M58 141 q42 30 84 0\" stroke=\"#9c6b43\" stroke-width=\"2\" stroke-dasharray=\"4 4\" fill=\"none\"/></g>", "kitturBig": "<rect width=\"400\" height=\"400\" fill=\"#e3f1ec\"/><g class=\"a-drift\" fill=\"#fff\"><circle cx=\"250\" cy=\"82\" r=\"13\"/><circle cx=\"267\" cy=\"74\" r=\"17\"/><circle cx=\"286\" cy=\"83\" r=\"11\"/><rect x=\"236\" y=\"82\" width=\"62\" height=\"12\" rx=\"6\"/></g><path d=\"M0 236 q80 -40 160 -14 q90 -36 240 6 V300 H0z\" fill=\"#bfdcae\"/><rect y=\"228\" width=\"400\" height=\"74\" fill=\"#d6b48a\"/><path d=\"M0 222 H400\" stroke=\"#d6b48a\" stroke-width=\"14\" stroke-dasharray=\"18 12\"/><path d=\"M250 302 v-36 q15 -18 30 0 v36z\" fill=\"#8f6b46\"/><rect x=\"30\" y=\"160\" width=\"60\" height=\"142\" fill=\"#caa478\"/><path d=\"M30 154 H90\" stroke=\"#caa478\" stroke-width=\"12\" stroke-dasharray=\"12 8\"/><rect x=\"318\" y=\"176\" width=\"56\" height=\"126\" fill=\"#caa478\"/><path d=\"M318 170 H374\" stroke=\"#caa478\" stroke-width=\"12\" stroke-dasharray=\"12 8\"/><rect x=\"58\" y=\"104\" width=\"4\" height=\"52\" fill=\"#7a5232\"/><path class=\"a-flag\" d=\"M62 106 h46 l-8 14 l8 14 h-46z\" fill=\"#f08a24\"/><rect y=\"300\" width=\"400\" height=\"100\" fill=\"#a9cc77\"/><path d=\"M0 362 Q200 342 400 366 V400 H0Z\" fill=\"#95bf64\"/><!-- the Company soldier, losing his hat --><g class=\"a-fly\"><rect x=\"318\" y=\"226\" width=\"18\" height=\"20\" rx=\"2\" fill=\"#23232f\"/><rect x=\"314\" y=\"244\" width=\"26\" height=\"5\" rx=\"2\" fill=\"#23232f\"/><path d=\"M327 226 q-4 -12 4 -16 q2 8 -1 16z\" fill=\"#d94a3d\"/></g><g transform=\"translate(330 330) rotate(-26)\"><g class=\"a-wobble\"><rect x=\"-12\" y=\"0\" width=\"10\" height=\"34\" rx=\"4\" fill=\"#f4f1ea\"/><rect x=\"2\" y=\"0\" width=\"10\" height=\"34\" rx=\"4\" fill=\"#f4f1ea\"/><rect x=\"-16\" y=\"-36\" width=\"32\" height=\"40\" rx=\"8\" fill=\"#c8352b\"/><path d=\"M-14 -34 l28 36 M14 -34 l-28 36\" stroke=\"#f4f1ea\" stroke-width=\"4\"/><circle cx=\"0\" cy=\"-50\" r=\"15\" fill=\"#f1c9a7\"/><path d=\"M-7 -55 l4 4 M-3 -55 l-4 4 M3 -55 l4 4 M7 -55 l-4 4\" stroke=\"#2b2118\" stroke-width=\"1.8\" stroke-linecap=\"round\"/><ellipse cx=\"0\" cy=\"-43\" rx=\"3\" ry=\"3.5\" fill=\"#7a3b2a\"/></g></g><!-- Rani Chennamma on horseback --><g class=\"a-gallop\"><g class=\"a-tail\"><path d=\"M112 292 q-34 -6 -46 26 q18 -12 46 -16z\" fill=\"#3b2418\"/></g><g class=\"a-legb\"><rect x=\"126\" y=\"314\" width=\"12\" height=\"54\" rx=\"5\" fill=\"#74472f\"/></g><g class=\"a-legf\"><rect x=\"146\" y=\"314\" width=\"12\" height=\"54\" rx=\"5\" fill=\"#7a4d33\"/></g><g class=\"a-legb\"><rect x=\"196\" y=\"314\" width=\"12\" height=\"54\" rx=\"5\" fill=\"#74472f\"/></g><g class=\"a-legf\"><rect x=\"214\" y=\"314\" width=\"12\" height=\"54\" rx=\"5\" fill=\"#7a4d33\"/></g><ellipse cx=\"172\" cy=\"300\" rx=\"62\" ry=\"28\" fill=\"#8b5a3c\"/><path d=\"M206 292 l30 -52 l24 10 l-20 52z\" fill=\"#8b5a3c\"/><path d=\"M232 238 q22 -10 42 8 l6 12 q-4 9 -15 7 l-33 -6z\" fill=\"#8b5a3c\"/><path d=\"M238 238 l4 -14 l8 12z\" fill=\"#8b5a3c\"/><circle cx=\"254\" cy=\"244\" r=\"2.6\" fill=\"#1f1712\"/><path d=\"M230 240 q-16 22 -26 54 l9 -2 q8 -30 24 -48z\" fill=\"#3b2418\"/><path d=\"M136 274 h64 l-6 36 h-52z\" fill=\"#d94a3d\"/><path d=\"M140 306 h50\" stroke=\"#f2b632\" stroke-width=\"4\"/><path d=\"M140 278 q24 -10 50 0 l6 26 q-32 10 -62 0z\" fill=\"#2e8b57\"/><path d=\"M134 302 q31 10 62 0\" stroke=\"#d94a3d\" stroke-width=\"5\" fill=\"none\"/><path d=\"M150 232 q20 -8 40 0 l6 48 h-52z\" fill=\"#2e8b57\"/><path d=\"M152 234 l42 44 l-8 4 l-38 -40z\" fill=\"#d94a3d\"/><path d=\"M158 244 q30 14 60 22\" stroke=\"#2e8b57\" stroke-width=\"10\" stroke-linecap=\"round\" fill=\"none\"/><circle cx=\"220\" cy=\"266\" r=\"6\" fill=\"#b77b52\"/><path d=\"M226 266 l20 -14\" stroke=\"#3b2418\" stroke-width=\"1.8\"/><g class=\"a-swing\" style=\"transform-origin: 0% 100%\"><path d=\"M186 240 q18 -16 22 -46\" stroke=\"#2e8b57\" stroke-width=\"11\" stroke-linecap=\"round\" fill=\"none\"/><path d=\"M206 186 l30 -66 l5 8 l-27 62z\" fill=\"#e6ecf2\" stroke=\"#9aa6b5\" stroke-width=\"1.5\"/><rect x=\"198\" y=\"184\" width=\"22\" height=\"6\" rx=\"3\" fill=\"#f2b632\" transform=\"rotate(24 209 187)\"/><circle cx=\"208\" cy=\"194\" r=\"7\" fill=\"#b77b52\"/></g><rect x=\"164\" y=\"216\" width=\"14\" height=\"16\" fill=\"#a86d47\"/><circle cx=\"146\" cy=\"190\" r=\"13\" fill=\"#1f1712\"/><circle cx=\"170\" cy=\"198\" r=\"28\" fill=\"#b77b52\"/><path d=\"M142 196 a28 28 0 0 1 56 0 q-6 -14 -24 -16 q-20 0 -32 16z\" fill=\"#1f1712\"/><path d=\"M156 172 l6 -10 l6 6 l6 -9 l6 9 l6 -6 l4 10z\" fill=\"#f2b632\"/><circle cx=\"176\" cy=\"186\" r=\"2.4\" fill=\"#d94a3d\"/><path d=\"M170 190 l9 2 M186 190 l8 -1\" stroke=\"#1f1712\" stroke-width=\"2.6\" stroke-linecap=\"round\"/><g class=\"a-blink\"><circle cx=\"176\" cy=\"198\" r=\"3\" fill=\"#1f1712\"/><circle cx=\"190\" cy=\"198\" r=\"3\" fill=\"#1f1712\"/></g><circle cx=\"195\" cy=\"207\" r=\"2.6\" fill=\"none\" stroke=\"#f2b632\" stroke-width=\"1.6\"/><ellipse cx=\"184\" cy=\"213\" rx=\"5\" ry=\"3.6\" fill=\"#7a2b22\"/><circle cx=\"150\" cy=\"206\" r=\"3.4\" fill=\"#f2b632\"/></g>", "kitturSmall": "<rect width=\"200\" height=\"200\" fill=\"#fdebd2\"/><g class=\"a-birds slow\" stroke=\"#7a4a2a\" stroke-width=\"2\" fill=\"none\" stroke-linecap=\"round\"><path class=\"a-flap\" d=\"M150 40 q5 -5 10 0 q5 -5 10 0\"/><path class=\"a-flap\" style=\"animation-delay:-.2s\" d=\"M170 58 q4 -4 8 0 q4 -4 8 0\"/></g><rect y=\"150\" width=\"200\" height=\"50\" fill=\"#a9cc77\"/><rect x=\"60\" y=\"78\" width=\"80\" height=\"80\" fill=\"#caa478\"/><path d=\"M60 72 H140\" stroke=\"#caa478\" stroke-width=\"14\" stroke-dasharray=\"12 8\"/><path d=\"M88 158 v-28 q12 -14 24 0 v28z\" fill=\"#8f6b46\"/><rect x=\"70\" y=\"92\" width=\"10\" height=\"14\" rx=\"5\" fill=\"#8f6b46\"/><rect x=\"120\" y=\"92\" width=\"10\" height=\"14\" rx=\"5\" fill=\"#8f6b46\"/><rect x=\"98\" y=\"20\" width=\"4\" height=\"46\" fill=\"#7a5232\"/><path class=\"a-flag\" d=\"M102 22 h44 l-8 13 l8 13 h-44z\" fill=\"#f08a24\"/><text x=\"100\" y=\"186\" text-anchor=\"middle\" font-family=\"Inter, sans-serif\" font-size=\"14\" font-weight=\"800\" fill=\"#5c7a3c\">KITTUR · 1824</text>"};

  const SCENES = [
    {
      era: ['Kadambas', 'ಕದಂಬರು'],
      title: ['Mayurasharma founds the Kadamba kingdom', 'ಮಯೂರಶರ್ಮನಿಂದ ಕದಂಬ ರಾಜ್ಯ'],
      sub: ['Banavasi, c. 345 CE. A century later, Halmidi gives Kannada its first inscription', 'ಬನವಾಸಿ, ಸು. ಕ್ರಿ.ಶ. 345. ಸು. 450ರಲ್ಲಿ ಹಲ್ಮಿಡಿಯಲ್ಲಿ ಮೊದಲ ಕನ್ನಡ ಶಾಸನ'],
      bubbles: [['Scholar today, king tomorrow!', 'ಇಂದು ವಿದ್ಯಾರ್ಥಿ, ನಾಳೆ ರಾಜ!', 'left:-2%;top:16%']],
      big: () => `${rect(0, 0, 400, 400, '#e4f1df')}${sun(306, 92, 30)}${cloud(150, 80, 0.9)}
        <path d="M0 250 q80 -60 170 -26 q100 -40 230 6 V320 H0z" fill="#bcd9a5"/>${dravida(330, 300, 0.55, '#d9b08a', '#c49470')}
        ${ground(300, '#9fca6e', '#8dbb5c')}
        ${tree(80, 330, 1.15, '#5f9e4f', [[-20, -118], [10, -126], [26, -98], [-40, -88], [0, -92], [36, -76], [-18, -70]])}
        ${banner(300, 120, 200, '#f2b632', 'lion')}
        ${anim('a-tumble', `<g transform="translate(118 300)"><rect x="-22" y="-6" width="44" height="12" rx="3" fill="#e8d7a3" stroke="#bfa86e"/><path d="M-16 0 h32" stroke="#9c8650"/></g>`)}
        ${figure({ x: 210, y: 392, s: 1.05, attire: 'king', lower: P.white, sash: P.red, wear: 'crown', skin: P.skin.brown, stache: 'handlebar', brows: 'fierce', mouth: 'grin', armR: 'up', holdR: 'sword', animR: 'a-swing', armL: 'out', move: 'a-bob' })}`,
      small: () => stoneSlab([64, 56, 64, 48, 60], 'HALMIDI · c. 450'),
    },
    {
      era: ['Badami Chalukyas', 'ಬಾದಾಮಿ ಚಾಲುಕ್ಯರು'],
      title: ['Pulakeshi II holds the Narmada', 'ನರ್ಮದೆಯ ದಡದಲ್ಲಿ ಇಮ್ಮಡಿ ಪುಲಕೇಶಿ'],
      sub: ['The Badami Chalukyas turn back Harshavardhana, c. 618 CE', 'ಬಾದಾಮಿ ಚಾಲುಕ್ಯರು ಹರ್ಷವರ್ಧನನನ್ನು ಹಿಮ್ಮೆಟ್ಟಿಸಿದರು, ಸು. ಕ್ರಿ.ಶ. 618'],
      bubbles: [['Not past the Narmada!', 'ನರ್ಮದೆ ದಾಟಿ ಬರಬೇಡ!', 'left:-4%;top:13%'], ['Back to Kannauj!', 'ಕನೌಜ್‌ಗೆ ವಾಪಸ್!', 'right:-2%;top:33%', 1]],
      big: () => LEGACY.pulakeshiBig,
      small: () => LEGACY.pulakeshiSmall,
    },
    {
      era: ['Badami Chalukyas', 'ಬಾದಾಮಿ ಚಾಲುಕ್ಯರು'],
      title: ['Queen Lokamahadevi builds at Pattadakal', 'ಪಟ್ಟದಕಲ್ಲಿನಲ್ಲಿ ರಾಣಿ ಲೋಕಮಹಾದೇವಿ'],
      sub: ['The Virupaksha temple celebrates a victory over the Pallavas, c. 740 CE', 'ಪಲ್ಲವರ ಮೇಲಿನ ಗೆಲುವಿನ ನೆನಪಿಗೆ ವಿರೂಪಾಕ್ಷ ದೇವಾಲಯ, ಸು. ಕ್ರಿ.ಶ. 740'],
      bubbles: [['Grander than Kanchi!', 'ಕಂಚಿಗಿಂತ ಭವ್ಯವಾಗಿರಲಿ!', 'left:-2%;top:24%'], ['Yes, my queen!', 'ಆಗಲಿ, ಮಹಾರಾಣಿ!', 'right:-3%;top:50%', 1]],
      big: () => `${rect(0, 0, 400, 400, '#fde8cc')}${sun(80, 86, 26, '#ffbf4d')}${birds(250, 70)}
        <path d="M0 270 q120 -40 240 -14 q90 -24 160 -2 V320 H0z" fill="#e9c79a"/>
        ${dravida(268, 312, 1.25)}
        <g stroke="#8a6a42" stroke-width="3" opacity=".8"><path d="M176 312 V120 M360 312 V120 M176 200 H360 M176 150 H360"/></g>
        ${ground(306, '#e2c08e', '#d6b07a')}
        ${figure({ x: 330, y: 396, s: 0.72, attire: 'commoner', skin: P.skin.deep, wear: 'turban', wearColor: '#f4efe2', stache: 'thin', armR: 'fwd', holdR: 'hammer', animR: 'a-tap', armL: 'fwd', flip: true })}
        ${figure({ x: 118, y: 396, s: 1, attire: 'saree', cloth: P.green, blouse: P.maroon, border: P.gold, hair: 'bun', wear: 'tiara', mark: 'bindi', nosering: true, armR: 'point', animR: 'a-point', armL: 'hip', move: 'a-bob' })}`,
      small: () => `${rect(0, 0, 200, 200, '#f6e3c8')}<path d="M0 30 h200 v80 h-200z" fill="#c0603e"/><path d="M0 52 h200 M0 74 h200 M0 94 h200" stroke="#a84f33" stroke-width="3"/>
        <path d="M54 110 v-40 h92 v40z" fill="#5e3426"/>${[64, 88, 112, 136].map((x) => rect(x - 4, 70, 8, 40, '#c0603e')).join('')}${rect(46, 62, 108, 10, '#a84f33')}
        ${rect(0, 110, 200, 90, '#6fb0c8')}<ellipse class="a-ripple" cx="100" cy="150" rx="60" ry="12" fill="none" stroke="#fff" stroke-width="2"/><ellipse class="a-ripple r2" cx="100" cy="150" rx="60" ry="12" fill="none" stroke="#fff" stroke-width="2"/>
        <text x="100" y="186" text-anchor="middle" font-family="Inter, sans-serif" font-size="13" font-weight="800" fill="#fff">BADAMI</text>`,
    },
    {
      era: ['Rashtrakutas', 'ರಾಷ್ಟ್ರಕೂಟರು'],
      title: ['Kavirajamarga, at Amoghavarsha\'s court', 'ಅಮೋಘವರ್ಷನ ಆಸ್ಥಾನದಲ್ಲಿ ಕವಿರಾಜಮಾರ್ಗ'],
      sub: ['The oldest surviving Kannada book maps the Kannada land, c. 850 CE', 'ಕನ್ನಡ ನಾಡನ್ನು ವರ್ಣಿಸಿದ ಮೊದಲ ಲಭ್ಯ ಕನ್ನಡ ಗ್ರಂಥ, ಸು. ಕ್ರಿ.ಶ. 850'],
      bubbles: [['From the Kaveri to the Godavari!', 'ಕಾವೇರಿಯಿಂದಮಾ ಗೋದಾವರಿವರಂ!', 'right:-6%;top:30%', 1]],
      big: () => `${rect(0, 0, 400, 400, '#f3e2c4')}
        ${anim('a-sway slow', `<path d="M0 0 h120 q-20 60 -60 90 q-40 -20 -60 -40z" fill="#b8382f"/>`, '0% 0%')}${anim('a-sway slow', `<path d="M400 0 h-120 q20 60 60 90 q40 -20 60 -40z" fill="#b8382f"/>`, '100% 0%')}
        <g transform="translate(140 46)"><rect width="120" height="92" rx="6" fill="#f4e6c4" stroke="#c9a96a" stroke-width="3"/>
          <path d="M10 22 q30 -12 50 0 t50 -4" stroke="#4f8fc0" stroke-width="4" fill="none"/><path d="M10 74 q30 10 50 0 t50 4" stroke="#4f8fc0" stroke-width="4" fill="none"/>
          <path class="a-glow" d="M12 28 q30 -12 48 0 t48 -4 v36 q-30 12 -48 0 t-48 4z" fill="#f2b632"/></g>
        ${rect(0, 300, 400, 100, '#d8b98a')}${rect(0, 300, 400, 8, '#c9a676')}
        <path d="M68 330 v-140 q62 -50 124 0 v140z" fill="${P.gold}" stroke="${P.goldD}" stroke-width="3"/><path d="M82 330 v-126 q48 -38 96 0 v126z" fill="#b8382f"/>
        ${figure({ x: 130, y: 342, s: 0.86, seated: true, attire: 'king', wear: 'kirita', mark: 'vibhuti', stache: 'handlebar', armL: 'down', armR: 'raise', animR: 'a-wave slow2', legs: P.white })}
        ${figure({ x: 300, y: 398, s: 0.9, attire: 'robe', cloth: '#f7f1e3', sash: P.saffron, wear: 'turban', stache: 'thin', mouth: 'talk', armR: 'fwd', holdR: 'leaf', armL: 'fwd', flip: true, nod: true })}`,
      small: () => `${rect(0, 0, 200, 200, '#fbe3cf')}<circle cx="100" cy="100" r="62" fill="#f6c99f"/>
        <g class="a-wing" style="transform-origin:100% 50%"><path d="M88 96 q-50 -40 -66 -10 q20 -2 26 8 q-20 0 -22 18 q22 -10 34 0 q-14 6 -12 20 q20 -14 40 -12z" fill="#d9542f"/></g>
        <g class="a-wing r" style="transform-origin:0% 50%"><path d="M112 96 q50 -40 66 -10 q-20 -2 -26 8 q20 0 22 18 q-22 -10 -34 0 q14 6 12 20 q-20 -14 -40 -12z" fill="#d9542f"/></g>
        <path d="M86 92 q14 -8 28 0 l-4 50 h-20z" fill="${P.gold}"/><circle cx="100" cy="76" r="15" fill="#2f8f7a"/><path d="M100 82 l-6 14 l12 0z" fill="${P.gold}"/>
        <circle cx="94" cy="74" r="2.4" fill="#fff"/><circle cx="106" cy="74" r="2.4" fill="#fff"/><path d="M90 60 l4 -10 l6 6 l6 -6 l4 10z" fill="${P.gold}"/>
        <text x="100" y="186" text-anchor="middle" font-family="Inter, sans-serif" font-size="13" font-weight="800" fill="#a8452a">GARUDA</text>`,
    },
    {
      era: ['Western Gangas', 'ಪಶ್ಚಿಮ ಗಂಗರು'],
      title: ['Gommateshwara rises at Shravanabelagola', 'ಶ್ರವಣಬೆಳಗೊಳದಲ್ಲಿ ಗೊಮ್ಮಟೇಶ್ವರ'],
      sub: ['Ganga minister Chavundaraya carves the 57-ft monolith, c. 981 CE', 'ಗಂಗರ ಮಂತ್ರಿ ಚಾವುಂಡರಾಯನ 57 ಅಡಿ ಏಕಶಿಲಾ ಮೂರ್ತಿ, ಸು. ಕ್ರಿ.ಶ. 981'],
      bubbles: [['For my mother\'s wish!', 'ಅಮ್ಮನ ಆಸೆಯಂತೆ!', 'left:-4%;top:56%']],
      big: () => `${rect(0, 0, 400, 400, '#e6eef8')}${cloud(40, 60, 0.8)}${cloud(330, 170, 0.6, 1)}
        <path d="M110 400 v-130 q90 -44 180 0 v130z" fill="#c9c3b5"/>
        <path d="M120 290 q-6 50 4 110 M280 290 q6 50 -4 110" stroke="#b5ae9f" stroke-width="22" stroke-linecap="round" fill="none"/>
        <g fill="none" stroke="#5f9e4f" stroke-width="3"><path d="M118 300 q14 20 0 40 q-14 20 2 40"/><path d="M282 300 q-14 20 0 40 q14 20 -2 40"/></g>
        <g fill="#6fae5b">${[[124, 318], [112, 352], [126, 382], [276, 318], [288, 352], [274, 382]].map(([x, y]) => `<ellipse cx="${x}" cy="${y}" rx="7" ry="4"/>`).join('')}</g>
        ${rect(186, 220, 28, 34, '#c9c3b5')}
        <ellipse cx="148" cy="190" rx="9" ry="26" fill="#c2bbac"/><ellipse cx="252" cy="190" rx="9" ry="26" fill="#c2bbac"/>
        <circle cx="200" cy="168" r="54" fill="#d3cdbf"/>
        <g fill="#a39c8d">${[[170, 128], [186, 120], [202, 118], [218, 121], [232, 128], [160, 140], [176, 133], [192, 129], [208, 129], [224, 133], [240, 141]].map(([x, y]) => `<circle cx="${x}" cy="${y}" r="7"/>`).join('')}</g>
        <path d="M178 172 q8 5 16 0 M206 172 q8 5 16 0" stroke="#7d766a" stroke-width="3" fill="none" stroke-linecap="round"/><path d="M198 180 q4 8 0 14" stroke="#a39c8d" stroke-width="2.5" fill="none"/><path d="M190 202 q10 6 20 0" stroke="#7d766a" stroke-width="3" fill="none" stroke-linecap="round"/>
        <g stroke="#9c7a4a" stroke-width="4"><path d="M300 400 V106 M352 400 V106 M300 200 H352 M300 300 H352"/></g>${rect(244, 100, 116, 7, '#8a6a3e', 2)}
        ${figure({ x: 290, y: 101, s: 0.42, attire: 'commoner', thread: true, skin: P.skin.brown, armR: 'raise', armL: 'hip', mouth: 'talk', flip: true })}
        <g fill="none" stroke-linecap="round"><path d="M245 44 q-12 22 -23 74" stroke="#9fb3c9" stroke-width="12" opacity=".45"/><path d="M245 44 q-12 22 -23 74" stroke="#fff" stroke-width="8"/><path class="a-pour" d="M245 44 q-12 22 -23 74" stroke="#cfdbe8" stroke-width="2.5" pathLength="1"/></g>
        <g transform="translate(262 38) rotate(-110)"><path d="M-13 -4 q0 16 13 16 q13 0 13 -16 q0 -8 -6 -10 h-14 q-6 2 -6 10z" fill="#c8892e" stroke="#9a6418" stroke-width="1.5"/>${rect(-5, -17, 10, 5, '#c8892e')}${rect(-8, -20, 16, 4, '#9a6418', 2)}</g>
        <g fill="none" stroke-linecap="round">${['M224 118 q26 6 28 34 q2 30 -8 62', 'M218 118 q-44 -4 -60 30 q-8 30 -2 66', 'M221 121 q-5 14 -2 28'].map((d) => `<path d="${d}" stroke="#a8a091" stroke-width="10" opacity=".35"/><path d="${d}" stroke="#fff" stroke-width="7"/><path class="a-pour" d="${d}" stroke="#dcd6ca" stroke-width="2" pathLength="1"/>`).join('')}</g>
        <path d="M186 124 q34 -18 66 2 q-8 10 -30 6 q-22 -2 -36 -8z" fill="#fff" opacity=".92"/><ellipse class="a-pulse" cx="222" cy="118" rx="13" ry="5" fill="#fff"/>
        ${figure({ x: 70, y: 404, s: 0.78, attire: 'robe', cloth: '#f7f1e3', sash: P.maroon, wear: 'turban', wearColor: '#f4efe2', stache: 'thin', armR: 'chest', armL: 'chest', nod: true })}`,
      small: () => `${rect(0, 0, 200, 200, '#e9f0e3')}<path d="M0 150 q100 -20 200 0 v50 h-200z" fill="#a9cc77"/>${elephant({ x: 92, y: 168, s: 0.62, walk: true, cloth: P.red })}
        <text x="100" y="40" text-anchor="middle" font-family="Inter, sans-serif" font-size="13" font-weight="800" fill="#5c7a3c">TALAKAD</text>`,
    },
    {
      era: ['Hoysalas', 'ಹೊಯ್ಸಳರು'],
      title: ['"Hoy, Sala!" The Hoysala legend', '"ಹೊಯ್ ಸಳ!" ಹೊಯ್ಸಳರ ದಂತಕಥೆ'],
      sub: ['His teacher cries "Strike, Sala!" and a dynasty gets its name, c. 11th century', 'ಗುರುವಿನ "ಹೊಯ್ ಸಳ!" ಎಂಬ ಕೂಗಿನಿಂದ ಹೊಯ್ಸಳ ಹೆಸರು, ಸು. 11ನೇ ಶತಮಾನ'],
      bubbles: [['Hoy, Sala!', 'ಹೊಯ್ ಸಳ!', 'left:-3%;top:27%']],
      big: () => `${rect(0, 0, 400, 400, '#e3efd9')}${tree(24, 300, 1.2, '#4f8c44')}${tree(386, 290, 1.1, '#4f8c44')}
        ${ground(290, '#9cc46a', '#88b558')}
        ${figure({ x: 42, y: 290, s: 0.5, attire: 'robe', cloth: P.white, sash: P.white, hair: 'bald', studs: false, brows: 'up', mouth: 'open', armR: 'point', armL: 'raise', holdL: 'pichhi' })}
        ${tiger(292, 384, 1.05)}
        ${figure({ x: 118, y: 396, s: 1, attire: 'king', lower: '#f7f1e3', sash: P.saffron, hair: 'short', stache: 'thin', brows: 'fierce', mouth: 'open', armR: 'up', holdR: 'sword', animR: 'a-strike', armL: 'out', skin: P.skin.brown })}`,
      small: () => `${rect(0, 0, 200, 200, '#dcd7c6')}<rect x="30" y="30" width="140" height="132" rx="10" fill="#a9a48f"/><rect x="38" y="38" width="124" height="116" rx="7" fill="#bdb8a3"/>
        <g fill="#8a8572"><ellipse cx="124" cy="112" rx="28" ry="14" transform="rotate(-30 124 112)"/><circle cx="106" cy="86" r="13"/><path d="M144 118 q16 -10 12 -30" stroke="#8a8572" stroke-width="6" fill="none"/>
        <circle cx="70" cy="70" r="11"/><path d="M60 84 h20 l4 46 h-28z"/><path d="M78 88 l20 -22 l4 -24" stroke="#8a8572" stroke-width="7" fill="none" stroke-linecap="round"/><path d="M102 42 l-4 -16" stroke="#77725f" stroke-width="4"/></g>
        <text x="100" y="184" text-anchor="middle" font-family="Inter, sans-serif" font-size="13" font-weight="800" fill="#6f6a57">HOYSALA</text>`,
    },
    {
      era: ['Kalyani Chalukyas', 'ಕಲ್ಯಾಣಿ ಚಾಲುಕ್ಯರು'],
      title: ['Vikramaditya VI starts a new era', 'ಆರನೇ ವಿಕ್ರಮಾದಿತ್ಯನ ಹೊಸ ಶಕೆ'],
      sub: ['The Chalukya-Vikrama era is counted from 1076 CE', 'ಚಾಲುಕ್ಯ-ವಿಕ್ರಮ ಶಕೆ ಕ್ರಿ.ಶ. 1076ರಿಂದ ಆರಂಭ'],
      bubbles: [['A new era begins!', 'ಹೊಸ ಶಕೆ ಆರಂಭ!', 'left:-2%;top:16%'], ['Year one, everybody!', 'ಇದು ಒಂದನೇ ವರ್ಷ!', 'right:-4%;top:46%', 1]],
      big: () => `${rect(0, 0, 400, 400, '#fbe9d0')}${sun(320, 80, 26)}${birds(80, 60)}
        ${dravida(200, 300, 1.05, '#a9a48f', '#8f8a76')}
        ${ground(296, '#d9c094', '#ccb07f')}
        ${figure({ x: 326, y: 398, s: 0.78, attire: 'commoner', skin: P.skin.deep, wear: 'turban', wearColor: P.red, stache: 'thin', mouth: 'talk', armR: 'fwd', holdR: 'drumstick', animR: 'a-tap', armL: 'fwd', flip: true })}
        <g transform="translate(286 330)"><ellipse cx="0" cy="0" rx="14" ry="24" fill="#b5462e"/><ellipse cx="0" cy="-22" rx="14" ry="5" fill="#f1e2c0"/></g>
        ${figure({ x: 132, y: 396, s: 1.05, attire: 'king', wear: 'kirita', mark: 'vibhuti', stache: 'handlebar', sash: P.maroon, armR: 'up', holdR: 'leaf', animR: 'a-wave slow2', armL: 'hip', move: 'a-bob' })}`,
      small: () => `${rect(0, 0, 200, 200, '#efe2cb')}${[0, 1, 2, 3].map((i) => `<path d="M${20 + i * 16} ${40 + i * 22} h${160 - i * 32} v22 h-${160 - i * 32}z" fill="${['#b9a07a', '#c7ae86', '#b9a07a', '#c7ae86'][i]}"/>`).join('')}
        ${rect(84, 128, 32, 40, '#6fb0c8')}<ellipse class="a-ripple" cx="100" cy="150" rx="14" ry="5" fill="none" stroke="#fff" stroke-width="2"/>
        <path d="M86 36 v-12 h28 v12z M90 24 l10 -10 l10 10z" fill="#8f7a58"/>
        <text x="100" y="188" text-anchor="middle" font-family="Inter, sans-serif" font-size="13" font-weight="800" fill="#8a7a62">LAKKUNDI</text>`,
    },
    {
      era: ['Hoysalas', 'ಹೊಯ್ಸಳರು'],
      title: ['Shantala dances at Belur', 'ಬೇಲೂರಿನಲ್ಲಿ ಶಾಂತಲೆಯ ನಾಟ್ಯ'],
      sub: ['King Vishnuvardhana\'s Chennakeshava temple, 1117 CE', 'ವಿಷ್ಣುವರ್ಧನನ ಚೆನ್ನಕೇಶವ ದೇವಾಲಯ, ಕ್ರಿ.ಶ. 1117'],
      bubbles: [['Hold that pose!', 'ಹಾಗೇ ನಿಲ್ಲಿ!', 'left:-2%;top:40%'], ['Only for a moment!', 'ಒಂದೇ ಕ್ಷಣ!', 'right:-2%;top:22%', 1]],
      big: () => `${rect(0, 0, 400, 400, '#f1ead9')}
        <path d="M20 150 h360 l-14 -22 h-332z" fill="#8f8b78"/>${rect(30, 150, 340, 140, '#a7a491')}
        ${[0, 1, 2, 3].map((r) => `<path d="M30 ${170 + r * 28} H370" stroke="#8f8b78" stroke-width="3"/>`).join('')}
        <g fill="#8f8b78">${Array.from({ length: 17 }, (_, i) => `<circle cx="${40 + i * 20}" cy="${276}" r="6"/>`).join('')}</g>
        <path d="M30 220 q10 -8 20 0 t20 0 t20 0 t20 0 t20 0 t20 0 t20 0 t20 0 t20 0 t20 0 t20 0 t20 0 t20 0 t20 0 t20 0 t20 0 t20 0" stroke="#8f8b78" stroke-width="3" fill="none"/>
        <path d="M176 290 v-96 h48 v96z" fill="#5f5b4c"/>${rect(166, 190, 10, 100, '#8f8b78')}${rect(224, 190, 10, 100, '#8f8b78')}
        <path d="M0 290 l20 -10 h360 l20 10 v10 H0z" fill="#8f8b78"/>${ground(300, '#d9cfb5', '#cfc3a5')}
        <g fill="#8f8b78" transform="translate(100 300)"><circle cx="0" cy="-86" r="9"/><path d="M-8 -76 h16 l6 40 l-6 36 h-16 l-6 -36z"/><path d="M8 -72 l14 -24" stroke="#8f8b78" stroke-width="5" stroke-linecap="round"/></g>
        ${figure({ x: 60, y: 398, s: 0.72, attire: 'commoner', skin: P.skin.brown, hair: 'short', stache: 'thin', armR: 'fwd', holdR: 'hammer', animR: 'a-tap', armL: 'fwd' })}
        ${figure({ x: 268, y: 398, s: 0.98, attire: 'saree', cloth: P.red, blouse: P.green, border: P.gold, hair: 'bun', wear: 'tiara', mark: 'bindi', nosering: true, eyes: 'closed', armR: 'up', animR: 'a-wave', armL: 'side', animL: 'a-wave slow2', move: 'a-dance' })}`,
      small: () => `${rect(0, 0, 200, 200, '#e6dfcc')}<path d="M40 30 h120 l-12 16 h-96z" fill="#8f8b78"/>
        <g fill="#8f8b78"><circle cx="100" cy="68" r="14"/><circle cx="88" cy="58" r="8"/><path d="M88 82 h24 l8 50 l-10 30 h-20 l-10 -30z"/><path d="M110 90 q22 -6 28 -30" stroke="#8f8b78" stroke-width="8" fill="none" stroke-linecap="round"/></g>
        <circle cx="140" cy="54" r="12" fill="#cfd8dc" stroke="#8f8b78" stroke-width="4"/><path class="a-twinkle" d="M146 44 l2 5 l5 2 l-5 2 l-2 5 l-2 -5 l-5 -2 l5 -2z" fill="#fff"/>
        <text x="100" y="186" text-anchor="middle" font-family="Inter, sans-serif" font-size="13" font-weight="800" fill="#6f6a57">BELUR</text>`,
    },
    {
      era: ['Kalachuris of Kalyana', 'ಕಲ್ಯಾಣದ ಕಲಚುರಿಗಳು'],
      title: ['Basavanna\'s Anubhava Mantapa', 'ಬಸವಣ್ಣನವರ ಅನುಭವ ಮಂಟಪ'],
      sub: ['A 12th-century hall where everyone had a say, like your vote today', 'ಎಲ್ಲರಿಗೂ ಮಾತಿನ ಹಕ್ಕಿದ್ದ 12ನೇ ಶತಮಾನದ ಸಭೆ, ಇಂದಿನ ನಿಮ್ಮ ಮತದಂತೆ'],
      bubbles: [['Work is worship!', 'ಕಾಯಕವೇ ಕೈಲಾಸ!', 'left:30%;top:22%'], ['I have a say too!', 'ನನ್ನದೂ ಒಂದು ಮಾತು!', 'right:-3%;top:44%', 1]],
      big: () => `${rect(0, 0, 400, 400, '#f8ead5')}<path d="M193 76 q7 -28 14 0z" fill="${P.gold}"/><path d="M74 112 h252 l-26 -38 h-200z" fill="#b07a4c"/><path d="M30 150 h340 l-34 -40 h-272z" fill="#8f603b"/>${rect(30, 148, 340, 10, '#7a5232')}
        <g fill="#d6b88b">${[58, 128, 252, 322].map((x) => rect(x, 158, 20, 150, '#d6b88b')).join('')}</g>
        <g>${[52, 122, 246, 316].map((x) => rect(x, 158, 32, 10, '#c39e6c', 2) + rect(x, 296, 32, 12, '#c39e6c', 2)).join('')}</g>
        ${rect(0, 306, 400, 94, '#d9b98c')}${rect(0, 306, 400, 8, '#c9a676')}
        <g class="a-hang"><path d="M200 158 L190 190 M200 158 L210 190" stroke="#7a5232" stroke-width="1.6"/><path d="M184 190 h32 l-6 10 h-20z" fill="${P.gold}"/><path class="a-flicker" d="M200 174 q-6 8 0 15 q6 -7 0 -15z" fill="#ff8a3d"/></g>
        ${figure({ x: 98, y: 344, s: 0.66, seated: true, attire: 'saree', cloth: P.saffron, blouse: '#d0701c', border: '#b3541a', hair: 'long', mark: 'vibhuti', mala: true, armR: 'chest', armL: 'chest', nod: true, skin: P.skin.brown })}
        ${figure({ x: 200, y: 346, s: 0.8, seated: true, attire: 'robe', cloth: '#fbf7ee', shawl: P.saffron, sash: P.saffron, hair: 'jata', mark: 'vibhuti', mala: true, armL: 'chest', holdL: 'linga', armR: 'raise', animR: 'a-wave slow2', nod: true })}
        ${figure({ x: 302, y: 344, s: 0.66, seated: true, attire: 'commoner', skin: P.skin.deep, wear: 'turban', stache: 'thin', mouth: 'talk', armR: 'up', animR: 'a-wave', armL: 'chest' })}`,
      small: () => LEGACY.basavaSmall,
    },
    {
      era: ['Vijayanagara · Sangama', 'ವಿಜಯನಗರ · ಸಂಗಮ'],
      title: ['Harihara and Bukka found Vijayanagara', 'ಹರಿಹರ-ಬುಕ್ಕರಿಂದ ವಿಜಯನಗರ ಸ್ಥಾಪನೆ'],
      sub: ['Where a hare turned on the hounds, by the Tungabhadra, 1336', 'ಮೊಲವೇ ನಾಯಿಗಳನ್ನು ಅಟ್ಟಿಸಿದ ತುಂಗಭದ್ರೆಯ ತೀರ, 1336'],
      bubbles: [['A hare chasing hounds?!', 'ಮೊಲವೇ ನಾಯಿಗಳನ್ನು ಅಟ್ಟುತ್ತಿದೆ!', 'left:-6%;top:22%'], ['Brave land. Build here!', 'ವೀರಭೂಮಿ, ಇಲ್ಲೇ ಕಟ್ಟಿ!', 'right:-4%;top:30%', 1]],
      big: () => `${rect(0, 0, 400, 400, '#fde6c8')}${sun(200, 90, 28, '#ffb547')}
        <path d="M0 250 q30 -70 80 -60 q20 -40 60 -20 q30 -30 70 0 q40 -20 70 10 q40 -30 120 20 V300 H0z" fill="#d7a06d"/>${boulder(56, 236, 44, 28, '#c58a57')}${boulder(352, 230, 40, 30, '#c58a57')}${boulder(370, 196, 22, 18, '#d29864')}
        ${water(282, 22)}${ground(300, '#e9c58f', '#dfb57b')}
        ${figure({ x: 70, y: 318, s: 0.58, attire: 'king', wear: 'turban', wearColor: P.red, stache: 'handlebar', armR: 'point', animR: 'a-point', armL: 'hip' })}
        ${figure({ x: 128, y: 322, s: 0.6, attire: 'king', wear: 'turban', wearColor: '#f4efe2', stache: 'handlebar', mouth: 'o', armR: 'hip', armL: 'hip', skin: P.skin.brown })}
        ${figure({ x: 336, y: 318, s: 0.6, attire: 'monk', cloth: P.saffron, hair: 'sage', hairColor: '#ece7dd', beard: true, stache: 'thin', mark: 'vibhuti', armR: 'down', holdR: 'staff', armL: 'raise', animL: 'a-wave slow2', skin: P.skin.brown })}
        ${hound(150, 384, 0.9, 0)}${hound(214, 392, 0.9, -0.2)}${hare(290, 388, 1.1)}`,
      small: () => `${rect(0, 0, 200, 200, '#fdeccf')}<circle cx="44" cy="54" r="16" fill="#ffb547"/><path d="M160 40 a16 16 0 1 0 6 28 a12 12 0 1 1 -6 -28z" fill="#e6dcc4"/>
        <g transform="translate(100 112) scale(2.4)" fill="#8a3a2b">${EMBLEM.boar}</g>
        <path d="M40 150 h112 l8 4 l-8 4 h-112z" fill="#cfd6de" stroke="${P.steel}"/>${rect(30, 148, 12, 12, P.gold, 2)}
        <text x="100" y="188" text-anchor="middle" font-family="Inter, sans-serif" font-size="13" font-weight="800" fill="#8a3a2b">VARAHA</text>`,
    },
    {
      era: ['Vijayanagara · Tuluva', 'ವಿಜಯನಗರ · ತುಳುವ'],
      title: ['Krishnadevaraya\'s Vijayanagara', 'ಶ್ರೀಕೃಷ್ಣದೇವರಾಯನ ವಿಜಯನಗರ'],
      sub: ['Hampi at its height, early 1500s', 'ವೈಭವದ ಉತ್ತುಂಗದಲ್ಲಿ ಹಂಪಿ, 16ನೇ ಶತಮಾನ'],
      bubbles: [['Welcome to Vijayanagara!', 'ವಿಜಯನಗರಕ್ಕೆ ಸ್ವಾಗತ!', 'left:-6%;top:28%'], ['Diamonds sold by the heap!', 'ವಜ್ರಗಳು ರಾಶಿ ರಾಶಿ!', 'right:-2%;top:14%', 1]],
      big: () => LEGACY.hampiBig,
      small: () => LEGACY.hampiSmall,
    },
    {
      era: ['Haridasas', 'ಹರಿದಾಸರು'],
      title: ['Kanakadasa sings at Udupi', 'ಉಡುಪಿಯಲ್ಲಿ ಕನಕದಾಸರು'],
      sub: ['Krishna turns to the little window, the Kanakana Kindi, 16th century', 'ಕೃಷ್ಣ ತಿರುಗಿ ದರ್ಶನವಿತ್ತ ಕನಕನ ಕಿಂಡಿ, 16ನೇ ಶತಮಾನ'],
      bubbles: [['Open the door, Hari!', 'ಬಾಗಿಲನು ತೆರೆದು…', 'left:-4%;top:30%'], ['He turned around!', 'ಕೃಷ್ಣ ತಿರುಗಿದ!', 'right:-4%;top:14%', 1]],
      big: () => `${rect(0, 0, 400, 400, '#fdebd6')}${palm(30, 300, 1.1, 10)}
        <path d="M110 150 l60 -70 h220 l20 70z" fill="#b0503a"/><path d="M118 150 l56 -62" stroke="#94412f" stroke-width="3"/>${[0, 1, 2, 3, 4].map((i) => `<path d="M${130 + i * 56} 150 l${40 - i * 2} -68" stroke="#94412f" stroke-width="2.5"/>`).join('')}
        ${rect(120, 150, 290, 160, '#f3ead6')}${rect(120, 300, 290, 12, '#d8cbb0')}
        <rect x="236" y="186" width="96" height="78" rx="4" fill="#5a3a26"/>
        <circle class="a-pulse" cx="284" cy="226" r="34" fill="#ffd36b" opacity=".85"/>
        <g class="a-turn"><path d="M272 256 v-30 q12 -10 24 0 v30z" fill="#2d2a3a"/><circle cx="284" cy="218" r="10" fill="#2d2a3a"/><path d="M276 210 l3 -10 l5 6 l5 -6 l3 10z" fill="${P.gold}"/><path d="M296 234 l10 -16" stroke="#2d2a3a" stroke-width="3"/></g>
        <g stroke="#7a5232" stroke-width="5">${[268, 300].map((x) => `<path d="M${x} 186 V264"/>`).join('')}${[212, 238].map((y) => `<path d="M236 ${y} H332"/>`).join('')}</g>
        ${ground(310, '#d9c39a', '#ccb385')}${notes(170, 210)}
        ${figure({ x: 120, y: 398, s: 1, attire: 'commoner', skin: P.skin.deep, wear: 'turban', wearColor: '#f4efe2', mark: 'namam', stache: 'thin', eyes: 'closed', mouth: 'talk', armL: 'down', holdL: 'tambura', armR: 'raise', animR: 'a-wave slow2', nod: true })}`,
      small: () => `${rect(0, 0, 200, 200, '#5a3a26')}<circle class="a-pulse" cx="100" cy="100" r="62" fill="#ffd36b"/>
        <g stroke="#7a5232" stroke-width="12">${[60, 100, 140].map((x) => `<path d="M${x} 20 V180"/>`).join('')}${[60, 100, 140].map((y) => `<path d="M20 ${y} H180"/>`).join('')}</g>`,
    },
    {
      era: ['Chowtas of Ullal', 'ಉಳ್ಳಾಲದ ಚೌಟರು'],
      title: ['Rani Abbakka of Ullal', 'ಉಳ್ಳಾಲದ ರಾಣಿ ಅಬ್ಬಕ್ಕ'],
      sub: ['The fearless queen keeps the Portuguese at bay for decades, 16th century', 'ದಶಕಗಳ ಕಾಲ ಪೋರ್ಚುಗೀಸರನ್ನು ತಡೆದ ಅಭಯ ರಾಣಿ, 16ನೇ ಶತಮಾನ'],
      bubbles: [['Not one inch of Ullal!', 'ಉಳ್ಳಾಲದ ಒಂದಿಂಚೂ ಕೊಡೆನು!', 'left:-2%;top:16%'], ['Fire on board!', 'ಹಡಗಿಗೆ ಬೆಂಕಿ!', 'right:-4%;top:34%', 1]],
      big: () => `${rect(0, 0, 400, 400, '#ffd9b0')}${sun(300, 120, 34, '#ff9a4d')}${birds(120, 70)}
        ${water(214, 96, '#5aa6c8')}
        ${anim('a-rock', `<g transform="translate(300 262)"><path d="M-62 -4 h124 l-16 26 h-92z" fill="#7a4a2e"/><path d="M-62 -4 h124" stroke="#5d3720" stroke-width="4"/>
          ${rect(-2, -110, 4, 106, '#5d3720')}${rect(-40, -110, 3, 106, '#5d3720')}
          <path d="M2 -100 q30 30 0 70 h-0z" fill="#f7f1e3"/><path d="M-36 -92 q24 26 0 58z" fill="#f7f1e3"/><path d="M10 -70 h12 M16 -76 v12" stroke="${P.red}" stroke-width="4"/>
          <path class="a-flicker" d="M6 -84 q-10 14 0 26 q10 -8 0 -26z" fill="#ff7a2a"/><path class="a-flicker" style="animation-delay:-.2s" d="M14 -74 q-6 8 0 16 q6 -6 0 -16z" fill="#ffc53a"/></g>`, '50% 100%')}
        ${anim('a-arrow', `<path d="M150 236 h34" stroke="#7a4a2e" stroke-width="3"/><path d="M184 232 l8 4 l-8 4z" fill="#6b7280"/><path class="a-flicker" d="M190 236 q8 -8 4 -16 q-10 6 -4 16z" fill="#ff7a2a"/>`)}
        ${ground(306, '#f1d7a0', '#e8c98a')}${palm(26, 330, 1.2, 18)}${palm(76, 318, 0.9, 8)}
        ${figure({ x: 140, y: 398, s: 1, attire: 'saree', cloth: P.maroon, blouse: P.green, border: P.gold, hair: 'bun', wear: 'tiara', mark: 'bindi', nosering: true, brows: 'fierce', armR: 'fwd', holdR: 'bow', armL: 'chest', move: 'a-bob', skin: P.skin.brown })}`,
      small: () => `${rect(0, 0, 200, 200, '#ffd2a1')}<circle class="a-pulse" cx="100" cy="104" r="28" fill="#ff8f45"/>${rect(0, 104, 200, 96, '#4f97bb')}
        <g class="a-rock" style="transform-origin:50% 100%"><path d="M62 132 h76 l-12 16 h-52z" fill="#6f4529"/><path d="M98 132 V92" stroke="#6f4529" stroke-width="3"/><path d="M100 94 l26 30 h-26z" fill="#f7f1e3"/></g>
        ${palm(30, 200, 0.62, 10)}${palm(176, 200, 0.55, -10)}`,
    },
    {
      era: ['Wodeyars of Mysuru', 'ಮೈಸೂರು ಒಡೆಯರು'],
      title: ['The Dasara begins', 'ನಾಡಹಬ್ಬ ದಸರಾ'],
      sub: ['Raja Wodeyar starts the festival at Srirangapatna in 1610; Mysuru still celebrates it', '1610ರಲ್ಲಿ ರಾಜ ಒಡೆಯರ್ ಶ್ರೀರಂಗಪಟ್ಟಣದಲ್ಲಿ ಆರಂಭಿಸಿದ ಹಬ್ಬ, ಇಂದಿಗೂ ಮೈಸೂರಿನಲ್ಲಿ'],
      bubbles: [['Make way for the Ambari!', 'ಅಂಬಾರಿಗೆ ದಾರಿ ಬಿಡಿ!', 'left:-4%;top:20%']],
      big: () => `${rect(0, 0, 400, 400, '#1f2a5c')}${stars([[30, 40], [80, 90], [150, 30], [330, 40], [370, 100], [260, 60], [120, 140], [350, 160]])}
        <g fill="#e8d9c2"><path d="M90 300 v-120 h220 v120z"/><path d="M170 180 v-40 h60 v40z"/></g>
        <g fill="#c96a4a"><path d="M170 140 q30 -60 60 0z"/><path d="M90 180 q16 -34 32 0z M278 180 q16 -34 32 0z M130 180 q14 -28 28 0z M242 180 q14 -28 28 0z"/></g>
        <g fill="#7a5a48">${[110, 150, 190, 230, 270].map((x) => `<path d="M${x} 300 v-56 q10 -14 20 0 v56z"/>`).join('')}</g>
        <g fill="#ffd36b">${[[92, 182], [120, 182], [130, 182], [158, 182], [172, 142], [200, 112], [228, 142], [242, 182], [270, 182], [280, 182], [308, 182], [90, 220], [310, 220], [90, 260], [310, 260], [200, 180], [150, 200], [250, 200]].map(([x, y], i) => `<circle class="a-twinkle" style="animation-delay:-${(i * 0.23).toFixed(2)}s" cx="${x}" cy="${y}" r="3"/>`).join('')}</g>
        ${ground(300, '#6d5a4a', '#5d4b3d')}
        <g class="a-burst"><circle cx="60" cy="70" r="20" fill="none" stroke="#ff8a5c" stroke-width="3" stroke-dasharray="3 6"/></g><g class="a-burst" style="animation-delay:-1s"><circle cx="340" cy="90" r="24" fill="none" stroke="#7ad1ff" stroke-width="3" stroke-dasharray="3 6"/></g>
        ${elephant({ x: 196, y: 392, s: 1, walk: true, cloth: '#b8382f', ambari: true, color: '#8f8f9f', dark: '#7d7d8d' })}
        ${figure({ x: 258, y: 336, s: 0.36, seated: true, attire: 'commoner', skin: P.skin.deep, wear: 'turban', wearColor: '#f4efe2', stache: 'thin', mouth: 'talk', armR: 'raise', holdR: 'goad', armL: 'down' })}`,
      small: () => `${rect(0, 0, 200, 200, '#b8382f')}<circle cx="100" cy="100" r="70" fill="#a3302a"/>
        <g fill="${P.gold}"><path d="M84 94 h32 v26 q-16 18 -32 0z"/>
        <path class="a-wing" style="transform-origin:100% 30%" d="M84 98 q-34 -12 -44 22 q16 -6 26 2 q-10 4 -12 16 q14 -8 30 -8z"/>
        <path class="a-wing r" style="transform-origin:0% 30%" d="M116 98 q34 -12 44 22 q-16 -6 -26 2 q10 4 12 16 q-14 -8 -30 -8z"/>
        <path d="M92 96 q-4 -22 -18 -30" stroke="${P.gold}" stroke-width="8" fill="none" stroke-linecap="round"/><path d="M108 96 q4 -22 18 -30" stroke="${P.gold}" stroke-width="8" fill="none" stroke-linecap="round"/>
        <circle cx="70" cy="62" r="10"/><circle cx="130" cy="62" r="10"/><path d="M62 60 l-12 4 l12 5z M138 60 l12 4 l-12 5z"/>
        <path d="M90 136 l-8 18 M100 138 v18 M110 136 l8 18" stroke="${P.gold}" stroke-width="5" stroke-linecap="round"/></g>
        <circle cx="68" cy="60" r="2.4" fill="#a3302a"/><circle cx="132" cy="60" r="2.4" fill="#a3302a"/>
        <text x="100" y="190" text-anchor="middle" font-family="Inter, sans-serif" font-size="13" font-weight="800" fill="#fbe3b0">MYSURU</text>`,
    },
    {
      era: ['Keladi Nayakas', 'ಕೆಳದಿ ನಾಯಕರು'],
      title: ['Keladi Chennamma shelters Rajaram', 'ರಾಜಾರಾಮನಿಗೆ ಆಶ್ರಯ ನೀಡಿದ ಕೆಳದಿ ಚೆನ್ನಮ್ಮ'],
      sub: ['And stands up to Aurangzeb\'s army, 1689', 'ಔರಂಗಜೇಬನ ಸೈನ್ಯಕ್ಕೆ ಎದೆಯೊಡ್ಡಿದ ರಾಣಿ, 1689'],
      bubbles: [['You are safe in Keladi.', 'ಕೆಳದಿಯಲ್ಲಿ ನೀವು ಸುರಕ್ಷಿತ.', 'right:-4%;top:18%', 1], ['Thank you, Rani!', 'ಧನ್ಯವಾದ, ರಾಣಿ!', 'left:-2%;top:40%']],
      big: () => `${rect(0, 0, 400, 400, '#dcefe4')}${cloud(60, 60, 0.9)}${cloud(260, 40, 0.7, 1)}
        <path d="M0 240 q70 -60 150 -30 q80 -50 160 -10 q50 -20 90 0 V320 H0z" fill="#7fb36a"/>
        ${areca(30, 300, 0.9)}${areca(62, 296, 0.75)}
        <g class="a-puff"><circle cx="14" cy="236" r="12" fill="#e6dcc0"/></g><g class="a-puff p2"><circle cx="36" cy="230" r="9" fill="#e6dcc0"/></g>
        <path d="M220 320 v-150 h170 v150z" fill="#a5573b"/>${crenel(220, 390, 166, '#a5573b')}<path d="M262 320 v-80 q43 -50 86 0 v80z" fill="#5d2f20"/>
        ${ground(310, '#8fbf6e', '#7fb05e')}
        ${figure({ x: 112, y: 396, s: 0.86, attire: 'robe', cloth: '#f7f1e3', sash: P.saffron, wear: 'maratha', stache: 'thin', mark: 'tilak', brows: 'up', armR: 'chest', armL: 'chest', nod: true })}
        ${figure({ x: 286, y: 398, s: 1, attire: 'saree', cloth: '#7d3c98', blouse: P.red, border: P.gold, hair: 'bun', wear: 'tiara', mark: 'bindi', nosering: true, armR: 'raise', animR: 'a-wave slow2', armL: 'hip', flip: true, move: 'a-bob' })}`,
      small: () => `${rect(0, 0, 200, 200, '#cfe3d8')}<g fill="#fff">${cloud(40, 40, 0.8)}</g>${rect(0, 150, 200, 50, '#7fb05e')}
        ${areca(50, 170, 0.6)}${areca(100, 176, 0.7)}${areca(150, 168, 0.62)}
        <g class="a-rain" stroke="#4f8fc0" stroke-width="2" stroke-linecap="round">${Array.from({ length: 12 }, (_, i) => `<path d="M${10 + i * 16} ${20 + (i % 3) * 18} l-4 12"/>`).join('')}</g>`,
    },
    {
      era: ['Chitradurga Nayakas', 'ಚಿತ್ರದುರ್ಗದ ನಾಯಕರು'],
      title: ['Onake Obavva guards Chitradurga', 'ಚಿತ್ರದುರ್ಗದ ಒನಕೆ ಓಬವ್ವ'],
      sub: ['With just a pestle, she holds the secret gap in the fort wall, 18th century', 'ಒನಕೆಯೊಂದರಿಂದಲೇ ಕೋಟೆಯ ಕಿಂಡಿಯನ್ನು ಕಾದ ವೀರವನಿತೆ, 18ನೇ ಶತಮಾನ'],
      bubbles: [['Come through, if you dare!', 'ಧೈರ್ಯವಿದ್ದರೆ ಬನ್ನಿ!', 'left:-4%;top:12%'], ['Ouch!', 'ಅಯ್ಯೋ!', 'right:4%;top:58%', 1]],
      big: () => `${rect(0, 0, 400, 400, '#fbe7cf')}${sun(70, 70, 24)}
        ${boulder(320, 260, 110, 90, '#b88a63')}${boulder(380, 170, 60, 50, '#c69a70')}${boulder(240, 200, 60, 44, '#c69a70')}
        <path d="M200 160 h200 v40 h-200z" fill="#a8774f"/>${crenel(200, 400, 156, '#a8774f')}
        ${ground(310, '#d9b98a', '#cfab78')}
        <ellipse cx="306" cy="336" rx="34" ry="26" fill="#3d2a1e"/>
        <g class="a-peek">${at(306, 362, 0.55, `<g transform="translate(0 -160)">${head({ skin: P.skin.wheat, wear: 'turban', wearColor: '#e9e2cf', eyes: 'dizzy', stache: 'thin', mouth: 'o' })}</g>`)}</g>
        <g class="a-spark" style="transform-origin:306px 260px"><path d="M306 248 l3 7 l7 1 l-5 5 l2 7 l-7 -4 l-7 4 l2 -7 l-5 -5 l7 -1z" fill="#ffd34d"/></g>
        <path d="M190 384 q14 -22 28 0 q-4 12 -14 12 q-10 0 -14 -12z" fill="${P.gold}" stroke="${P.goldD}" stroke-width="2"/>
        ${figure({ x: 140, y: 396, s: 1.02, attire: 'saree', cloth: P.green, blouse: P.red, border: P.red, hair: 'bun', mark: 'bindi', nosering: true, brows: 'fierce', mouth: 'grin', armR: 'up', holdR: 'pestle', animR: 'a-bonk', armL: 'hip', skin: P.skin.brown })}`,
      small: () => `${rect(0, 0, 200, 200, '#fbe7cf')}${boulder(60, 150, 70, 50, '#b88a63')}${boulder(150, 140, 60, 56, '#c69a70')}${boulder(110, 110, 40, 30, '#b88a63')}
        <path d="M20 108 h160 v-24 h-160z" fill="#a8774f"/>${crenel(20, 180, 80, '#a8774f', 10)}<path d="M120 60 V20" stroke="#7a5232" stroke-width="3"/><path class="a-flag" d="M122 22 h34 l-6 10 l6 10 h-34z" fill="${P.red}"/>
        ${rect(0, 186, 200, 14, '#d9b98a')}`,
    },
    {
      era: ['Kittur Desais', 'ಕಿತ್ತೂರು ದೇಸಾಯಿಗಳು'],
      title: ['Rani Chennamma of Kittur', 'ಕಿತ್ತೂರು ರಾಣಿ ಚೆನ್ನಮ್ಮ'],
      sub: ['Defies the East India Company, 1824', 'ಈಸ್ಟ್ ಇಂಡಿಯಾ ಕಂಪನಿಗೆ ಸವಾಲು, 1824'],
      bubbles: [['Kittur is ours!', 'ಕಿತ್ತೂರು ನಮ್ಮದು!', 'left:14%;top:12%'], ['Retreat, retreat!', 'ಹಿಂದೆ ಸರಿಯಿರಿ!', 'right:-3%;top:44%', 1]],
      big: () => LEGACY.kitturBig,
      small: () => LEGACY.kitturSmall,
    },
    {
      era: ['Wodeyars of Mysuru', 'ಮೈಸೂರು ಒಡೆಯರು'],
      title: ['Bengaluru switches on', 'ಬೆಳಗಿದ ಬೆಂಗಳೂರು'],
      sub: ['Under Krishnaraja Wodeyar IV, street lights run on Shivanasamudra power, 1905', 'ನಾಲ್ವಡಿ ಕೃಷ್ಣರಾಜ ಒಡೆಯರ ಕಾಲದಲ್ಲಿ ಶಿವನಸಮುದ್ರದ ವಿದ್ಯುತ್ ದೀಪಗಳು, 1905'],
      bubbles: [['Power from Shivanasamudra!', 'ಶಿವನಸಮುದ್ರದ ವಿದ್ಯುತ್!', 'left:-6%;top:22%'], ['First in Asia!', 'ಏಷ್ಯಾದಲ್ಲೇ ಮೊದಲು!', 'right:-4%;top:40%', 1]],
      big: () => `${rect(0, 0, 400, 400, '#283466')}${stars([[40, 50], [110, 30], [200, 60], [300, 30], [360, 70], [250, 100]])}
        <g fill="#a8463a"><path d="M150 290 v-110 h240 v110z"/><path d="M240 180 l30 -24 l30 24z"/></g>
        <g fill="#efe3cf">${[170, 200, 230, 260, 290, 320, 350].map((x) => rect(x, 196, 10, 94, '#efe3cf')).join('')}${rect(150, 180, 240, 12, '#efe3cf')}</g>
        ${ground(290, '#4a4f6a', '#3f4460')}<path d="M0 330 Q200 316 400 334" stroke="#8b8fa8" stroke-width="3" stroke-dasharray="14 12" fill="none"/>
        ${[[120, 0], [210, 0.7], [300, 1.4]].map(([x, d]) => `${rect(x - 3, 210, 6, 104, '#1d1d24')}<path d="M${x - 12} 214 h24 l-4 -16 h-16z" fill="#1d1d24"/><circle class="a-light" style="animation-delay:${d}s" cx="${x}" cy="206" r="26" fill="#ffe28a"/><circle class="a-light" style="animation-delay:${d}s" cx="${x}" cy="206" r="8" fill="#fff6c8"/>`).join('')}
        ${figure({ x: 282, y: 398, s: 0.6, attire: 'saree', cloth: '#2f7d8c', blouse: P.gold, hair: 'bun', mark: 'bindi', mouth: 'o', brows: 'up', armR: 'raise', armL: 'down', flip: true, skin: P.skin.brown })}
        ${figure({ x: 328, y: 398, s: 0.62, attire: 'commoner', skin: P.skin.deep, wear: 'turban', wearColor: '#f4efe2', stache: 'thin', mouth: 'o', brows: 'up', armR: 'raise', animR: 'a-wave', armL: 'down', flip: true })}
        ${figure({ x: 76, y: 398, s: 0.98, attire: 'coat', cloth: '#efe4cc', sash: P.green, wear: 'peta', stache: 'thin', mark: 'tilak', armR: 'point', animR: 'a-point', armL: 'hip' })}`,
      small: () => `${rect(0, 0, 200, 200, '#d6ece4')}${boulder(30, 70, 50, 40, '#8f7f6a')}${boulder(170, 70, 50, 40, '#8f7f6a')}
        ${rect(60, 30, 80, 130, '#9fd3ea')}<g class="a-fall" stroke="#fff" stroke-width="3" stroke-linecap="round">${[70, 86, 100, 114, 130].map((x) => `<path d="M${x} 20 V170" stroke-dasharray="12 10"/>`).join('')}</g>
        ${rect(0, 150, 200, 50, '#5aa6c8')}<g class="a-puff"><circle cx="80" cy="156" r="12" fill="#fff" opacity=".8"/></g><g class="a-puff p2"><circle cx="120" cy="158" r="10" fill="#fff" opacity=".8"/></g>
        <path d="M176 120 l-10 40 h20z M166 132 h20" stroke="#5d6470" stroke-width="2.5" fill="none"/><path d="M170 104 l-4 10 h6 l-4 10" stroke="#ffd34d" stroke-width="2.5" fill="none" stroke-linecap="round"/>
        <text x="100" y="190" text-anchor="middle" font-family="Inter, sans-serif" font-size="12" font-weight="800" fill="#fff">1902</text>`,
    },
  ];

  // --------------------------------------------------------------- runtime
  const box = document.getElementById('scenes');
  const dots = document.getElementById('dots');
  const toggle = document.getElementById('playpause');
  const HOLD = 7000;
  const kn = () => document.documentElement.lang === 'kn';
  const txt = ([en, k]) => `data-en="${en.replace(/"/g, '&quot;')}" data-kn="${k.replace(/"/g, '&quot;')}">${kn() ? k : en}`;
  let at0 = 0;
  let timer = null;
  let playing = true;
  let onScreen = true;

  function build(sc) {
    const f = document.createElement('figure');
    f.className = 'scene';
    f.innerHTML = `<div class="disc big"><div class="face">${svg(400, sc.big())}</div>${sc.bubbles.map(([en, k, pos, r], i) =>
      `<span class="bubble${r ? ' r' : ''}" style="${pos};--d:${0.9 + i * 1.3}s" aria-hidden="true" ${txt([en, k])}</span>`).join('')}</div>
      <div class="disc small"><div class="face">${svg(200, sc.small())}</div></div>
      <figcaption><em class="era" ${txt(sc.era)}</em><b ${txt(sc.title)}</b><span ${txt(sc.sub)}</span></figcaption>`;
    return f;
  }

  function show(n) {
    at0 = (n + SCENES.length) % SCENES.length;
    const next = build(SCENES[at0]);
    box.querySelectorAll('.scene').forEach((old) => {
      old.classList.remove('active');
      setTimeout(() => old.remove(), 700);
    });
    box.appendChild(next);
    void next.offsetWidth; // commit the start state so the entrance animates
    next.classList.add('active');
    [...dots.children].forEach((d, k) => d.setAttribute('aria-current', k === at0 ? 'true' : 'false'));
  }
  function stop() { clearInterval(timer); timer = null; }
  function play() {
    stop();
    if (playing && !document.hidden && onScreen) timer = setInterval(() => show(at0 + 1), HOLD);
  }

  dots.innerHTML = SCENES.map((s) => `<button type="button" aria-label="${s.title[0].replace(/"/g, '&quot;')}"></button>`).join('');
  [...dots.children].forEach((d, k) => d.addEventListener('click', () => { show(k); play(); }));
  toggle.addEventListener('click', () => {
    playing = !playing;
    stage.classList.toggle('held', !playing);
    toggle.setAttribute('aria-label', playing ? 'Pause the illustrations' : 'Play the illustrations');
    toggle.textContent = playing ? '❚❚' : '▶';
    play();
  });
  document.addEventListener('visibilitychange', play);
  // Off screen, freeze the loops and the cycle so phones don't spend battery on them.
  if ('IntersectionObserver' in window) {
    new IntersectionObserver(([e]) => {
      onScreen = e.isIntersecting;
      stage.classList.toggle('paused', !onScreen);
      play();
    }).observe(stage);
  }

  show(0);
  play();
})();
