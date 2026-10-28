/* Share card: the search result drawn as a picture (1080 x 1350, the shape
 * WhatsApp status and Instagram show whole), in the site's own look — warm
 * paper, dot grid, the amber-to-red gradient, the ticket tiles.
 *
 * Drawn here in the browser like everything else on the page: nothing is sent
 * anywhere. Only the last four digits of the EPIC are shown; the full number
 * stays on the phone unless its owner types it somewhere.
 */
(() => {
  const W = 1080, H = 1350;
  const C = {
    bg: '#f8f5ef', surface: '#ffffff', surface2: '#f3efe7', ink: '#16192b', ink2: '#5b6078',
    line: '#e8e2d6', ok: '#0f8a5f', okBg: '#e6f6ef', accent2: '#d9381e', dot: 'rgba(22, 25, 43, .07)'
  };
  const FONT = (w, px) => `${w} ${px}px Inter, 'Noto Sans Kannada', system-ui, sans-serif`;

  function rr(ctx, x, y, w, h, r) {
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.arcTo(x + w, y, x + w, y + h, r);
    ctx.arcTo(x + w, y + h, x, y + h, r);
    ctx.arcTo(x, y + h, x, y, r);
    ctx.arcTo(x, y, x + w, y, r);
    ctx.closePath();
  }

  const grad = (ctx, x0, y0, x1, y1) => {
    const g = ctx.createLinearGradient(x0, y0, x1, y1);
    g.addColorStop(0, '#f5b301'); g.addColorStop(0.5, '#ef7a1a'); g.addColorStop(1, '#d9381e');
    return g;
  };

  // The largest size (<= px) at which `text` fits in `max` pixels.
  function fit(ctx, text, weight, px, max) {
    for (; px > 18; px -= 2) {
      ctx.font = FONT(weight, px);
      if (ctx.measureText(text).width <= max) break;
    }
    return px;
  }

  function blob(ctx, x, y, r, color) {
    const g = ctx.createRadialGradient(x, y, 0, x, y, r);
    g.addColorStop(0, color); g.addColorStop(1, 'rgba(255,255,255,0)');
    ctx.fillStyle = g;
    ctx.fillRect(x - r, y - r, 2 * r, 2 * r);
  }

  function check(ctx, x, y, s, width, color) {
    ctx.save();
    ctx.strokeStyle = color; ctx.lineWidth = width; ctx.lineCap = 'round'; ctx.lineJoin = 'round';
    ctx.beginPath();
    ctx.moveTo(x - s * 0.42, y + s * 0.02);
    ctx.lineTo(x - s * 0.12, y + s * 0.32);
    ctx.lineTo(x + s * 0.46, y - s * 0.3);
    ctx.stroke();
    ctx.restore();
  }

  /* o: { kn, brand, roll, headline, verified, place, district, tiles: [[label, value] x3],
   *      epicLabel, epicMasked, cta, url, privacy } — all text already in the chosen language. */
  async function draw(o) {
    try {
      await Promise.all([
        document.fonts.load(FONT(800, 80), 'Ag'), document.fonts.load(FONT(600, 30), 'Ag'),
        document.fonts.load(`800 80px 'Noto Sans Kannada'`, 'ಕನ್ನಡ'), document.fonts.load(`600 30px 'Noto Sans Kannada'`, 'ಕನ್ನಡ')
      ]);
    } catch { /* system fonts will do */ }
    const cv = document.createElement('canvas');
    cv.width = W; cv.height = H;
    const ctx = cv.getContext('2d');
    ctx.textBaseline = 'alphabetic';

    // Paper, dot grid and the three soft blobs of the page backdrop.
    ctx.fillStyle = C.bg; ctx.fillRect(0, 0, W, H);
    blob(ctx, 960, 110, 420, 'rgba(245, 179, 1, .30)');
    blob(ctx, 90, 760, 380, 'rgba(239, 122, 26, .16)');
    blob(ctx, 1000, 1240, 420, 'rgba(217, 56, 30, .16)');
    ctx.fillStyle = C.dot;
    for (let y = 22; y < H; y += 44) for (let x = 22; x < W; x += 44) { ctx.beginPath(); ctx.arc(x, y, 2.4, 0, 7); ctx.fill(); }

    const L = 84, R = W - 84;

    // Brand row: the gradient tile with its tick, then the site's name.
    ctx.save();
    ctx.shadowColor = 'rgba(217, 56, 30, .45)'; ctx.shadowBlur = 24; ctx.shadowOffsetY = 10;
    rr(ctx, L, 84, 76, 76, 22); ctx.fillStyle = grad(ctx, L, 84, L + 76, 160); ctx.fill();
    ctx.restore();
    check(ctx, L + 38, 122, 40, 8, '#fff');
    ctx.fillStyle = C.ink;
    fit(ctx, o.brand, 800, 36, R - L - 100);
    ctx.fillText(o.brand, L + 100, 136);

    // Eyebrow pill with the roll's name.
    ctx.font = FONT(600, 26);
    const pw = Math.min(ctx.measureText(o.roll).width + 74, R - L);
    rr(ctx, L, 204, pw, 52, 26); ctx.fillStyle = C.surface; ctx.fill();
    ctx.strokeStyle = C.line; ctx.lineWidth = 2; ctx.stroke();
    ctx.beginPath(); ctx.arc(L + 30, 230, 8, 0, 7); ctx.fillStyle = grad(ctx, L + 22, 222, L + 38, 238); ctx.fill();
    ctx.fillStyle = C.ink2; ctx.fillText(o.roll, L + 50, 239, pw - 64);

    // Headline in the page's ink-to-red heading gradient.
    const hpx = fit(ctx, o.headline, 800, o.kn ? 84 : 104, R - L);
    const hg = ctx.createLinearGradient(L, 0, R, 0);
    hg.addColorStop(0.3, C.ink); hg.addColorStop(1, '#b8321b');
    ctx.fillStyle = hg;
    ctx.fillText(o.headline, L, 300 + hpx);

    // The result card.
    const cy = 470, ch = 640;
    ctx.save();
    ctx.shadowColor = 'rgba(22, 25, 43, .18)'; ctx.shadowBlur = 60; ctx.shadowOffsetY = 26;
    rr(ctx, L, cy, R - L, ch, 44); ctx.fillStyle = C.surface; ctx.fill();
    ctx.restore();
    ctx.save();
    rr(ctx, L, cy, R - L, ch, 44); ctx.clip();
    ctx.fillStyle = C.okBg; ctx.fillRect(L, cy, R - L, 104);
    ctx.restore();
    rr(ctx, L, cy, R - L, ch, 44); ctx.strokeStyle = C.line; ctx.lineWidth = 2; ctx.stroke();

    // Header band: green dot with a tick, "Verified on the final roll".
    ctx.beginPath(); ctx.arc(L + 68, cy + 52, 26, 0, 7); ctx.fillStyle = C.ok; ctx.fill();
    check(ctx, L + 68, cy + 53, 24, 5.5, '#fff');
    ctx.fillStyle = C.ok;
    fit(ctx, o.verified, 700, 34, R - L - 150);
    ctx.fillText(o.verified, L + 112, cy + 64);

    // Constituency and district.
    const ix = L + 48, iw = R - L - 96;
    ctx.fillStyle = C.ink;
    fit(ctx, o.place, 800, 54, iw);
    ctx.fillText(o.place, ix, cy + 196);
    ctx.fillStyle = C.ink2;
    fit(ctx, o.district, 500, 32, iw);
    ctx.fillText(o.district, ix, cy + 246);

    // Three ticket tiles, gradient edge on the left, as on the page.
    const gap = 20, tw = (iw - 2 * gap) / 3, ty = cy + 290, th = 180;
    o.tiles.forEach(([k, v], i) => {
      const tx = ix + i * (tw + gap);
      ctx.save();
      rr(ctx, tx, ty, tw, th, 28); ctx.clip();
      ctx.fillStyle = C.surface2; ctx.fillRect(tx, ty, tw, th);
      ctx.fillStyle = grad(ctx, tx, ty, tx, ty + th); ctx.fillRect(tx, ty, 7, th);
      ctx.restore();
      ctx.fillStyle = C.ink2;
      fit(ctx, k.toUpperCase(), 700, 22, tw - 48);
      ctx.fillText(k.toUpperCase(), tx + 30, ty + 52);
      ctx.fillStyle = C.ink;
      fit(ctx, String(v), 800, 76, tw - 48);
      ctx.fillText(String(v), tx + 30, ty + 140);
    });

    // EPIC, last four digits only.
    const ey = ty + th + 44;
    rr(ctx, ix, ey, iw, 76, 22); ctx.fillStyle = C.surface2; ctx.fill();
    ctx.fillStyle = C.ink2; ctx.font = FONT(700, 24);
    ctx.fillText(o.epicLabel, ix + 30, ey + 48);
    ctx.fillStyle = C.ink; ctx.font = FONT(800, 36);
    const ew = ctx.measureText(o.epicMasked).width;
    ctx.fillText(o.epicMasked, ix + iw - 30 - ew, ey + 51);

    // Call to action, the address, and the privacy promise.
    ctx.fillStyle = C.ink;
    fit(ctx, o.cta, 800, 44, R - L);
    ctx.fillText(o.cta, L, 1196);
    ctx.fillStyle = C.accent2;
    fit(ctx, o.url, 700, 32, R - L);
    ctx.fillText(o.url, L, 1246);
    ctx.fillStyle = C.ink2;
    fit(ctx, o.privacy, 500, 24, R - L);
    ctx.fillText(o.privacy, L, 1290);

    // The gradient rule along the bottom edge.
    ctx.fillStyle = grad(ctx, 0, 0, W, 0); ctx.fillRect(0, H - 14, W, 14);

    return new Promise((res) => cv.toBlob(res, 'image/png'));
  }

  window.ShareCard = { draw };
})();
