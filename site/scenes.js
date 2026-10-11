/* Hero decoration: cartoon moments from Karnataka's history, Kadambas to
 * Wodeyars and on to modern Karnataka (Tipu Sultan, Visvesvaraya, Vidhana
 * Soudha, sport, space), drawn as inline SVG and shuffled on every visit.
 * Independent of the search (app.js). Captions and speech bubbles carry
 * data-en/data-kn, so app.js's language switch translates them like any
 * other text.
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
    sultan: (c) => `<path d="M-36 -6 q0 -34 36 -36 q36 2 36 34 q-36 -14 -72 2z" fill="${c || P.cream}"/><path d="M-30 -14 q30 -12 60 0 M-32 -25 q32 -12 64 0" stroke="${P.gold}" stroke-width="2.5" fill="none"/><path d="M4 -38 q2 -22 14 -28 q-2 14 -8 28z" fill="#fff"/><circle cx="4" cy="-30" r="5" fill="${P.red}" stroke="${P.gold}" stroke-width="2"/><path d="M-16 -19 q16 6 32 0" stroke="#fff" stroke-width="2.6" stroke-dasharray=".1 4.2" stroke-linecap="round" fill="none"/>`,
    gandhi: () => `<path d="M-31 -12 q0 -20 31 -23 q31 3 31 23 q-31 -8 -62 0z" fill="#fbfaf5" stroke="#ddd7c8" stroke-width="1.5"/><path d="M0 -35 v21" stroke="#ddd7c8" stroke-width="1.5"/>`,
    topi: (c) => `<path d="M-33 -4 q-6 -40 30 -48 q40 4 36 48 q-33 -12 -66 0z" fill="${c || '#fbfaf5'}"/><path d="M-26 -18 q26 -10 54 0 M6 -50 q10 10 4 30" stroke="#ddd7ca" stroke-width="2" fill="none"/>`,
    tricorn: () => `<path d="M-42 -8 q10 -12 18 -10 q8 -26 24 -26 q16 0 24 26 q8 -2 18 10 q-42 -10 -84 0z" fill="#1d1d24"/><path d="M-38 -10 q38 -8 76 0" stroke="${P.gold}" stroke-width="2" fill="none"/>`,
  };
  const MARK = {
    vibhuti: `<path d="M-10 -19 h20 M-10 -16 h20 M-10 -13 h20" stroke="#fbf8f0" stroke-width="1.7" stroke-linecap="round"/><circle cy="-16" r="1.8" fill="${P.red}"/>`,
    namam: `<path d="M-5 -20 v6 q5 5 10 0 v-6" stroke="#fbf8f0" stroke-width="2.2" fill="none" stroke-linecap="round"/><path d="M0 -21 v9" stroke="${P.red}" stroke-width="2" stroke-linecap="round"/>`,
    bindi: `<circle cy="-12" r="2.4" fill="${P.red}"/>`,
    tilak: `<path d="M0 -20 v8" stroke="${P.red}" stroke-width="2.6" stroke-linecap="round"/>`,
  };

  // Faces are drawn from portrait references: a jawed face (not a disc),
  // light from the upper left, almond eyes with iris and lids, a modelled
  // nose and two-tone lips. Shape presets: [half-width, jaw half-width, chin y].
  const FACE = { m: [31, 24, 41], f: [29, 20, 39], long: [28, 20, 45], lean: [30, 21, 43], round: [33, 28, 40] };
  // Mix a #rrggbb colour toward black (f < 0) or white (f > 0).
  const tone = (hex, f) => {
    const n = parseInt(hex.slice(1), 16), t = f < 0 ? 0 : 255, a = Math.abs(f);
    return `#${[n >> 16, (n >> 8) & 255, n & 255].map((v) => Math.round(v + (t - v) * a).toString(16).padStart(2, '0')).join('')}`;
  };
  const mirror = (body) => `${body}<g transform="scale(-1 1)">${body}</g>`;
  const facePath = (w, j, c) => `M0 -37 C${w * 0.6} -37 ${w} -25 ${w} -7 C${w} 5 ${w - 1} 13 ${j + 3} 22 C${j - 1} 31 ${j * 0.55} ${c - 1} 0 ${c} C${-j * 0.55} ${c - 1} ${-j + 1} 31 ${-j - 3} 22 C${-w + 1} 13 ${-w} 5 ${-w} -7 C${-w} -25 ${-w * 0.6} -37 0 -37Z`;
  // Left brow (viewer's left); the right one is its mirror.
  const BROWS = {
    calm: 'M-21 -7 Q-13 -12.5 -4 -9 Q-13 -10 -21 -5.5Z', fierce: 'M-21 -11.5 Q-12 -11 -4 -6 Q-12 -8.5 -21 -9.5Z',
    worried: 'M-21 -6 Q-12 -9 -4 -12.5 Q-12 -7.5 -21 -4.5Z', up: 'M-21 -11 Q-13 -16.5 -4 -13 Q-13 -14 -21 -9.5Z',
  };
  // Moustaches sit between the nose (y 20) and the upper lip (my).
  const STACHE = {
    thin: (my) => `M-11 ${my - 2} Q-6 ${my - 5.5} 0 ${my - 4.2} Q6 ${my - 5.5} 11 ${my - 2} Q6 ${my - 3.2} 0 ${my - 2.8} Q-6 ${my - 3.2} -11 ${my - 2}Z`,
    full: (my) => `M-15 ${my + 1} Q-14 ${my - 7.5} 0 ${my - 6.5} Q14 ${my - 7.5} 15 ${my + 1} Q11 ${my - 2.4} 0 ${my - 2.6} Q-11 ${my - 2.4} -15 ${my + 1}Z`,
    handlebar: (my) => mirror(`<path d="M0 ${my - 6} C-7 ${my - 7.4} -14 ${my - 5.4} -17.5 ${my - 2.4} C-19.5 ${my - .6} -21.5 ${my - 3} -20.5 ${my - 6.4} C-23 ${my - 3.4} -22 ${my + 1.6} -17.5 ${my + .6} C-12 ${my - .2} -6 ${my - 2.6} 0 ${my - 2.6}Z"/>`),
  };

  function head(o) {
    const sk = o.skin, fem = o.attire === 'saree' || o.female, old = o.age === 'old', hair = o.hair || 'short';
    const [w, j, c] = FACE[o.face || (fem ? 'f' : 'm')];
    const dk = tone(sk, -0.2), dk2 = tone(sk, -0.42), lt = tone(sk, 0.16), ink = '#1d130d';
    const hr = o.hairColor || (old ? '#a39d93' : P.hair), my = c - 14;
    let s = '';

    // Behind the face: long hair, a veil, a bun, a top-knot.
    if (hair === 'long') s += `<path d="M${-w - 4} -6 C${-w - 7} -42 ${w + 7} -42 ${w + 4} -6 L${w + 9} 60 Q0 70 ${-w - 9} 60Z" fill="${hr}"/>`;
    if (hair === 'veil') s += `<path d="M${-w - 7} 0 C${-w - 9} -48 ${w + 9} -48 ${w + 7} 0 L${w + 13} 58 Q0 68 ${-w - 13} 58Z" fill="${o.veil || o.cloth}"/>`;
    if (hair === 'bun') s += `<circle cx="${-w + 1}" cy="-17" r="13" fill="${hr}"/><g fill="#fffdf5">${[[-9, -27], [-13, -16], [-10, -5]].map(([dx, dy]) => `<circle cx="${-w + dx}" cy="${dy}" r="3"/>`).join('')}</g>`;
    if (hair === 'jata') s += `<ellipse cy="-41" rx="13" ry="11" fill="${hr}"/><ellipse cy="-41" rx="13" ry="11" fill="none" stroke="#6b3a24" stroke-width="3.2" stroke-dasharray=".1 5" stroke-linecap="round"/>`;
    if (hair === 'sage') s += `<ellipse cy="-41" rx="11" ry="9" fill="${hr}"/>`;

    // The jaw's shadow on the neck, then ears, then the face.
    s += `<path d="M${-j * 0.62} ${c - 7} Q0 ${c + 9} ${j * 0.62} ${c - 7} L${j * 0.5} ${c + 7} Q0 ${c + 13} ${-j * 0.5} ${c + 7}Z" fill="${dk2}" opacity=".45"/>`;
    s += mirror(`<path d="M${-w + 3} -9 C${-w - 6} -14 ${-w - 10} -2 ${-w - 7} 8 C${-w - 5} 14 ${-w} 15 ${-w + 3} 11Z" fill="${sk}"/><path d="M${-w - 1} -5 C${-w - 6} -6 ${-w - 6} 4 ${-w - 2} 8" stroke="${dk}" stroke-width="1.6" fill="none" stroke-linecap="round"/>`);
    s += `<path d="${facePath(w, j, c)}" fill="${sk}"/>`;
    s += `<path d="M${w - 1} -10 C${w} 8 ${j + 4} 24 ${j * 0.3} ${c - 1} C${j + 1} 22 ${w - 6} 8 ${w - 6} -10Z" fill="${dk}" opacity=".6"/>`;
    s += `<path d="M${-w + 1} -4 C${-w + 1} 10 ${-j - 2} 22 ${-j + 4} 28 C${-j + 2} 18 ${-w + 5} 8 ${-w + 4} -4Z" fill="${dk}" opacity=".3"/>`;
    s += `<ellipse cx="-9" cy="-22" rx="12" ry="7" fill="${lt}" opacity=".45"/><ellipse cx="-15" cy="11" rx="6" ry="4" fill="${lt}" opacity=".35"/>`;
    s += mirror(`<ellipse cx="-12" cy="0" rx="9" ry="5.5" fill="${dk}" opacity=".35"/>`);
    if (fem) s += mirror(`<ellipse cx="-15" cy="13" rx="6" ry="3.5" fill="#d9665a" opacity=".16"/>`);
    if (old) s += `<path d="M-12 -27 q12 -3 24 0 M-10 -23 q10 -2.5 20 0" stroke="${dk}" stroke-width="1" fill="none" opacity=".8"/>`;

    // Hair in front: a hairline with sideburns, a centre parting, a veil's edge.
    const hairline = `M${-w - 1} -2 C${-w - 3} -30 -14 -42 2 -41 C20 -41 ${w + 3} -30 ${w + 1} -2 C${w - 2} -14 ${w - 6} -20 ${w - 12} -24 C10 -20 -6 -22 -18 -19 C${-w + 4} -15 ${-w + 2} -9 ${-w - 1} -2Z`;
    if (['short', 'jata', 'sage'].includes(hair)) {
      s += `<path d="${hairline}" fill="${hr}"/><path d="M${-w + .6} -8 l2.6 0 l-.8 9 l-1.8 -1.6z M${w - .6} -8 l-2.6 0 l.8 9 l1.8 -1.6z" fill="${hr}"/>`;
      s += `<path d="M-14 -36 Q-4 -40 8 -38" stroke="${tone(hr, 0.3)}" stroke-width="2" fill="none" stroke-linecap="round" opacity=".6"/>`;
    }
    if (hair === 'shaven' || hair === 'shikha') s += `<path d="${hairline}" fill="${hr}" opacity=".22"/>`;
    if (hair === 'shikha') s += `<path d="M-4 -36 q4 -16 14 -8 q-6 -1 -8 8z" fill="${hr}"/>`;
    if (hair === 'long' || hair === 'bun') {
      s += mirror(`<path d="M0 -37 C-12 -38 ${-w - 2} -30 ${-w - 1} -2 C${-w + 4} -18 -14 -27 0 -29Z" fill="${hr}"/>`);
      s += `<path d="M-6 -34 Q-16 -30 -22 -18 M6 -34 Q16 -30 22 -18" stroke="${tone(hr, 0.25)}" stroke-width="1.2" fill="none" opacity=".6"/>`;
    }
    if (hair === 'veil') s += `<path d="M${-w - 6} 4 C${-w - 7} -36 -16 -47 0 -47 C16 -47 ${w + 7} -36 ${w + 6} 4 C${w + 1} -18 16 -31 0 -31 C-16 -31 ${-w - 1} -18 ${-w - 6} 4Z" fill="${o.veil || o.cloth}"/><path d="M${-w - 2} 2 C${-w - 1} -18 -16 -32 0 -32 C16 -32 ${w + 1} -18 ${w + 2} 2" stroke="${o.border || P.gold}" stroke-width="2.4" fill="none"/>`;

    if (o.wear) s += `<g transform="translate(0 -3)">${WEAR[o.wear](o.wearColor)}</g>`;
    if (o.mark) s += MARK[o.mark];

    // Brows, eyes, nose.
    s += mirror(`<path d="${BROWS[o.brows || 'calm']}" fill="${old ? '#b3ada3' : hair === 'sage' ? '#cfc8bb' : ink}"/>`);
    const eye = `<path d="M-19 2 Q-12 -3.6 -5 2 Q-12 5.6 -19 2Z" fill="#f3ece2"/><circle cx="-12" cy="1.6" r="3.4" fill="${o.iris || '#3b2414'}"/><circle cx="-12" cy="1.6" r="1.7" fill="#0d0805"/><circle cx="-10.9" cy=".5" r=".9" fill="#fff"/>` +
      `<path d="M-20 2.4 Q-12 -4.4 -4.4 1.6${fem ? ' M-20 2.4 l-2.6 -1.8' : ''}" stroke="${ink}" stroke-width="${fem ? 2.2 : 1.6}" fill="none" stroke-linecap="round"/>` +
      `<path d="M-17.5 3.8 Q-12 6.2 -6.5 3.6" stroke="${dk2}" stroke-width=".7" fill="none" opacity=".7"/><path d="M-18 -1.6 Q-12 -5.4 -6 -2.4" stroke="${dk2}" stroke-width=".8" fill="none" opacity=".55"/>` +
      (old ? `<path d="M-17 6.4 Q-12 9 -7 6.4" stroke="${dk2}" stroke-width=".7" fill="none" opacity=".7"/>` : '');
    s += o.eyes === 'closed'
      ? mirror(`<path d="M-19 3 Q-12 6.4 -5 3" stroke="${ink}" stroke-width="1.8" fill="none" stroke-linecap="round"/><path d="M-16 5 l-1 2 M-12 5.8 v2 M-8 5 l1 2" stroke="${ink}" stroke-width=".8"/>`)
      : o.eyes === 'dizzy'
        ? mirror(`<path d="M-16 -2 l7 7 M-9 -2 l-7 7" stroke="${ink}" stroke-width="2" stroke-linecap="round"/>`)
        : `<g class="a-blink">${mirror(eye)}</g>`;
    s += `<path d="M2 -4 C3 4 5 9 6.5 13" stroke="${dk}" stroke-width="2.2" fill="none" opacity=".75" stroke-linecap="round"/>`;
    s += `<path d="M-6.5 14.5 C-9 16.5 -7.5 20 -4 19.5 C-2 21 2 21 4 19.5 C7.5 20 9 16.5 6.5 14.5" stroke="${dk2}" stroke-width="1.4" fill="none" stroke-linecap="round"/>`;
    s += `<ellipse cx="-3" cy="18.6" rx="1.6" ry="1" fill="${dk2}"/><ellipse cx="3" cy="18.6" rx="1.6" ry="1" fill="${dk2}"/><ellipse cx="-1" cy="14.4" rx="2.4" ry="1.6" fill="${lt}" opacity=".6"/>`;
    s += `<path d="M-5 ${my + 7.5} Q0 ${my + 9.5} 5 ${my + 7.5}" stroke="${dk}" stroke-width="1.4" fill="none" opacity=".6" stroke-linecap="round"/>`;
    if (!fem) s += mirror(`<path d="M-7.5 18.5 Q-11.5 23 -10.5 ${my + 1}" stroke="${dk}" stroke-width="1.2" fill="none" opacity="${old ? '.9' : '.5'}"/>`);

    // Beard under the mouth, then the mouth, then the moustache over the lip.
    if (o.beard) {
      const by = o.beard === 'long' ? c + 26 : c + 7, bc = o.beard === 'long' ? c + 16 : c + 4;
      s += `<path d="M${-w + 1} -2 C${-w} 18 ${-j * 0.8} ${bc} 0 ${by} C${j * 0.8} ${bc} ${w} 18 ${w - 1} -2 C${w - 4} 12 ${j} 24 ${j - 6} 28 Q0 ${my + 4} ${-j + 6} 28 C${-j} 24 ${-w + 4} 12 ${-w + 1} -2Z" fill="${hr}"/>`;
    }
    const L1 = fem ? '#9c3b36' : tone(sk, -0.38), L2 = fem ? '#b9544a' : tone(sk, -0.2), gum = '#4a1d18', teeth = '#f4f0e8';
    const lips = `<path d="M-8.5 ${my} Q-4 ${my - 2.4} 0 ${my - 1} Q4 ${my - 2.4} 8.5 ${my} Q0 ${my + 1.2} -8.5 ${my}Z" fill="${L1}"/><path d="M-7.5 ${my + .4} Q0 ${my + 5.4} 7.5 ${my + .4} Q0 ${my + 1.8} -7.5 ${my + .4}Z" fill="${L2}"/>`;
    const open = `<path d="M-8 ${my - 1} Q0 ${my - 3} 8 ${my - 1} Q7 ${my + 8} 0 ${my + 9} Q-7 ${my + 8} -8 ${my - 1}Z" fill="${gum}"/><path d="M-6.5 ${my - .6} Q0 ${my - 2} 6.5 ${my - .6} L6 ${my + 1.6} Q0 ${my + .6} -6 ${my + 1.6}Z" fill="${teeth}"/><path d="M-8 ${my - 1} Q0 ${my - 3.4} 8 ${my - 1}" stroke="${L1}" stroke-width="2" fill="none"/>`;
    s += {
      smile: `${lips}<path d="M-9.5 ${my - 1.6} Q0 ${my + 2.6} 9.5 ${my - 1.6}" stroke="${ink}" stroke-width="1" fill="none" opacity=".75"/>`,
      flat: `${lips}<path d="M-8.5 ${my} Q0 ${my + 1} 8.5 ${my}" stroke="${ink}" stroke-width="1" fill="none" opacity=".75"/>`,
      open,
      talk: `<g class="a-talk">${open}</g>`,
      o: `<ellipse cy="${my + 2}" rx="3.8" ry="4.6" fill="${gum}" stroke="${L2}" stroke-width="1.8"/>`,
      grin: `<path d="M-10 ${my - 1.5} Q0 ${my - 3} 10 ${my - 1.5} Q8 ${my + 8} 0 ${my + 8.5} Q-8 ${my + 8} -10 ${my - 1.5}Z" fill="${gum}"/><path d="M-8.6 ${my - 1} Q0 ${my - 2.4} 8.6 ${my - 1} L8 ${my + 2.6} Q0 ${my + 1.4} -8 ${my + 2.6}Z" fill="${teeth}"/>`,
    }[o.mouth || 'smile'];
    if (o.stache) s += `<g fill="${hr}">${o.stache === 'handlebar' ? STACHE.handlebar(my) : `<path d="${STACHE[o.stache](my)}"/>`}</g>`;

    if (o.studs !== false) s += mirror(`<circle cx="${-w - 5}" cy="12" r="${fem ? 2.6 : 2.4}" fill="${P.gold}"/>${fem ? `<path d="M${-w - 8} 15 q3 -3 6 0 l-1 5 h-4z" fill="${P.gold}"/>` : ''}`);
    if (o.nosering) s += `<circle cx="-5.5" cy="19.5" r="2.6" fill="none" stroke="${P.gold}" stroke-width="1.2"/>`;
    return s;
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
    racquet: (x, y) => [`<path d="M${x} ${y + 4} L${x + 4} ${y - 38}" stroke="#3a3a44" stroke-width="3" stroke-linecap="round"/><ellipse cx="${x + 6}" cy="${y - 54}" rx="11" ry="16" fill="rgba(255,255,255,.15)" stroke="#c8352b" stroke-width="3"/><path d="M${x - 4} ${y - 58} h20 M${x - 4} ${y - 50} h20 M${x + 2} ${y - 69} v30 M${x + 10} ${y - 69} v30" stroke="#e8e8e8" stroke-width="1"/>`, ''],
    scroll: (x, y) => ['', `<rect x="${x - 22}" y="${y - 6}" width="44" height="11" rx="5.5" fill="#3f6fb0"/><path d="M${x - 16} ${y - 1} h32" stroke="#cfe0f5" stroke-width="1.5"/>`],
    torch: (x, y) => [`<path d="M${x} ${y + 8} L${x + 6} ${y - 24}" stroke="${P.wood}" stroke-width="4" stroke-linecap="round"/><path class="a-flicker" d="M${x + 6} ${y - 24} q-9 -10 0 -24 q9 12 0 24z" fill="#ff9a1f"/>`, ''],
    kflag: (x, y) => [`<path d="M${x} ${y + 30} V${y - 96}" stroke="#7a5232" stroke-width="4"/><g class="a-flag"><path d="M${x + 2} ${y - 96} h54 v15 h-54z" fill="#f5c518"/><path d="M${x + 2} ${y - 81} h54 v15 h-54z" fill="#d9381e"/></g>`, ''],
    // A Jain monk's peacock-feather whisk.
    pichhi: (x, y) => [`<path d="M${x} ${y + 8} L${x + 2} ${y - 26}" stroke="${P.wood}" stroke-width="3" stroke-linecap="round"/><path d="M${x - 11} ${y - 24} q13 -32 26 0 q-13 8 -26 0z" fill="#2f7d6a"/><circle cx="${x + 2}" cy="${y - 31}" r="5" fill="#1f4f9a"/><circle cx="${x + 2}" cy="${y - 31}" r="2.2" fill="${P.gold}"/>`, ''],
    shield: (x, y) => ['', `<circle cx="${x}" cy="${y}" r="24" fill="#a8473b" stroke="${P.gold}" stroke-width="4"/><circle cx="${x}" cy="${y}" r="6" fill="${P.gold}"/>`],
  };
  const SLEEVE = { jama: 'cloth', robe: 'cloth', coat: 'cloth', monk: 'cloth', soldier: 'cloth', euro: 'cloth' };

  function arm(side, o) {
    const type = o['arm' + side];
    if (!type) return '';
    const [d, hx, hy] = ARM[type];
    const col = o.sleeve || (SLEEVE[o.attire] ? o.cloth : o.skin);
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
      case 'jama': return `${neck}<path d="${torso}" fill="${o.cloth}"/><path d="${o.stripe === false ? '' : 'M-20 -108 q6 8 0 16 M0 -110 q6 8 0 16 M20 -108 q6 8 0 16 M-22 -88 q6 8 0 16 M-2 -90 q6 8 0 16 M18 -88 q6 8 0 16'}" stroke="${o.stripe || '#3a2418'}" stroke-width="3.4" fill="none" stroke-linecap="round" opacity=".8"/>${rect(-34, -64, 68, 9, o.sash || P.green, 3)}<path d="M-14 -114 q14 24 28 0" stroke="#fff" stroke-width="3" stroke-dasharray=".1 4.4" stroke-linecap="round" fill="none"/>`;
      case 'shirt': return `${neck}<path d="${torso}" fill="${o.cloth}"/><path d="M-12 -116 l12 12 l12 -12" stroke="rgba(0,0,0,.18)" stroke-width="3" fill="none" stroke-linejoin="round"/>${o.id ? `<path d="M-9 -112 l9 28 l9 -28" stroke="#2b5ea8" stroke-width="2" fill="none"/><rect x="-7" y="-86" width="14" height="16" rx="2" fill="#fff" stroke="#2b5ea8" stroke-width="1.5"/>` : ''}`;
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
      case 'jama': return `${feet}<path d="M-34 -58 h68 l16 52 h-100z" fill="${o.cloth}"/><path d="${o.stripe === false ? '' : 'M-26 -46 q6 8 0 16 M-6 -48 q6 8 0 16 M14 -48 q6 8 0 16 M30 -40 q4 6 0 12'}" stroke="${o.stripe || '#3a2418'}" stroke-width="3.4" fill="none" stroke-linecap="round" opacity=".8"/>${rect(-50, -12, 100, 6, P.gold, 2)}`;
      case 'shirt': {
        const sh = o.shoes || '#2b2b33', shoes = `<ellipse cx="-17" cy="-3" rx="11" ry="5" fill="${sh}"/><ellipse cx="17" cy="-3" rx="11" ry="5" fill="${sh}"/>`;
        return o.shorts
          ? `${shoes}${rect(-22, -40, 11, 36, o.skin, 4)}${rect(11, -40, 11, 36, o.skin, 4)}<path d="M-31 -58 h62 l4 24 h-26 l-9 -8 l-9 8 h-26z" fill="${o.lower || P.white}"/>`
          : `${shoes}<path d="M-31 -58 h62 l-2 54 h-22 l-7 -42 l-7 42 h-22z" fill="${o.lower || '#3a4256'}"/>`;
      }
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
    bubri: '<path d="M-16 -12 q7 9 0 18 q-7 9 0 18 M0 -14 q7 10 0 20 M16 -12 q7 9 0 18 q-7 9 0 18" stroke="currentColor" stroke-width="4" fill="none" stroke-linecap="round" transform="translate(0 -6)"/>',
  };
  function dravida(x, y, s, c1 = '#d9a87a', c2 = '#c48d5f') {
    return at(x, y, s, `${rect(-64, -22, 128, 22, c2)}${rect(-50, -84, 100, 62, c1)}<path d="M-38 -84 v62 M-14 -84 v62 M14 -84 v62 M38 -84 v62" stroke="${c2}" stroke-width="3"/><path d="M-12 -22 v-36 q12 -14 24 0 v36z" fill="#6e4a32"/><path d="M-60 -84 h120 l-12 -18 h-96z" fill="${c2}"/><path d="M-44 -102 h88 l-10 -18 h-68z" fill="${c1}"/><path d="M-30 -120 h60 l-9 -16 h-42z" fill="${c2}"/><path d="M-20 -136 q20 -34 40 0z" fill="${c1}"/>${rect(-3, -176, 6, 10, P.gold, 2)}`);
  }
  // Animals are drawn from life (proportions, markings), feet at (0,0).

  /** An Asian elephant facing right: twin-domed head, small ear, tusk, toenails. */
  function elephant(o) {
    const c = o.color || '#8f949e', d = o.dark || '#7a7f8a', w = o.walk ? ' slow' : '';
    const leg = (x, col, cls) => anim(o.walk ? cls + w : '', `<path d="M${x} -58 h22 v52 q0 6 -6 6 h-10 q-6 0 -6 -6z" fill="${col}"/><path d="M${x + 3} -3 q3 -3 6 0 M${x + 10} -3 q3 -3 6 0" stroke="#e8e1cf" stroke-width="2" fill="none" stroke-linecap="round"/><path d="M${x + 4} -24 q7 2 14 0 M${x + 4} -18 q7 2 14 0" stroke="${d}" stroke-width="1.4" fill="none" opacity=".7"/>`);
    let s = `<path d="M-62 -76 q-9 18 -7 38" stroke="${c}" stroke-width="3.5" fill="none" stroke-linecap="round"/><path d="M-73 -40 l4 12 l5 -11z" fill="#3a3a44"/>` +
      leg(-46, d, 'a-legb') + leg(18, d, 'a-legf') +
      `<path d="M-64 -46 C-76 -82 -50 -112 -8 -110 C22 -110 42 -100 50 -84 L56 -48 Q-4 -32 -64 -46Z" fill="${c}"/><path d="M-44 -56 q22 6 46 2" stroke="${d}" stroke-width="2" fill="none" opacity=".6"/>` +
      leg(-60, c, 'a-legf') + leg(32, c, 'a-legb') +
      `<path d="M36 -98 C36 -124 64 -134 82 -124 C94 -116 96 -98 92 -84 C88 -72 80 -66 68 -64 L48 -60Z" fill="${c}"/><path d="M62 -130 q5 6 3 13" stroke="${d}" stroke-width="2" fill="none" stroke-linecap="round"/>` +
      `<path d="M50 -110 C34 -112 30 -86 36 -70 C42 -60 54 -64 58 -76 C60 -90 58 -104 50 -110Z" fill="${d}"/>` +
      anim('a-trunk', `<path d="M78 -82 C94 -78 100 -56 98 -32 C97 -18 98 -10 106 -8 C109 -5 105 0 98 -2 C88 -5 86 -18 86 -30 C86 -50 80 -62 66 -68Z" fill="${c}"/><path d="M86 -58 q6 -2 11 2 M88 -46 q5 -2 9 2 M88 -34 q5 -2 9 2" stroke="${d}" stroke-width="1.8" fill="none"/>`, '0% 0%') +
      `<path d="M80 -70 q10 12 24 8" stroke="#f4eedd" stroke-width="5" fill="none" stroke-linecap="round"/>` +
      `<path d="M62 -101 q4 -3 8 0" stroke="#3a3a44" stroke-width="1.6" fill="none"/><circle cx="66" cy="-98" r="2.4" fill="#2b2b38"/>`;
    if (o.cloth) s += `<path d="M-42 -106 h72 v48 q-36 12 -72 0z" fill="${o.cloth}"/><path d="M-42 -58 q36 12 72 0" stroke="${P.gold}" stroke-width="4" fill="none"/><g fill="${P.gold}">${[-34, -18, -2, 14].map((x) => `<circle cx="${x}" cy="-50" r="2.6"/>`).join('')}</g><path d="M72 -126 q12 2 18 12 l-4 32 q-6 4 -12 -2z" fill="${P.gold}"/><circle cx="80" cy="-104" r="3" fill="${P.red}"/>`;
    if (o.ambari) s += `<circle class="a-pulse" cx="0" cy="-130" r="44" fill="#ffd36b" opacity=".35"/><path d="M-30 -100 v-34 h60 v34z" fill="${P.gold}" stroke="${P.goldD}" stroke-width="2"/><path d="M-36 -134 h72 l-8 -10 h-56z" fill="${P.goldD}"/><path d="M-22 -144 q22 -36 44 0z" fill="${P.gold}" stroke="${P.goldD}" stroke-width="2"/><circle cy="-182" r="5" fill="${P.gold}"/><path d="M-20 -128 h40 M-20 -116 h40" stroke="${P.goldD}" stroke-width="2"/>`;
    return at(o.x, o.y, o.s || 1, anim(o.walk ? 'a-plod' : '', s), o.flip ? -(o.s || 1) : (o.s || 1));
  }

  /** A bay horse facing right: arched neck, black mane, tail and lower legs. */
  function horse(o) {
    const c = o.color || '#8b5a3c', dk = o.dark || '#74472f', k = '#2b1a10', h = '#17110c';
    const fore = (x, col, cls) => anim(cls, `<path d="M${x} -64 L${x + 1} -32" stroke="${col}" stroke-width="11" stroke-linecap="round"/><path d="M${x + 1} -34 L${x} -7" stroke="${k}" stroke-width="7.5" stroke-linecap="round"/>${rect(x - 5, -8, 11, 8, h, 2)}`);
    const hind = (x, col, cls) => anim(cls, `<path d="M${x} -66 Q${x + 9} -46 ${x - 4} -32" stroke="${col}" stroke-width="12" fill="none" stroke-linecap="round"/><path d="M${x - 4} -34 L${x} -7" stroke="${k}" stroke-width="7.5" stroke-linecap="round"/>${rect(x - 5, -8, 11, 8, h, 2)}`);
    const s = anim('a-tail', `<path d="M-60 -86 C-84 -84 -92 -58 -86 -28 C-78 -48 -70 -64 -58 -74Z" fill="${k}"/>`) +
      hind(-46, dk, 'a-legf') + fore(32, dk, 'a-legb') +
      `<path d="M-62 -70 C-66 -94 -40 -100 -6 -96 C18 -94 34 -100 48 -98 C60 -92 64 -74 56 -62 C44 -50 18 -50 -8 -52 C-34 -52 -58 -52 -62 -70Z" fill="${c}"/>` +
      hind(-36, c, 'a-legb') + fore(44, c, 'a-legf') +
      `<path d="M38 -96 C46 -120 60 -140 76 -146 L92 -128 C82 -114 70 -96 60 -66Z" fill="${c}"/>` +
      `<path d="M74 -150 l2 -14 l8 11z" fill="${c}"/><path d="M70 -150 C80 -158 94 -152 102 -138 L116 -118 C119 -111 113 -105 106 -107 L86 -113 C78 -118 72 -130 70 -150Z" fill="${c}"/>` +
      `<path d="M102 -124 L116 -118 C119 -111 113 -105 106 -107 L98 -110z" fill="rgba(0,0,0,.2)"/>` +
      `<path d="M72 -150 C58 -138 46 -120 36 -96 L46 -94 C54 -112 64 -128 80 -142Z" fill="${k}"/><path d="M78 -152 q9 3 7 13 q-6 -4 -10 -9z" fill="${k}"/>` +
      `<path d="M88 -144 L104 -112 M86 -120 L108 -116" stroke="#5a2a1a" stroke-width="2" fill="none"/><circle cx="90" cy="-136" r="2.6" fill="${h}"/><circle cx="111" cy="-113" r="1.6" fill="${h}"/>` +
      (o.cloth ? `<path d="M-36 -94 h64 l-6 36 h-52z" fill="${o.cloth}"/><path d="M-32 -62 h50" stroke="${P.gold}" stroke-width="4"/>` : '');
    return at(o.x, o.y, o.s || 1, anim(o.gallop ? 'a-gallop' : '', s + (o.rider || '')), o.flip ? -(o.s || 1) : (o.s || 1));
  }

  /** A tiger rearing up on its hind legs, facing left. */
  function tiger(x, y, s) {
    const O = '#f08a24', D = '#cf6a14', K = '#2e1c12', W = '#fff4e2';
    const tail = 'M30 -38 q46 -4 46 -54 q0 -14 -10 -18';
    // Stripes start at the back edge of the tilted body and curl inward.
    const stripes = [-40, -22, -4, 14, 32].map((t) => {
      const w = 30 * Math.sqrt(1 - (t / 62) ** 2) - 1;
      return `M${(10 - t * 0.423 + w * 0.906).toFixed(1)} ${(-80 - t * 0.906 - w * 0.423).toFixed(1)} q-8 -2 -17 7 q-3 3 -8 3`;
    }).join(' ');
    return at(x, y, s, anim('a-pounce', `${anim('a-tail', `<path d="${tail}" stroke="${O}" stroke-width="11" fill="none" stroke-linecap="round"/><path d="${tail}" stroke="${K}" stroke-width="11" fill="none" stroke-dasharray="4 11"/><circle cx="66" cy="-110" r="6" fill="${K}"/>`, '0% 100%')}
    <path d="M18 -40 q10 18 9 36" stroke="${D}" stroke-width="18" stroke-linecap="round" fill="none"/><ellipse cx="29" cy="-3" rx="12" ry="5.5" fill="${D}"/>
    <path d="M-4 -116 q-30 -14 -54 -22" stroke="${D}" stroke-width="15" stroke-linecap="round" fill="none"/><circle cx="-60" cy="-139" r="11" fill="${D}"/><path d="M-30 -128 l2 12 M-42 -133 l2 11" stroke="${K}" stroke-width="3.5" stroke-linecap="round"/>
    <ellipse cx="10" cy="-80" rx="30" ry="62" fill="${O}" transform="rotate(-25 10 -80)"/><ellipse cx="-4" cy="-76" rx="14" ry="48" fill="${W}" transform="rotate(-25 -4 -76)"/>
    <path d="${stripes}" stroke="${K}" stroke-width="5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
    <path d="M-2 -42 q-4 20 -8 38" stroke="${O}" stroke-width="20" stroke-linecap="round" fill="none"/><ellipse cx="-14" cy="-3" rx="14" ry="6.5" fill="${O}"/>
    <path d="M-15 -30 h10 M-16 -19 h10" stroke="${K}" stroke-width="4" stroke-linecap="round"/>
    <path d="M-2 -104 q-30 4 -54 0" stroke="${O}" stroke-width="16" stroke-linecap="round" fill="none"/><circle cx="-57" cy="-104" r="11.5" fill="${O}"/>
    <path d="M-22 -112 v14 M-34 -111 v13 M-46 -110 v11" stroke="${K}" stroke-width="4" stroke-linecap="round"/>
    <path d="M-67 -111 l-6 -3 M-69 -104 h-6 M-67 -97 l-6 3 M-69 -145 l-6 -2 M-70 -138 h-6" stroke="#fff" stroke-width="2.4" stroke-linecap="round"/>
    <circle cx="-16" cy="-173" r="9" fill="${K}"/><circle cx="-16" cy="-173" r="5" fill="${W}"/><circle cx="-44" cy="-175" r="9" fill="${K}"/><circle cx="-44" cy="-175" r="5" fill="${W}"/>
    <path d="M-4 -150 l9 3 l-6 5 l8 5 l-9 3 l3 6 l-10 -2" fill="${W}"/>
    <path d="M-57 -150 C-57 -170 -42 -180 -28 -178 C-12 -176 -3 -165 -4 -150 C-4 -138 -10 -128 -20 -124 L-44 -124 C-52 -130 -57 -140 -57 -150Z" fill="${O}"/>
    <ellipse cx="-19" cy="-134" rx="11" ry="9" fill="${W}"/><ellipse cx="-45" cy="-137" rx="16" ry="12" fill="${W}"/>
    <ellipse cx="-44" cy="-161" rx="4.5" ry="2.4" fill="${W}"/><ellipse cx="-24" cy="-161" rx="4.5" ry="2.4" fill="${W}"/>
    <path d="M-30 -178 v10 M-38 -176 l2 8 M-22 -176 l-2 8 M-5 -156 h-8 M-5 -146 h-9 M-54 -152 h6" stroke="${K}" stroke-width="3.2" stroke-linecap="round"/>
    <ellipse cx="-43" cy="-153" rx="4.6" ry="3.8" fill="#f6e04b"/><ellipse cx="-24" cy="-153" rx="4.6" ry="3.8" fill="#f6e04b"/><circle cx="-44" cy="-153" r="2.2" fill="${K}"/><circle cx="-25" cy="-153" r="2.2" fill="${K}"/>
    <path d="M-50 -158 l11 2 M-17 -158 l-11 2" stroke="${K}" stroke-width="2.6" stroke-linecap="round"/>
    <path d="M-55 -146 h11 l-5.5 7z" fill="#b5555a"/><path d="M-49.5 -139 v4" stroke="${K}" stroke-width="1.6"/>
    <path d="M-60 -134 q11 16 24 2z" fill="#7a2b22"/><path d="M-56 -134 l2.2 6 l2.2 -6 M-43 -134 l2.2 6 l2.2 -6" fill="#fff"/>
    <g fill="${K}"><circle cx="-54" cy="-138" r=".9"/><circle cx="-50" cy="-137" r=".9"/><circle cx="-40" cy="-137" r=".9"/></g>`));
  }

  /** A Mudhol hound, Karnataka's own sighthound, running left. */
  function hound(x, y, s, delay) {
    const c = '#b07d4c', d = '#8c5f35', k = '#2b2118';
    const leg = (p, col, cls) => anim(cls, `<path d="${p}" stroke="${col}" stroke-width="4.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>`);
    return at(x, y, s, `<g class="a-run" style="animation-delay:${delay || 0}s">${leg('M-16 -26 L-20 -12 L-24 0', d, 'a-legb')}${leg('M18 -32 Q28 -18 20 -10 L24 0', d, 'a-legf')}
      <path d="M24 -36 q16 2 16 18 q0 4 4 4" stroke="${c}" stroke-width="2.6" fill="none" stroke-linecap="round"/>
      <path d="M-26 -40 C-30 -26 -22 -20 -12 -20 C-2 -22 6 -30 14 -30 C22 -30 26 -30 28 -34 C30 -42 22 -46 10 -44 C-2 -42 -14 -48 -26 -40Z" fill="${c}"/>
      ${leg('M-12 -24 L-14 -12 L-18 0', c, 'a-legf')}${leg('M22 -34 Q34 -20 26 -10 L30 0', c, 'a-legb')}
      <path d="M-26 -42 L-32 -54 L-22 -58 L-14 -44Z" fill="${c}"/>
      <path d="M-28 -60 C-36 -62 -46 -58 -56 -52 L-57 -49 C-48 -48 -36 -48 -24 -52Z" fill="${c}"/>
      <path d="M-28 -60 q8 -2 12 6 q-8 0 -12 -6z" fill="${d}"/><path d="M-26 -50 l6 4" stroke="#b5462e" stroke-width="2.4" stroke-linecap="round"/>
      <circle cx="-40" cy="-55" r="1.8" fill="${k}"/><circle cx="-56" cy="-50.5" r="2" fill="${k}"/></g>`);
  }

  /** A black-naped hare, the common hare of the Deccan, bounding left. */
  const hare = (x, y, s) => at(x, y, s, anim('a-hop', `<ellipse cx="-4" cy="-52" rx="4.5" ry="15" fill="#9c7d5c" transform="rotate(10 -4 -52)"/><ellipse cx="-1.6" cy="-64.5" rx="3.6" ry="3.4" fill="#2b2118"/>
    <ellipse cx="18" cy="-6" rx="14" ry="6" fill="#9c7d5c"/>
    <path d="M-14 -12 C-20 -26 -6 -36 12 -34 C28 -32 34 -18 28 -8 C20 0 -6 0 -14 -12Z" fill="#b3926c"/><path d="M-10 -10 C-2 -4 14 -4 24 -8" stroke="#e9dcc6" stroke-width="4" fill="none" stroke-linecap="round"/>
    <circle cx="30" cy="-22" r="4.5" fill="#fff"/><path d="M26 -24 q4 -4 8 0z" fill="#2b2118"/>
    <path d="M-12 -12 l-10 10 M-6 -10 l-8 10" stroke="#9c7d5c" stroke-width="4" stroke-linecap="round"/>
    <ellipse cx="-12" cy="-50" rx="4.5" ry="15" fill="#b3926c" transform="rotate(-20 -12 -50)"/><ellipse cx="-16.4" cy="-62.5" rx="3.6" ry="3.4" fill="#2b2118"/>
    <path d="M-10 -38 q8 2 8 10 q-6 -2 -10 -4z" fill="#2b2118"/>
    <ellipse cx="-18" cy="-30" rx="11" ry="9" fill="#b3926c"/><circle cx="-21" cy="-32" r="2.6" fill="#2b2118"/><circle cx="-21.8" cy="-32.8" r=".8" fill="#fff"/><circle cx="-28.5" cy="-28" r="1.6" fill="#b5555a"/>`));

  /** A wild boar facing right: bristled back, tusks. */
  const boar = () => `<path d="M-36 -30 q-9 0 -9 9" stroke="#3a2c26" stroke-width="2" fill="none"/><path d="M-47 -22 l3 5 l3 -5z" fill="#3a2c26"/>
    ${rect(-26, -20, 6, 20, '#3a2c26', 2)}${rect(22, -20, 6, 20, '#3a2c26', 2)}
    <path d="M-36 -20 C-42 -38 -24 -50 0 -50 C18 -50 30 -44 36 -34 L40 -22 C30 -14 -20 -12 -36 -20Z" fill="#4a3a33"/>
    ${rect(-18, -20, 6, 20, '#4a3a33', 2)}${rect(30, -20, 6, 20, '#4a3a33', 2)}
    <path d="M-24 -46 l4 -7 l4 5 l4 -8 l4 6 l4 -8 l4 6 l4 -7 l4 5 l4 -5" stroke="#2b201b" stroke-width="2.4" fill="none" stroke-linejoin="round"/>
    <path d="M28 -44 C40 -44 50 -36 58 -27 L60 -20 C56 -18 46 -18 34 -22Z" fill="#4a3a33"/><path d="M30 -44 l2 -11 l7 9z" fill="#3a2c26"/>
    <ellipse cx="59.5" cy="-23.5" rx="2.6" ry="4" fill="#2b201b"/><path d="M50 -20 q5 -6 2 -13" stroke="#f4eedd" stroke-width="2.6" fill="none" stroke-linecap="round"/><circle cx="41" cy="-36" r="1.9" fill="#160f0b"/>`;
  const stoneSlab = (lines, label, bg = '#efe4d0') => `${rect(0, 0, 200, 200, bg)}${rect(0, 156, 200, 44, '#d8c7a6')}<path d="M46 160 V60 q0 -26 48 -26 q48 0 48 26 V160z" fill="#b8ab95"/><path d="M52 156 V62 q0 -20 42 -20 q42 0 42 20 V156z" fill="#cdc1ac"/>
    <g stroke="#6e6252" stroke-width="4" stroke-linecap="round" fill="none">${lines.map((w, i) => `<path class="a-draw" style="--i:${i}" pathLength="1" d="M62 ${68 + i * 16} h${w}"/>`).join('')}</g>
    <path d="M124 132 l18 -20 l5 5 l-18 20z" fill="#6b7280"/><circle cx="146" cy="116" r="8" fill="${P.skin.wheat}"/>
    <g class="a-spark"><path d="M120 136 l-8 -2 M122 142 l-8 6 M126 144 l0 8" stroke="#f5b301" stroke-width="2.5" stroke-linecap="round"/></g>
    <g class="a-tap" style="transform-origin: 100% 50%">${rect(146, 88, 18, 12, '#6b7280', 3)}${rect(162, 91, 28, 6, P.wood, 3)}</g>
    <text x="96" y="184" text-anchor="middle" font-family="Inter, sans-serif" font-size="13" font-weight="800" fill="#8a7a62">${label}</text>`;
  const notes = (x, y) => `<g fill="#7a4a9a">${[0, 1, 2].map((i) => `<g class="a-note" style="animation-delay:-${i * 1.1}s"><path d="M${x + i * 14} ${y} v-16 l10 -3 v14" stroke="#7a4a9a" stroke-width="2.2" fill="none"/><ellipse cx="${x + i * 14 - 2}" cy="${y}" rx="4" ry="3"/><ellipse cx="${x + i * 14 + 8}" cy="${y - 3}" rx="4" ry="3"/></g>`).join('')}</g>`;
  // A Mysorean war rocket: iron tube on a bamboo guide stick, pointing +x.
  const rocketBody = () => `<path d="M-46 0 H-4" stroke="#b08a4a" stroke-width="2.6"/>${rect(-6, -4, 20, 8, '#4a4f5a', 2)}<path d="M14 -4 l8 4 l-8 4z" fill="#4a4f5a"/>`;
  const rocket = (x, y, ang, dist, delay) => `<g transform="translate(${x} ${y}) rotate(${ang})"><g class="a-rocket" style="--dx:${dist}px;--dy:0px;animation-delay:${delay}s"><path d="M-6 -4 l-18 4 l18 4z" fill="#ffb02e"/><circle cx="-30" cy="0" r="5" fill="#e9e2d4" opacity=".7"/><circle cx="-40" cy="1" r="4" fill="#e9e2d4" opacity=".5"/>${rocketBody()}</g></g>`;

  // ------------------------------------------------------------- scenes
  const LEGACY = {"pulakeshiBig": "<rect width=\"400\" height=\"400\" fill=\"#fdecd8\"/><circle class=\"a-pulse\" cx=\"292\" cy=\"92\" r=\"32\" fill=\"#ffc55a\"/><g class=\"a-drift\" fill=\"#fff\"><circle cx=\"86\" cy=\"96\" r=\"14\"/><circle cx=\"104\" cy=\"88\" r=\"18\"/><circle cx=\"124\" cy=\"97\" r=\"12\"/><rect x=\"72\" y=\"96\" width=\"64\" height=\"13\" rx=\"6.5\"/></g><g class=\"a-drift slow\" fill=\"#fff\" opacity=\".8\"><circle cx=\"196\" cy=\"146\" r=\"10\"/><circle cx=\"210\" cy=\"140\" r=\"13\"/><circle cx=\"224\" cy=\"147\" r=\"9\"/><rect x=\"186\" y=\"146\" width=\"46\" height=\"10\" rx=\"5\"/></g><path d=\"M0 212 Q60 168 128 196 T262 186 T400 182 V230 H0Z\" fill=\"#efd3aa\"/><rect y=\"222\" width=\"400\" height=\"40\" fill=\"#dccf94\"/><rect y=\"258\" width=\"400\" height=\"44\" fill=\"#7db7de\"/><g class=\"a-flow\" stroke=\"#fff\" stroke-opacity=\".75\" stroke-width=\"3\" stroke-linecap=\"round\"><path d=\"M-40 270 H440\" stroke-dasharray=\"16 24\"/><path d=\"M-40 288 H440\" stroke-dasharray=\"24 16\"/></g><path d=\"M0 298 Q200 284 400 300 V400 H0Z\" fill=\"#acd07c\"/><path d=\"M0 366 Q200 344 400 370 V400 H0Z\" fill=\"#95bf64\"/><!-- Harshavardhana's elephant, far bank, turning for home --><g transform=\"translate(250 196)\"><g class=\"a-puff\"><circle cx=\"-2\" cy=\"56\" r=\"7\" fill=\"#efe4bd\"/></g><g class=\"a-puff p2\"><circle cx=\"-12\" cy=\"50\" r=\"5\" fill=\"#efe4bd\"/></g><g class=\"a-trot\">{{ELEPHANT}}<path d=\"M20 18 h36 v16 q-18 8 -36 0z\" fill=\"#d94a3d\"/><path d=\"M20 32 q18 8 36 0\" stroke=\"#f2b632\" stroke-width=\"3\" fill=\"none\"/><path d=\"M30 19 q9 -16 18 0z\" fill=\"#f3e3b5\"/>{{HARSHA}}</g><g class=\"a-tumble\"><path d=\"M14 -24 q14 -14 28 0z\" fill=\"#fff6dc\" stroke=\"#f2b632\" stroke-width=\"2\"/><path d=\"M28 -24 v14\" stroke=\"#7a5232\" stroke-width=\"2\"/></g></g><!-- Chalukya boar banner --><rect x=\"41\" y=\"118\" width=\"5\" height=\"282\" fill=\"#7a5232\"/><circle cx=\"43.5\" cy=\"116\" r=\"6\" fill=\"#f2b632\"/><g class=\"a-flag\"><path d=\"M46 126 h72 l-12 22 l12 22 h-72z\" fill=\"#f2b632\"/><path d=\"M56 156 q4 -12 20 -12 q10 0 16 6 l7 -2 l-2 6 q2 6 -4 8 h-4 v6 h-4 v-6 h-14 v6 h-4 v-6 q-8 -2 -11 -6z\" fill=\"#8a3a2b\"/></g>{{KING}}", "pulakeshiSmall": "<rect width=\"200\" height=\"200\" fill=\"#efe4d0\"/><rect y=\"156\" width=\"200\" height=\"44\" fill=\"#d8c7a6\"/><rect x=\"46\" y=\"36\" width=\"96\" height=\"124\" rx=\"10\" fill=\"#b8ab95\"/><rect x=\"52\" y=\"42\" width=\"84\" height=\"112\" rx=\"7\" fill=\"#cdc1ac\"/><g stroke=\"#6e6252\" stroke-width=\"4\" stroke-linecap=\"round\" fill=\"none\"><path class=\"a-draw\" style=\"--i:0\" pathLength=\"1\" d=\"M62 60 h64\"/><path class=\"a-draw\" style=\"--i:1\" pathLength=\"1\" d=\"M62 76 h56\"/><path class=\"a-draw\" style=\"--i:2\" pathLength=\"1\" d=\"M62 92 h64\"/><path class=\"a-draw\" style=\"--i:3\" pathLength=\"1\" d=\"M62 108 h48\"/><path class=\"a-draw\" style=\"--i:4\" pathLength=\"1\" d=\"M62 124 h60\"/></g><path d=\"M124 132 l18 -20 l5 5 l-18 20z\" fill=\"#6b7280\"/><circle cx=\"146\" cy=\"116\" r=\"8\" fill=\"#c68a5e\"/><g class=\"a-spark\"><path d=\"M120 136 l-8 -2 M122 142 l-8 6 M126 144 l0 8\" stroke=\"#f5b301\" stroke-width=\"2.5\" stroke-linecap=\"round\"/></g><g class=\"a-tap\" style=\"transform-origin: 100% 50%\"><rect x=\"146\" y=\"88\" width=\"18\" height=\"12\" rx=\"3\" fill=\"#6b7280\"/><rect x=\"162\" y=\"91\" width=\"28\" height=\"6\" rx=\"3\" fill=\"#8a5a3b\"/></g><text x=\"96\" y=\"182\" text-anchor=\"middle\" font-family=\"Inter, sans-serif\" font-size=\"13\" font-weight=\"700\" fill=\"#8a7a62\">AIHOLE · 634</text>", "basavaBig": "<rect width=\"400\" height=\"400\" fill=\"#f8ead5\"/><path d=\"M193 76 q7 -28 14 0z\" fill=\"#f2b632\"/><path d=\"M74 112 h252 l-26 -38 h-200z\" fill=\"#b07a4c\"/><path d=\"M30 150 h340 l-34 -40 h-272z\" fill=\"#8f603b\"/><rect x=\"30\" y=\"148\" width=\"340\" height=\"10\" fill=\"#7a5232\"/><g fill=\"#d6b88b\"><rect x=\"58\" y=\"158\" width=\"20\" height=\"150\"/><rect x=\"128\" y=\"158\" width=\"20\" height=\"150\"/><rect x=\"252\" y=\"158\" width=\"20\" height=\"150\"/><rect x=\"322\" y=\"158\" width=\"20\" height=\"150\"/></g><g fill=\"#c39e6c\"><rect x=\"52\" y=\"158\" width=\"32\" height=\"10\" rx=\"2\"/><rect x=\"122\" y=\"158\" width=\"32\" height=\"10\" rx=\"2\"/><rect x=\"246\" y=\"158\" width=\"32\" height=\"10\" rx=\"2\"/><rect x=\"316\" y=\"158\" width=\"32\" height=\"10\" rx=\"2\"/><rect x=\"52\" y=\"296\" width=\"32\" height=\"12\" rx=\"2\"/><rect x=\"122\" y=\"296\" width=\"32\" height=\"12\" rx=\"2\"/><rect x=\"246\" y=\"296\" width=\"32\" height=\"12\" rx=\"2\"/><rect x=\"316\" y=\"296\" width=\"32\" height=\"12\" rx=\"2\"/></g><rect y=\"306\" width=\"400\" height=\"94\" fill=\"#d9b98c\"/><rect y=\"306\" width=\"400\" height=\"8\" fill=\"#c9a676\"/><g class=\"a-hang\"><path d=\"M200 158 L190 190 M200 158 L210 190\" stroke=\"#7a5232\" stroke-width=\"1.6\"/><path d=\"M184 190 h32 l-6 10 h-20z\" fill=\"#f2b632\"/><path class=\"a-flicker\" d=\"M200 174 q-6 8 0 15 q6 -7 0 -15z\" fill=\"#ff8a3d\"/></g><!-- a vachanakara --><ellipse cx=\"100\" cy=\"332\" rx=\"36\" ry=\"11\" fill=\"#d99a4e\"/><path d=\"M72 332 q4 -48 28 -52 q24 4 28 52z\" fill=\"#e8b468\"/><circle cx=\"100\" cy=\"306\" r=\"6.5\" fill=\"#c08458\"/><g class=\"a-nod\" style=\"animation-delay:-1.2s\"><path d=\"M76 258 a24 24 0 0 1 48 0 v44 q-24 8 -48 0z\" fill=\"#2b2118\"/><circle cx=\"100\" cy=\"258\" r=\"23\" fill=\"#c08458\"/><path d=\"M77 258 a23 23 0 0 1 46 0 q-10 -12 -23 -12 q-13 0 -23 12z\" fill=\"#2b2118\"/><circle cx=\"100\" cy=\"252\" r=\"2.4\" fill=\"#d94a3d\"/><g class=\"a-blink\"><circle cx=\"92\" cy=\"261\" r=\"2.6\" fill=\"#2b2118\"/><circle cx=\"108\" cy=\"261\" r=\"2.6\" fill=\"#2b2118\"/></g><path d=\"M95 270 q5 4 10 0\" stroke=\"#7a3b2a\" stroke-width=\"2\" fill=\"none\" stroke-linecap=\"round\"/></g><!-- Basavanna --><ellipse cx=\"200\" cy=\"332\" rx=\"50\" ry=\"13\" fill=\"#efe6d4\"/><path d=\"M162 332 q6 -60 38 -64 q32 4 38 64z\" fill=\"#fbf7ee\"/><path d=\"M176 278 q24 22 48 0 l5 10 q-29 26 -58 0z\" fill=\"#f08a24\"/><path d=\"M188 276 q12 22 24 0\" stroke=\"#7a3b2a\" stroke-width=\"3.2\" stroke-dasharray=\"0.1 5\" stroke-linecap=\"round\" fill=\"none\"/><ellipse cx=\"200\" cy=\"300\" rx=\"4\" ry=\"5\" fill=\"#3a3a48\"/><path d=\"M190 322 q10 -16 20 0 q-10 6 -20 0z\" fill=\"#b9825a\"/><g class=\"a-nod\"><rect x=\"192\" y=\"256\" width=\"16\" height=\"16\" fill=\"#a8734d\"/><circle cx=\"200\" cy=\"236\" r=\"30\" fill=\"#b9825a\"/><circle cx=\"200\" cy=\"202\" r=\"11\" fill=\"#2b2118\"/><path d=\"M170 236 a30 30 0 0 1 60 0 q-12 -16 -30 -16 q-18 0 -30 16z\" fill=\"#2b2118\"/><path d=\"M176 246 q24 34 48 0 q-2 22 -24 26 q-22 -4 -24 -26z\" fill=\"#2b2118\"/><path d=\"M189 226 h22 M189 230.5 h22 M189 235 h22\" stroke=\"#fff\" stroke-width=\"2\" stroke-linecap=\"round\"/><circle cx=\"200\" cy=\"230.5\" r=\"2\" fill=\"#d94a3d\"/><g class=\"a-blink\"><circle cx=\"190\" cy=\"243\" r=\"3\" fill=\"#2b2118\"/><circle cx=\"210\" cy=\"243\" r=\"3\" fill=\"#2b2118\"/></g><path d=\"M194 257 q6 4 12 0\" stroke=\"#e8c4a0\" stroke-width=\"2\" fill=\"none\" stroke-linecap=\"round\"/></g><!-- a farmer speaking up --><ellipse cx=\"300\" cy=\"332\" rx=\"36\" ry=\"11\" fill=\"#d7d0bf\"/><path d=\"M272 332 q4 -48 28 -52 q24 4 28 52z\" fill=\"#5f8fc9\"/><circle cx=\"288\" cy=\"306\" r=\"6.5\" fill=\"#a86b45\"/><g class=\"a-wave\" style=\"transform-origin: 0% 100%\"><path d=\"M318 298 q14 -20 12 -50\" stroke=\"#5f8fc9\" stroke-width=\"11\" stroke-linecap=\"round\" fill=\"none\"/><circle cx=\"330\" cy=\"244\" r=\"7.5\" fill=\"#a86b45\"/></g><g class=\"a-nod\" style=\"animation-delay:-2s\"><circle cx=\"300\" cy=\"258\" r=\"23\" fill=\"#a86b45\"/><path d=\"M276 256 q0 -28 24 -30 q24 2 24 30 q-24 -12 -48 0z\" fill=\"#ece5d3\"/><path d=\"M282 246 q18 -10 36 0\" stroke=\"#d6cdb6\" stroke-width=\"2.5\" fill=\"none\"/><g class=\"a-blink\"><circle cx=\"292\" cy=\"262\" r=\"2.6\" fill=\"#2b2118\"/><circle cx=\"308\" cy=\"262\" r=\"2.6\" fill=\"#2b2118\"/></g><path d=\"M290 269 q10 -5 20 0\" stroke=\"#2b2118\" stroke-width=\"3.5\" fill=\"none\" stroke-linecap=\"round\"/><ellipse class=\"a-talk\" cx=\"300\" cy=\"275\" rx=\"3.2\" ry=\"2.6\" fill=\"#6b2d22\"/></g>", "basavaSmall": "<rect width=\"200\" height=\"200\" fill=\"#e6ecfb\"/><g fill=\"#f5b301\"><path class=\"a-twinkle\" d=\"M40 50 l3 8 l8 3 l-8 3 l-3 8 l-3 -8 l-8 -3 l8 -3z\"/><path class=\"a-twinkle\" style=\"animation-delay:-.7s\" d=\"M160 118 l2.5 6 l6 2.5 l-6 2.5 l-2.5 6 l-2.5 -6 l-6 -2.5 l6 -2.5z\"/><path class=\"a-twinkle\" style=\"animation-delay:-1.4s\" d=\"M48 112 l2 5 l5 2 l-5 2 l-2 5 l-2 -5 l-5 -2 l5 -2z\"/></g><g class=\"a-lift\"><rect x=\"78\" y=\"44\" width=\"28\" height=\"96\" rx=\"14\" fill=\"#c68a5e\"/><rect x=\"83\" y=\"48\" width=\"18\" height=\"22\" rx=\"8\" fill=\"#e8b896\"/><path d=\"M92 50 v30\" stroke=\"#4b2a7a\" stroke-width=\"5\" stroke-linecap=\"round\"/><path d=\"M62 210 v-70 q0 -14 14 -14 h56 q14 0 14 14 v70z\" fill=\"#c68a5e\"/><path d=\"M106 130 q24 -2 32 14 M108 150 h30 M108 168 h30\" stroke=\"#b07650\" stroke-width=\"3\" fill=\"none\" stroke-linecap=\"round\"/><path d=\"M66 156 q-4 -22 18 -24\" stroke=\"#b07650\" stroke-width=\"3\" fill=\"none\" stroke-linecap=\"round\"/></g><g class=\"a-bob\"><circle cx=\"150\" cy=\"66\" r=\"18\" fill=\"#0f8a5f\"/><path d=\"M142 66 l6 6 l11 -12\" stroke=\"#fff\" stroke-width=\"4\" fill=\"none\" stroke-linecap=\"round\" stroke-linejoin=\"round\"/></g>", "hampiBig": "<rect width=\"400\" height=\"400\" fill=\"#fde3c4\"/><rect y=\"150\" width=\"400\" height=\"140\" fill=\"#fbd2a4\"/><circle class=\"a-pulse\" cx=\"124\" cy=\"118\" r=\"30\" fill=\"#ffb547\"/><g class=\"a-birds\" stroke=\"#7a4a2a\" stroke-width=\"2.5\" fill=\"none\" stroke-linecap=\"round\"><path class=\"a-flap\" d=\"M260 80 q6 -6 12 0 q6 -6 12 0\"/><path class=\"a-flap\" style=\"animation-delay:-.2s\" d=\"M292 98 q5 -5 10 0 q5 -5 10 0\"/><path class=\"a-flap\" style=\"animation-delay:-.1s\" d=\"M240 104 q4 -4 8 0 q4 -4 8 0\"/></g><path d=\"M0 250 q30 -70 80 -60 q20 -40 60 -20 q30 -30 70 0 q40 -20 70 10 q40 -30 120 20 V300 H0z\" fill=\"#d7a06d\"/><ellipse cx=\"60\" cy=\"244\" rx=\"44\" ry=\"28\" fill=\"#c58a57\"/><ellipse cx=\"44\" cy=\"208\" rx=\"22\" ry=\"18\" fill=\"#d29864\"/><ellipse cx=\"338\" cy=\"238\" rx=\"42\" ry=\"30\" fill=\"#c58a57\"/><ellipse cx=\"356\" cy=\"198\" rx=\"24\" ry=\"20\" fill=\"#d29864\"/><ellipse cx=\"334\" cy=\"170\" rx=\"13\" ry=\"11\" fill=\"#c58a57\"/><rect y=\"288\" width=\"400\" height=\"112\" fill=\"#e9c58f\"/><path d=\"M0 340 Q200 324 400 344 V400 H0Z\" fill=\"#dfb57b\"/><!-- the stone chariot --><rect x=\"186\" y=\"262\" width=\"128\" height=\"40\" rx=\"4\" fill=\"#b9a58a\"/><path d=\"M194 272 h112 M194 282 h112 M194 292 h112\" stroke=\"#a6927a\" stroke-width=\"2\"/><rect x=\"204\" y=\"214\" width=\"92\" height=\"50\" fill=\"#c7b398\"/><path d=\"M238 264 v-30 q12 -14 24 0 v30z\" fill=\"#7d6a52\"/><path d=\"M196 214 h108 l-10 -14 h-88z\" fill=\"#b9a58a\"/><path d=\"M210 200 h80 l-10 -16 h-60z\" fill=\"#c7b398\"/><path d=\"M224 184 h52 l-10 -16 h-32z\" fill=\"#b9a58a\"/><path d=\"M244 168 q6 -20 12 0z\" fill=\"#f2b632\"/><g class=\"a-spin\"><circle cx=\"214\" cy=\"300\" r=\"22\" fill=\"#a99377\" stroke=\"#7d6a52\" stroke-width=\"4\"/><path d=\"M214 280 v40 M194 300 h40 M200 286 l28 28 M228 286 l-28 28\" stroke=\"#7d6a52\" stroke-width=\"3\"/><circle cx=\"214\" cy=\"300\" r=\"6\" fill=\"#7d6a52\"/></g><g class=\"a-spin\"><circle cx=\"286\" cy=\"300\" r=\"22\" fill=\"#a99377\" stroke=\"#7d6a52\" stroke-width=\"4\"/><path d=\"M286 280 v40 M266 300 h40 M272 286 l28 28 M300 286 l-28 28\" stroke=\"#7d6a52\" stroke-width=\"3\"/><circle cx=\"286\" cy=\"300\" r=\"6\" fill=\"#7d6a52\"/></g>{{KING}}", "hampiSmall": "<rect width=\"200\" height=\"200\" fill=\"#d5e9f4\"/><ellipse cx=\"34\" cy=\"98\" rx=\"52\" ry=\"20\" fill=\"#c58a57\"/><ellipse cx=\"172\" cy=\"100\" rx=\"42\" ry=\"15\" fill=\"#d29864\"/><rect y=\"100\" width=\"200\" height=\"100\" fill=\"#7db7de\"/><ellipse class=\"a-ripple\" cx=\"100\" cy=\"150\" rx=\"60\" ry=\"14\" fill=\"none\" stroke=\"#fff\" stroke-width=\"2\"/><ellipse class=\"a-ripple r2\" cx=\"100\" cy=\"150\" rx=\"60\" ry=\"14\" fill=\"none\" stroke=\"#fff\" stroke-width=\"2\"/><g class=\"a-rock\"><g class=\"a-paddle\" style=\"transform-origin: 0% 0%\"><path d=\"M112 118 L146 166\" stroke=\"#8a5a3b\" stroke-width=\"4\" stroke-linecap=\"round\"/><ellipse cx=\"146\" cy=\"168\" rx=\"5\" ry=\"10\" fill=\"#8a5a3b\" transform=\"rotate(-35 146 168)\"/></g><path d=\"M90 140 v-24 q10 -6 20 0 v24z\" fill=\"#f6efe0\"/><circle cx=\"100\" cy=\"100\" r=\"12\" fill=\"#a86b45\"/><path d=\"M88 98 q12 -16 24 0 q-12 -5 -24 0z\" fill=\"#d94a3d\"/><circle cx=\"105\" cy=\"101\" r=\"1.8\" fill=\"#2b2118\"/><path d=\"M108 120 l6 -2\" stroke=\"#a86b45\" stroke-width=\"6\" stroke-linecap=\"round\"/><ellipse cx=\"100\" cy=\"140\" rx=\"48\" ry=\"13\" fill=\"#8a5a3b\"/><path d=\"M52 140 q48 36 96 0z\" fill=\"#6f4529\"/><path d=\"M58 141 q42 30 84 0\" stroke=\"#9c6b43\" stroke-width=\"2\" stroke-dasharray=\"4 4\" fill=\"none\"/></g>", "kitturBig": "<rect width=\"400\" height=\"400\" fill=\"#e3f1ec\"/><g class=\"a-drift\" fill=\"#fff\"><circle cx=\"250\" cy=\"82\" r=\"13\"/><circle cx=\"267\" cy=\"74\" r=\"17\"/><circle cx=\"286\" cy=\"83\" r=\"11\"/><rect x=\"236\" y=\"82\" width=\"62\" height=\"12\" rx=\"6\"/></g><path d=\"M0 236 q80 -40 160 -14 q90 -36 240 6 V300 H0z\" fill=\"#bfdcae\"/><rect y=\"228\" width=\"400\" height=\"74\" fill=\"#d6b48a\"/><path d=\"M0 222 H400\" stroke=\"#d6b48a\" stroke-width=\"14\" stroke-dasharray=\"18 12\"/><path d=\"M250 302 v-36 q15 -18 30 0 v36z\" fill=\"#8f6b46\"/><rect x=\"30\" y=\"160\" width=\"60\" height=\"142\" fill=\"#caa478\"/><path d=\"M30 154 H90\" stroke=\"#caa478\" stroke-width=\"12\" stroke-dasharray=\"12 8\"/><rect x=\"318\" y=\"176\" width=\"56\" height=\"126\" fill=\"#caa478\"/><path d=\"M318 170 H374\" stroke=\"#caa478\" stroke-width=\"12\" stroke-dasharray=\"12 8\"/><rect x=\"58\" y=\"104\" width=\"4\" height=\"52\" fill=\"#7a5232\"/><path class=\"a-flag\" d=\"M62 106 h46 l-8 14 l8 14 h-46z\" fill=\"#f08a24\"/><rect y=\"300\" width=\"400\" height=\"100\" fill=\"#a9cc77\"/><path d=\"M0 362 Q200 342 400 366 V400 H0Z\" fill=\"#95bf64\"/><!-- the Company soldier, losing his hat --><g class=\"a-fly\"><rect x=\"318\" y=\"226\" width=\"18\" height=\"20\" rx=\"2\" fill=\"#23232f\"/><rect x=\"314\" y=\"244\" width=\"26\" height=\"5\" rx=\"2\" fill=\"#23232f\"/><path d=\"M327 226 q-4 -12 4 -16 q2 8 -1 16z\" fill=\"#d94a3d\"/></g>{{SOLDIER}}<!-- Rani Chennamma on horseback --><g class=\"a-gallop\">{{HORSE}}<path d=\"M136 274 h64 l-6 36 h-52z\" fill=\"#d94a3d\"/><path d=\"M140 306 h50\" stroke=\"#f2b632\" stroke-width=\"4\"/>{{RIDER}}</g>", "kitturSmall": "<rect width=\"200\" height=\"200\" fill=\"#fdebd2\"/><g class=\"a-birds slow\" stroke=\"#7a4a2a\" stroke-width=\"2\" fill=\"none\" stroke-linecap=\"round\"><path class=\"a-flap\" d=\"M150 40 q5 -5 10 0 q5 -5 10 0\"/><path class=\"a-flap\" style=\"animation-delay:-.2s\" d=\"M170 58 q4 -4 8 0 q4 -4 8 0\"/></g><rect y=\"150\" width=\"200\" height=\"50\" fill=\"#a9cc77\"/><rect x=\"60\" y=\"78\" width=\"80\" height=\"80\" fill=\"#caa478\"/><path d=\"M60 72 H140\" stroke=\"#caa478\" stroke-width=\"14\" stroke-dasharray=\"12 8\"/><path d=\"M88 158 v-28 q12 -14 24 0 v28z\" fill=\"#8f6b46\"/><rect x=\"70\" y=\"92\" width=\"10\" height=\"14\" rx=\"5\" fill=\"#8f6b46\"/><rect x=\"120\" y=\"92\" width=\"10\" height=\"14\" rx=\"5\" fill=\"#8f6b46\"/><rect x=\"98\" y=\"20\" width=\"4\" height=\"46\" fill=\"#7a5232\"/><path class=\"a-flag\" d=\"M102 22 h44 l-8 13 l8 13 h-44z\" fill=\"#f08a24\"/><text x=\"100\" y=\"186\" text-anchor=\"middle\" font-family=\"Inter, sans-serif\" font-size=\"14\" font-weight=\"800\" fill=\"#5c7a3c\">KITTUR · 1824</text>"};

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
      big: () => LEGACY.pulakeshiBig.replace('{{ELEPHANT}}', elephant({ x: 38, y: 60, s: 0.4, walk: true }))
        .replace('{{HARSHA}}', at(39, 5, 0.26, head({ skin: P.skin.light, wear: 'crown', stache: 'thin' })))
        // Pulakeshi II after the Badami statue: tall kirita, clean-shaven.
        .replace('{{KING}}', figure({ x: 140, y: 392, s: 1.02, attire: 'king', wear: 'kirita', lower: '#f6efe0', sash: P.red, skin: P.skin.brown, brows: 'fierce', mouth: 'open', armR: 'up', holdR: 'sword', animR: 'a-swing', armL: 'out', holdL: 'shield', move: 'a-bob' })),
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
        ${figure({ x: 336, y: 318, s: 0.6, attire: 'monk', cloth: P.saffron, hair: 'shaven', hairColor: '#4a4540', beard: 'long', stache: 'full', face: 'long', mark: 'vibhuti', armR: 'down', holdR: 'staff', armL: 'raise', animL: 'a-wave slow2', skin: P.skin.brown })}
        ${hound(150, 384, 0.9, 0)}${hound(214, 392, 0.9, -0.2)}${hare(290, 388, 1.1)}`,
      small: () => `${rect(0, 0, 200, 200, '#fdeccf')}<circle cx="44" cy="54" r="16" fill="#ffb547"/><path d="M160 40 a16 16 0 1 0 6 28 a12 12 0 1 1 -6 -28z" fill="#e6dcc4"/>
        ${at(92, 146, 1.3, boar())}
        <path d="M40 150 h112 l8 4 l-8 4 h-112z" fill="#cfd6de" stroke="${P.steel}"/>${rect(30, 148, 12, 12, P.gold, 2)}
        <text x="100" y="188" text-anchor="middle" font-family="Inter, sans-serif" font-size="13" font-weight="800" fill="#8a3a2b">VARAHA</text>`,
    },
    {
      era: ['Vijayanagara', 'ವಿಜಯನಗರ'],
      title: ['Krishnadevaraya\'s Vijayanagara', 'ಶ್ರೀಕೃಷ್ಣದೇವರಾಯನ ವಿಜಯನಗರ'],
      sub: ['Hampi at its height, early 1500s', 'ವೈಭವದ ಉತ್ತುಂಗದಲ್ಲಿ ಹಂಪಿ, 16ನೇ ಶತಮಾನ'],
      bubbles: [['Welcome to Vijayanagara!', 'ವಿಜಯನಗರಕ್ಕೆ ಸ್ವಾಗತ!', 'left:-6%;top:28%'], ['Diamonds sold by the heap!', 'ವಜ್ರಗಳು ರಾಶಿ ರಾಶಿ!', 'right:-2%;top:14%', 1]],
      // Krishnadevaraya after his Tirumala bronze: tall kullayi, clean-shaven.
      big: () => LEGACY.hampiBig.replace('{{KING}}', figure({ x: 110, y: 386, s: 0.86, attire: 'robe', cloth: P.cream, sash: P.red, wear: 'kullayi', face: 'round', skin: P.skin.wheat, mouth: 'talk', armR: 'point', animR: 'a-point', armL: 'down', move: 'a-bob' })),
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
        ${figure({ x: 120, y: 398, s: 1, attire: 'commoner', shawl: '#2b2b30', skin: P.skin.deep, face: 'lean', mark: 'namam', beard: true, stache: 'full', eyes: 'closed', mouth: 'talk', armL: 'down', holdL: 'tambura', armR: 'raise', animR: 'a-wave slow2', nod: true })}`,
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
        ${figure({ x: 140, y: 398, s: 1, attire: 'saree', cloth: '#f4ead2', blouse: P.red, border: P.red, hair: 'bun', mark: 'bindi', nosering: true, brows: 'fierce', armR: 'fwd', holdR: 'bow', armL: 'chest', move: 'a-bob', skin: P.skin.brown })}`,
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
      era: ['Kingdom of Mysore', 'ಮೈಸೂರು ಸಂಸ್ಥಾನ'],
      title: ['Tipu Sultan\'s rockets', 'ಟಿಪ್ಪು ಸುಲ್ತಾನನ ರಾಕೆಟ್‌ಗಳು'],
      sub: ['Iron-cased Mysorean rockets help rout the Company at Pollilur, 1780', 'ಕಬ್ಬಿಣದ ಕವಚದ ಮೈಸೂರು ರಾಕೆಟ್‌ಗಳು, ಪೊಲ್ಲಿಲೂರು ಕದನ, 1780'],
      bubbles: [['Fire!', 'ಹಾರಿಸಿ!', 'left:4%;top:34%'], ['Rockets! Run!', 'ರಾಕೆಟ್! ಓಡಿ!', 'right:-4%;top:50%', 1]],
      big: () => `${rect(0, 0, 400, 400, '#fde3c4')}${sun(250, 70, 22, '#ffb35a')}
        <path d="M0 230 q100 -40 200 -14 q110 -30 200 4 V300 H0z" fill="#e9c79a"/>
        ${banner(30, 108, 210, '#f2b632', 'bubri', '#3a2418')}
        ${ground(300, '#d9b98a', '#cfab78')}
        <g class="a-puff"><circle cx="232" cy="300" r="12" fill="#e9e2d4"/></g><g class="a-puff p2"><circle cx="214" cy="304" r="9" fill="#e9e2d4"/></g>
        <path d="M222 332 l12 -30 l12 30 M214 312 L268 290" stroke="#7a5232" stroke-width="4" fill="none" stroke-linecap="round"/>
        ${rocket(252, 288, -16, 96, 0)}${rocket(236, 262, -8, 104, -0.55)}${rocket(258, 232, 4, 84, -1.1)}
        <g class="a-burst"><circle cx="312" cy="288" r="26" fill="#ffb02e" opacity=".8"/><circle cx="312" cy="288" r="14" fill="#fff1a8"/></g>
        <path d="M284 318 h52 v-22 h-52z" fill="#7a5232"/><circle cx="296" cy="322" r="9" fill="#4a3324"/><circle cx="326" cy="322" r="9" fill="#4a3324"/>
        ${figure({ x: 338, y: 396, s: 0.5, attire: 'euro', cloth: '#c8352b', wear: 'tricorn', skin: P.skin.euro, hairColor: '#8a6a4a', brows: 'up', mouth: 'o', armR: 'raise', armL: 'raise', animR: 'a-wave', move: 'a-run' })}
        ${figure({ x: 186, y: 392, s: 0.66, attire: 'soldier', cloth: '#c9762e', wear: 'turban', wearColor: '#b5462e', stache: 'handlebar', skin: P.skin.deep, brows: 'fierce', mouth: 'open', armR: 'fwd', holdR: 'torch', armL: 'hip' })}
        ${figure({ x: 90, y: 398, s: 1, attire: 'jama', cloth: '#4f7a3a', stripe: false, sash: P.gold, wear: 'sultan', wearColor: '#3f6b34', stache: 'thin', face: 'round', skin: P.skin.light, brows: 'fierce', mouth: 'open', armR: 'point', holdR: 'sword', animR: 'a-point', armL: 'hip' })}`,
      small: () => `${rect(0, 0, 200, 200, '#f2b632')}
        <g stroke="#3a2418" stroke-width="5" fill="none" stroke-linecap="round" opacity=".55">${Array.from({ length: 16 }, (_, i) => `<path d="M${(i % 4) * 56 + 6} ${Math.floor(i / 4) * 50 + 4} q8 10 0 20 q-8 10 0 20"/>`).join('')}</g>
        ${at(104, 96, 2.2, `<g transform="rotate(-28)">${rocketBody()}</g>`)}
        ${rect(0, 160, 200, 40, '#3a2418')}<text x="100" y="185" text-anchor="middle" font-family="Inter, sans-serif" font-size="12" font-weight="800" fill="#f2b632">MYSORE ROCKET</text>`,
    },
    {
      era: ['Kittur Desais', 'ಕಿತ್ತೂರು ದೇಸಾಯಿಗಳು'],
      title: ['Rani Chennamma of Kittur', 'ಕಿತ್ತೂರು ರಾಣಿ ಚೆನ್ನಮ್ಮ'],
      sub: ['Defies the East India Company, 1824', 'ಈಸ್ಟ್ ಇಂಡಿಯಾ ಕಂಪನಿಗೆ ಸವಾಲು, 1824'],
      bubbles: [['Kittur is ours!', 'ಕಿತ್ತೂರು ನಮ್ಮದು!', 'left:14%;top:12%'], ['Retreat, retreat!', 'ಹಿಂದೆ ಸರಿಯಿರಿ!', 'right:-3%;top:44%', 1]],
      big: () => LEGACY.kitturBig.replace('{{HORSE}}', horse({ x: 172, y: 368 }))
        .replace('{{SOLDIER}}', `<g transform="rotate(-22 330 384)">${figure({ x: 330, y: 384, s: 0.48, attire: 'euro', cloth: '#c8352b', skin: P.skin.euro, hairColor: '#7a5a3a', eyes: 'dizzy', mouth: 'o', brows: 'up', armR: 'raise', armL: 'raise', move: 'a-wobble' })}</g>`)
        // Chennamma as in her Kittur statue: saree drawn over the head, sword raised.
        .replace('{{RIDER}}', `<path d="M182 290 q9 22 3 42" stroke="#2e8b57" stroke-width="13" stroke-linecap="round" fill="none"/><ellipse cx="188" cy="334" rx="9" ry="4.5" fill="#6b4128"/>${figure({ x: 168, y: 290, s: 0.7, seated: true, attire: 'saree', cloth: '#2e8b57', legs: '#2e8b57', blouse: P.red, border: P.red, hair: 'veil', mark: 'bindi', nosering: true, skin: P.skin.brown, brows: 'fierce', mouth: 'open', armR: 'up', holdR: 'sword', animR: 'a-swing', armL: 'fwd' })}`),
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
        ${figure({ x: 76, y: 398, s: 0.98, attire: 'coat', cloth: '#efe6d2', sash: '#efe6d2', wear: 'peta', wearColor: '#e9dcc0', face: 'lean', stache: 'handlebar', mark: 'tilak', skin: P.skin.light, armR: 'point', animR: 'a-point', armL: 'hip' })}`,
      small: () => `${rect(0, 0, 200, 200, '#d6ece4')}${boulder(30, 70, 50, 40, '#8f7f6a')}${boulder(170, 70, 50, 40, '#8f7f6a')}
        ${rect(60, 30, 80, 130, '#9fd3ea')}<g class="a-fall" stroke="#fff" stroke-width="3" stroke-linecap="round">${[70, 86, 100, 114, 130].map((x) => `<path d="M${x} 20 V170" stroke-dasharray="12 10"/>`).join('')}</g>
        ${rect(0, 150, 200, 50, '#5aa6c8')}<g class="a-puff"><circle cx="80" cy="156" r="12" fill="#fff" opacity=".8"/></g><g class="a-puff p2"><circle cx="120" cy="158" r="10" fill="#fff" opacity=".8"/></g>
        <path d="M176 120 l-10 40 h20z M166 132 h20" stroke="#5d6470" stroke-width="2.5" fill="none"/><path d="M170 104 l-4 10 h6 l-4 10" stroke="#ffd34d" stroke-width="2.5" fill="none" stroke-linecap="round"/>
        <text x="100" y="190" text-anchor="middle" font-family="Inter, sans-serif" font-size="12" font-weight="800" fill="#fff">1902</text>`,
    },
    {
      era: ['Kingdom of Mysore', 'ಮೈಸೂರು ಸಂಸ್ಥಾನ'],
      title: ['Visvesvaraya dams the Kaveri', 'ಕಾವೇರಿಗೆ ವಿಶ್ವೇಶ್ವರಯ್ಯನವರ ಅಣೆಕಟ್ಟು'],
      sub: ['Krishna Raja Sagara, built to Sir M. Visvesvaraya\'s design, opens in 1932', 'ಸರ್ ಎಂ. ವಿಶ್ವೇಶ್ವರಯ್ಯನವರ ವಿನ್ಯಾಸದ ಕೃಷ್ಣರಾಜಸಾಗರ, 1932'],
      bubbles: [['Every drop to the fields!', 'ಪ್ರತಿ ಹನಿಯೂ ಹೊಲಕ್ಕೆ!', 'left:-4%;top:26%'], ['Water at last!', 'ಕೊನೆಗೂ ನೀರು!', 'right:0%;top:57%', 1]],
      big: () => `${rect(0, 0, 400, 400, '#e4f1f7')}${cloud(60, 60, 0.8)}${cloud(280, 90, 0.6, 1)}
        <path d="M0 160 q90 -40 190 -10 q110 -40 210 0 V200 H0z" fill="#b9d39a"/>${rect(100, 146, 300, 28, '#6fa9d6')}
        <path d="M100 172 H400 V256 H100Z" fill="#cdbf9f"/>${rect(100, 166, 300, 8, '#b7a886')}
        ${[118, 150, 182, 214, 246, 278, 310, 342, 374].map((x) => `<path d="M${x} 256 v-36 q8 -10 16 0 v36z" fill="#857860"/>`).join('')}
        <g class="a-fall" stroke="#fff" stroke-width="3" stroke-linecap="round" opacity=".85">${[126, 158, 190, 222, 254, 286, 318, 350, 382].map((x) => `<path d="M${x} 232 V280" stroke-dasharray="9 7"/>`).join('')}</g>
        ${water(256, 46)}${ground(300, '#9fca6e', '#8dbb5c')}
        <g fill="#5f9e4f">${[[240, 340], [270, 352], [300, 338], [372, 346], [390, 372], [250, 380]].map(([x, y]) => `<path d="M${x} ${y} l-6 -14 l6 8 l2 -16 l3 16 l6 -10 l-4 16z"/>`).join('')}</g>
        ${figure({ x: 306, y: 398, s: 0.62, attire: 'commoner', skin: P.skin.deep, wear: 'turban', wearColor: '#f4efe2', stache: 'thin', mouth: 'grin', armR: 'raise', animR: 'a-wave', armL: 'down', flip: true })}
        ${figure({ x: 112, y: 398, s: 1, attire: 'coat', cloth: '#2f3342', sash: '#2f3342', wear: 'peta', wearColor: '#f1efe9', face: 'long', age: 'old', stache: 'full', skin: P.skin.wheat, mouth: 'talk', armR: 'point', animR: 'a-point', armL: 'fwd', holdL: 'scroll' })}`,
      small: () => `${rect(0, 0, 200, 200, '#e8eef6')}
        <g class="a-spin" style="transform-origin:100px 88px"><g fill="#5d6b82">${Array.from({ length: 10 }, (_, i) => `<rect x="94" y="34" width="12" height="18" rx="2" transform="rotate(${i * 36} 100 88)"/>`).join('')}</g><circle cx="100" cy="88" r="40" fill="#5d6b82"/><circle cx="100" cy="88" r="16" fill="#e8eef6"/></g>
        <text x="100" y="160" text-anchor="middle" font-family="Inter, sans-serif" font-size="12" font-weight="800" fill="#3f4b60">ENGINEERS' DAY</text>
        <text x="100" y="178" text-anchor="middle" font-family="Inter, sans-serif" font-size="11" font-weight="700" fill="#6b7890">15 SEPT</text>`,
    },
    {
      era: ['Mysore State', 'ಮೈಸೂರು ರಾಜ್ಯ'],
      title: ['Vidhana Soudha rises in Bengaluru', 'ಬೆಂಗಳೂರಿನಲ್ಲಿ ವಿಧಾನಸೌಧ'],
      sub: ['Chief Minister Kengal Hanumanthaiah builds it in granite, in Indian style, 1952–56', 'ಮುಖ್ಯಮಂತ್ರಿ ಕೆಂಗಲ್ ಹನುಮಂತಯ್ಯನವರು ಕಟ್ಟಿಸಿದ ಭಾರತೀಯ ಶೈಲಿಯ ಕಲ್ಲಿನ ಸೌಧ, 1952–56'],
      bubbles: [['In our own Indian style!', 'ನಮ್ಮದೇ ಭಾರತೀಯ ಶೈಲಿಯಲ್ಲಿ!', 'left:-4%;top:50%'], ['Carved in granite!', 'ಗ್ರಾನೈಟ್‌ನಲ್ಲಿ ಕೆತ್ತನೆ!', 'right:-4%;top:58%', 1]],
      big: () => `${rect(0, 0, 400, 400, '#dcebf7')}${cloud(40, 60, 0.7)}${cloud(300, 50, 0.6, 1)}
        ${rect(197, 104, 6, 16, P.gold, 2)}<path d="M166 186 q34 -84 68 0z" fill="#cfc6b3"/>${rect(162, 182, 76, 10, '#bdb39c')}
        ${[[60, 206], [110, 206], [290, 206], [340, 206]].map(([x, y]) => `<path d="M${x - 16} ${y} q16 -34 32 0z" fill="#cfc6b3"/>${rect(x - 2, y - 40, 4, 10, P.gold, 1)}`).join('')}
        ${rect(36, 206, 328, 94, '#ddd6c6')}
        <g fill="#8d8473">${[52, 72, 92, 292, 312, 332].map((x) => [222, 252, 278].map((y) => rect(x, y, 10, 14, '#8d8473', 2)).join('')).join('')}</g>
        ${rect(124, 192, 152, 18, '#cfc7b5')}<text x="200" y="204.5" text-anchor="middle" font-family="Inter, sans-serif" font-size="6.6" font-weight="800" fill="#6b6250">GOVERNMENT WORK IS GOD'S WORK</text>
        ${rect(128, 210, 144, 90, '#e9e3d6')}${[136, 156, 176, 196, 216, 236, 256].map((x) => rect(x, 212, 8, 88, '#f6f2ea', 2)).join('')}
        ${rect(30, 300, 340, 10, '#c9c2b2')}${[0, 1, 2, 3].map((i) => rect(150 - i * 6, 310 + i * 6, 100 + i * 12, 6, i % 2 ? '#d8d1c1' : '#c9c2b2')).join('')}
        ${ground(334, '#8fc069', '#7fb05a')}
        <path d="M258 392 h44 v-28 h-44z" fill="#cfc7b5"/><path d="M264 372 h10 M280 380 h14" stroke="#a89f8c" stroke-width="2"/>
        ${figure({ x: 318, y: 398, s: 0.62, attire: 'commoner', skin: P.skin.deep, wear: 'turban', wearColor: '#e9e2cf', stache: 'thin', mouth: 'smile', armR: 'fwd', holdR: 'hammer', animR: 'a-tap', armL: 'down', flip: true })}
        ${figure({ x: 84, y: 398, s: 0.74, attire: 'coat', cloth: '#f1efe8', sash: '#f1efe8', wear: 'topi', face: 'round', skin: P.skin.brown, stache: 'thin', mouth: 'talk', armR: 'point', animR: 'a-point', armL: 'hip' })}`,
      small: () => `${rect(0, 0, 200, 200, '#e2ddd0')}<rect x="22" y="62" width="156" height="84" rx="6" fill="#d3ccbb" stroke="#b5ac98" stroke-width="3"/>
        <text x="100" y="98" text-anchor="middle" font-family="'Noto Sans Kannada', sans-serif" font-size="19" font-weight="800" fill="#5b5344">ಸರ್ಕಾರದ ಕೆಲಸ</text>
        <text x="100" y="128" text-anchor="middle" font-family="'Noto Sans Kannada', sans-serif" font-size="19" font-weight="800" fill="#5b5344">ದೇವರ ಕೆಲಸ</text>`,
    },
    {
      era: ['Karnataka', 'ಕರ್ನಾಟಕ'],
      title: ['Mysore State becomes Karnataka', 'ಮೈಸೂರು ರಾಜ್ಯ ಕರ್ನಾಟಕವಾಯಿತು'],
      sub: ['Renamed on 1 November 1973, under Chief Minister Devaraj Urs', '1 ನವೆಂಬರ್ 1973, ಮುಖ್ಯಮಂತ್ರಿ ದೇವರಾಜ ಅರಸು ಅವರ ಕಾಲದಲ್ಲಿ ಮರುನಾಮಕರಣ'],
      bubbles: [['Karnataka!', 'ಕರ್ನಾಟಕ!', 'left:-2%;top:30%'], ['Glory to Kannada!', 'ಸಿರಿಗನ್ನಡಂ ಗೆಲ್ಗೆ!', 'right:-4%;top:40%', 1]],
      big: () => `${rect(0, 0, 400, 400, '#fff1d6')}
        <path d="M0 40 L90 70 M400 40 L310 70" stroke="#a87a4a" stroke-width="2"/>
        <rect x="90" y="52" width="220" height="50" rx="10" fill="#fffaf0" stroke="${P.gold}" stroke-width="3"/>
        <text x="200" y="88" text-anchor="middle" font-family="'Noto Sans Kannada', sans-serif" font-size="30" font-weight="800" fill="${P.red}">ಕರ್ನಾಟಕ</text>
        <g>${Array.from({ length: 18 }, (_, i) => `<rect class="a-twinkle" style="animation-delay:-${(i * 0.29).toFixed(2)}s" x="${(i * 61) % 380 + 10}" y="${120 + ((i * 37) % 120)}" width="6" height="6" rx="1" fill="${i % 2 ? '#f5c518' : '#d9381e'}"/>`).join('')}</g>
        ${ground(330, '#9fca6e', '#8dbb5c')}
        ${figure({ x: 314, y: 398, s: 0.74, attire: 'shirt', cloth: '#5b8fd0', lower: '#3a4256', skin: P.skin.brown, stache: 'thin', mouth: 'grin', armR: 'raise', holdR: 'kflag', armL: 'down', flip: true })}
        ${figure({ x: 246, y: 398, s: 0.5, attire: 'shirt', cloth: '#f5c518', lower: '#2f6fb0', shorts: true, skin: P.skin.wheat, mouth: 'open', armR: 'raise', animR: 'a-wave', armL: 'raise', flip: true })}
        ${figure({ x: 168, y: 398, s: 0.8, attire: 'coat', cloth: '#f1e6cf', sash: '#f1e6cf', wear: 'peta', wearColor: '#f7f1e3', stache: 'handlebar', skin: P.skin.wheat, mouth: 'grin', armR: 'raise', animR: 'a-wave', armL: 'hip' })}
        ${figure({ x: 84, y: 398, s: 0.8, attire: 'saree', cloth: '#d9381e', blouse: '#f5c518', border: '#f5c518', hair: 'bun', mark: 'bindi', skin: P.skin.brown, mouth: 'grin', armR: 'raise', holdR: 'kflag', armL: 'hip' })}`,
      small: () => `${rect(0, 0, 200, 200, '#fff1d6')}${rect(56, 30, 5, 150, '#7a5232')}
        <g class="a-flag"><path d="M61 36 h90 v34 h-90z" fill="#f5c518"/><path d="M61 70 h90 v34 h-90z" fill="#d9381e"/></g>
        <text x="100" y="150" text-anchor="middle" font-family="Inter, sans-serif" font-size="13" font-weight="800" fill="#8a2f2a">1 · 11 · 1973</text>`,
    },
    {
      era: ['Sport', 'ಕ್ರೀಡೆ'],
      title: ['Prakash Padukone wins the All England', 'ಆಲ್ ಇಂಗ್ಲೆಂಡ್ ಗೆದ್ದ ಪ್ರಕಾಶ್ ಪಡುಕೋಣೆ'],
      sub: ['The first Indian champion, London, March 1980', 'ಮೊದಲ ಭಾರತೀಯ ಚಾಂಪಿಯನ್, ಲಂಡನ್, ಮಾರ್ಚ್ 1980'],
      bubbles: [['Smash!', 'ಸ್ಮ್ಯಾಶ್!', 'left:-2%;top:22%']],
      big: () => `${rect(0, 0, 400, 400, '#22314f')}
        <g>${Array.from({ length: 60 }, (_, i) => `<circle cx="${(i * 47) % 400}" cy="${70 + (i % 5) * 24 + ((i * 7) % 9)}" r="7" fill="${['#e8b04a', '#d9604a', '#7fa8d8', '#e9e2cf', '#9a7fc8'][i % 5]}" opacity=".55"/>`).join('')}</g>
        ${rect(0, 190, 400, 210, '#2f7d5a')}<path d="M0 300 H400 M60 190 L0 260 M340 190 L400 260 M200 190 V400" stroke="#fff" stroke-width="3" opacity=".75"/>
        <g stroke="#fff" stroke-width="1" opacity=".35">${Array.from({ length: 40 }, (_, i) => `<path d="M${30 + i * 8.5} 232 V268"/>`).join('')}<path d="M30 250 H370"/></g>
        ${rect(28, 228, 344, 5, '#fff')}${rect(26, 228, 5, 70, '#d7dbe2')}${rect(369, 228, 5, 70, '#d7dbe2')}
        <g class="a-shuttle" style="--dx:170px;--dy:-30px"><path d="M196 120 l-14 -8 l2 16z" fill="#fff"/><circle cx="197" cy="121" r="4" fill="#f2e6c8"/></g>
        ${figure({ x: 150, y: 398, s: 1, face: 'lean', attire: 'shirt', cloth: '#f7f7f2', lower: '#f7f7f2', shorts: true, shoes: '#f2f2f2', skin: P.skin.wheat, brows: 'fierce', mouth: 'open', armR: 'up', holdR: 'racquet', animR: 'a-strike', armL: 'fwd', move: 'a-bob' })}`,
      small: () => `${rect(0, 0, 200, 200, '#22314f')}
        <path d="M66 40 h68 q0 50 -34 62 q-34 -12 -34 -62z" fill="${P.gold}" stroke="${P.goldD}" stroke-width="3"/><path d="M66 50 q-22 0 -18 18 q4 14 24 16 M134 50 q22 0 18 18 q-4 14 -24 16" stroke="${P.gold}" stroke-width="5" fill="none"/>
        ${rect(94, 102, 12, 20, P.goldD)}${rect(74, 122, 52, 14, '#5a3a24', 3)}
        <text x="100" y="164" text-anchor="middle" font-family="Inter, sans-serif" font-size="12" font-weight="800" fill="#f2b632">ALL ENGLAND</text>
        <text x="100" y="182" text-anchor="middle" font-family="Inter, sans-serif" font-size="12" font-weight="800" fill="#fff">1980</text>`,
    },
    {
      era: ['Cricket', 'ಕ್ರಿಕೆಟ್'],
      title: ['Anil Kumble takes all ten', 'ಹತ್ತೂ ವಿಕೆಟ್ ಪಡೆದ ಅನಿಲ್ ಕುಂಬ್ಳೆ'],
      sub: ['10 for 74 against Pakistan in Delhi, February 1999', 'ದೆಹಲಿಯಲ್ಲಿ ಪಾಕಿಸ್ತಾನದ ವಿರುದ್ಧ 74ಕ್ಕೆ 10 ವಿಕೆಟ್, ಫೆಬ್ರವರಿ 1999'],
      bubbles: [['Howzat!', 'ಹೌಝಾಟ್!', 'left:-2%;top:34%'], ['All ten!', 'ಹತ್ತಕ್ಕೆ ಹತ್ತು!', 'right:-2%;top:30%', 1]],
      big: () => `${rect(0, 0, 400, 400, '#cfe8f5')}
        <g>${Array.from({ length: 70 }, (_, i) => `<circle cx="${(i * 37) % 400}" cy="${118 + (i % 4) * 12 + ((i * 5) % 7)}" r="5" fill="${['#2f6fb0', '#e9e2cf', '#d9604a', '#f2b632'][i % 4]}" opacity=".7"/>`).join('')}</g>
        ${rect(0, 166, 400, 234, '#7fb85a')}<path d="M0 166 H400" stroke="#fff" stroke-width="3"/>
        <path d="M160 400 L240 400 L218 196 L182 196Z" fill="#dcc690"/><path d="M168 360 H232 M184 222 H216" stroke="#fff" stroke-width="2.5"/>
        ${rect(186, 168, 6, 40, '#f3e6c4', 2)}${rect(208, 168, 6, 40, '#f3e6c4', 2)}
        <g transform="rotate(-26 200 208)">${rect(197, 168, 6, 40, '#f3e6c4', 2)}</g>
        <g class="a-fly">${rect(186, 160, 12, 4, '#f3e6c4', 2)}</g><g class="a-fly" style="animation-delay:-.6s">${rect(202, 160, 12, 4, '#f3e6c4', 2)}</g>
        <g class="a-rocket" style="--dx:40px;--dy:-120px"><circle cx="160" cy="320" r="5" fill="#b3261e"/></g>
        <rect x="218" y="48" width="112" height="62" rx="8" fill="#1d2a3a"/><text x="274" y="88" text-anchor="middle" font-family="Inter, sans-serif" font-size="28" font-weight="800" fill="#ffc53a">10/74</text>
        <text x="274" y="103" text-anchor="middle" font-family="Inter, sans-serif" font-size="8" font-weight="700" fill="#cfd8e6">DELHI · 1999</text>
        ${figure({ x: 110, y: 400, s: 1, face: 'long', attire: 'shirt', cloth: '#f7f7f2', sleeve: '#f7f7f2', lower: '#f7f7f2', shoes: '#f2f2f2', skin: P.skin.brown, mouth: 'open', brows: 'up', armR: 'raise', animR: 'a-wave', armL: 'raise' })}`,
      small: () => `${rect(0, 0, 200, 200, '#7fb85a')}
        <g class="a-spin" style="transform-origin:100px 86px"><circle cx="100" cy="86" r="44" fill="#b3261e"/><path d="M70 54 q30 32 0 64 M130 54 q-30 32 0 64" stroke="#f3e6c4" stroke-width="3" fill="none" stroke-dasharray="4 3"/></g>
        <text x="100" y="166" text-anchor="middle" font-family="Inter, sans-serif" font-size="18" font-weight="800" fill="#fff">10 / 74</text>`,
    },
    {
      era: ['Science & tech', 'ವಿಜ್ಞಾನ-ತಂತ್ರಜ್ಞಾನ'],
      title: ['Chandrayaan-3 lands on the Moon', 'ಚಂದ್ರನ ಮೇಲೆ ಚಂದ್ರಯಾನ-3'],
      sub: ['Guided down from ISRO\'s mission control in Bengaluru, 23 August 2023', 'ಬೆಂಗಳೂರಿನ ಇಸ್ರೋ ನಿಯಂತ್ರಣ ಕೇಂದ್ರದಿಂದ ಮಾರ್ಗದರ್ಶನ, 23 ಆಗಸ್ಟ್ 2023'],
      bubbles: [['India is on the Moon!', 'ಭಾರತ ಚಂದ್ರನ ಮೇಲೆ!', 'left:-4%;top:48%'], ['Touchdown!', 'ಇಳಿಯಿತು!', 'right:-2%;top:54%', 1]],
      big: () => `${rect(0, 0, 400, 400, '#111a33')}
        <rect x="46" y="40" width="308" height="156" rx="10" fill="#070d1d" stroke="#3a4c72" stroke-width="4"/>
        ${stars([[80, 64], [130, 90], [300, 70], [330, 120], [250, 58], [100, 130]])}
        <path d="M50 192 q150 -50 300 0z" fill="#9c9ca8"/><ellipse cx="140" cy="182" rx="14" ry="4" fill="#85858f"/><ellipse cx="280" cy="180" rx="10" ry="3" fill="#85858f"/>
        <g class="a-land"><path class="a-flicker" d="M194 176 l6 16 l6 -16z" fill="#ffb02e"/><path d="M186 172 l-10 14 M214 172 l10 14" stroke="#c9ccd6" stroke-width="2.4"/>${rect(184, 148, 32, 26, '#d9a93a', 3)}${rect(190, 140, 20, 8, '#e8e8ee', 2)}<path d="M188 160 h24" stroke="#b5862a" stroke-width="2"/></g>
        <text x="200" y="62" text-anchor="middle" font-family="Inter, sans-serif" font-size="9" font-weight="700" fill="#7fd1a8">VIKRAM · DESCENT</text>
        ${figure({ x: 120, y: 410, s: 0.8, attire: 'saree', cloth: '#7a3fa0', blouse: P.gold, border: P.gold, hair: 'bun', mark: 'bindi', skin: P.skin.brown, mouth: 'grin', armR: 'raise', animR: 'a-wave', armL: 'raise' })}
        ${figure({ x: 282, y: 410, s: 0.82, attire: 'shirt', cloth: '#e8eef6', sleeve: '#e8eef6', id: true, skin: P.skin.deep, stache: 'thin', mouth: 'grin', armR: 'raise', armL: 'raise', animL: 'a-wave', flip: true })}
        <path d="M0 340 H400 V400 H0Z" fill="#2a3550"/>${[30, 120, 210, 300].map((x, i) => `${rect(x, 316, 64, 26, '#0b1222', 3)}<rect class="a-glow" style="animation-delay:-${i * 0.5}s" x="${x + 4}" y="320" width="56" height="18" fill="#3fbf8f"/>`).join('')}`,
      small: () => `${rect(0, 0, 200, 200, '#070d1d')}<circle cx="150" cy="46" r="18" fill="#3f86d0"/><path d="M140 36 q8 4 4 12 q10 0 12 10" stroke="#5fae6a" stroke-width="5" fill="none"/>
        <path d="M0 128 q100 -26 200 0 V200 H0z" fill="#9c9ca8"/><ellipse cx="150" cy="150" rx="16" ry="5" fill="#85858f"/>
        <path d="M54 126 l-10 14 M86 126 l10 14" stroke="#c9ccd6" stroke-width="2.4"/>${rect(50, 98, 40, 30, '#d9a93a', 3)}${rect(58, 90, 24, 8, '#e8e8ee', 2)}
        <g class="a-rove">${rect(106, 128, 24, 10, '#cfd2da', 2)}<path d="M110 128 l-8 -12 h28 l-6 12" fill="#2f4f8f"/>${[108, 118, 128].map((x) => `<circle cx="${x}" cy="141" r="3.4" fill="#5d6470"/>`).join('')}</g>
        <text x="100" y="186" text-anchor="middle" font-family="Inter, sans-serif" font-size="12" font-weight="800" fill="#fff">CHANDRAYAAN-3</text>`,
    },
  ];

  // --------------------------------------------------------------- runtime
  const box = document.getElementById('scenes');
  const dots = document.getElementById('dots');
  const toggle = document.getElementById('playpause');
  const HOLD = 5000;
  const kn = () => document.documentElement.lang === 'kn';
  const txt = ([en, k]) => `data-en="${en.replace(/"/g, '&quot;')}" data-kn="${k.replace(/"/g, '&quot;')}">${kn() ? k : en}`;
  // Each visit gets a new shuffle, with scenes this browser hasn't shown yet
  // first, so a returning visitor sees new illustrations straight away.
  const KEY = 'scenes-seen';
  const shuffle = (a) => {
    for (let i = a.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [a[i], a[j]] = [a[j], a[i]];
    }
    return a;
  };
  let seen = [];
  try { seen = JSON.parse(localStorage.getItem(KEY)) || []; } catch (e) { /* storage blocked */ }
  if (!Array.isArray(seen)) seen = [];
  const last = seen[seen.length - 1];
  let fresh = SCENES.filter((sc) => !seen.includes(sc.title[0]));
  if (!fresh.length) { seen = []; fresh = SCENES.filter((sc) => sc.title[0] !== last); }
  const ORDER = [...shuffle(fresh), ...shuffle(SCENES.filter((sc) => !fresh.includes(sc)))];
  function markSeen(sc) {
    if (seen.includes(sc.title[0])) return;
    seen.push(sc.title[0]);
    try { localStorage.setItem(KEY, JSON.stringify(seen)); } catch (e) { /* storage blocked */ }
  }

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
    at0 = (n + ORDER.length) % ORDER.length;
    const next = build(ORDER[at0]);
    markSeen(ORDER[at0]);
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

  dots.innerHTML = ORDER.map((s) => `<button type="button" aria-label="${s.title[0].replace(/"/g, '&quot;')}"></button>`).join('');
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
