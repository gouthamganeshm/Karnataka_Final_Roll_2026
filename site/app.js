/* Karnataka roll search — static client.
 *
 * Lookup without a server: SHA-256(EPIC) in the browser; bytes 0..1 pick the
 * bucket data/roll/<ab>/<cd>.bin, bytes 2..5 are binary-searched inside it.
 * The EPIC itself is never sent anywhere. Record layout: see scripts/ci/build.mjs.
 */
(() => {
  const REC = 9;
  const EPIC_RE = /^[A-Z]{3}[0-9]{7}$/;
  const $ = (id) => document.getElementById(id);
  let manifest = null;
  let lang = 'kn';

  // ------------------------------------------------------------ preferences
  const store = {
    get(k) { try { return localStorage.getItem(k); } catch { return null; } },
    set(k, v) { try { localStorage.setItem(k, v); } catch { /* private mode */ } }
  };

  function applyLang(l) {
    lang = l;
    document.documentElement.lang = l === 'kn' ? 'kn' : 'en';
    document.body.classList.toggle('kn', l === 'kn');
    document.querySelectorAll('[data-en]').forEach((el) => { el.textContent = el.dataset[l] || el.dataset.en; });
    $('lang').textContent = l === 'kn' ? 'English' : 'ಕನ್ನಡ';
    $('filter').placeholder = l === 'kn' ? 'ಹೆಸರು ಅಥವಾ ಸಂಖ್ಯೆಯಿಂದ ಹುಡುಕಿ' : 'Filter by name or number';
    if (manifest) renderMeta();
    if (last) render(last);
  }
  $('lang').addEventListener('click', () => { const n = lang === 'en' ? 'kn' : 'en'; store.set('lang', n); applyLang(n); });

  function applyTheme(t) { if (t) document.documentElement.dataset.theme = t; else delete document.documentElement.dataset.theme; }
  $('theme').addEventListener('click', () => {
    const dark = document.documentElement.dataset.theme
      ? document.documentElement.dataset.theme === 'dark'
      : matchMedia('(prefers-color-scheme: dark)').matches;
    const t = dark ? 'light' : 'dark';
    store.set('theme', t); applyTheme(t);
  });
  applyTheme(store.get('theme'));

  const t = (en, kn) => (lang === 'kn' ? kn : en);
  const fmt = (n) => Number(n).toLocaleString('en-IN');

  // --------------------------------------------------------------- data
  async function loadManifest() {
    const r = await fetch('data/manifest.json', { cache: 'no-cache' });
    if (!r.ok) throw new Error('manifest ' + r.status);
    manifest = await r.json();
    manifest.byAc = new Map(manifest.acs.map((a) => [a.ac, a]));
    renderMeta();
  }

  const buckets = new Map();
  async function bucket(ab, cd) {
    const key = ab + cd;
    if (!buckets.has(key)) {
      buckets.set(key, fetch(`data/roll/${ab}/${cd}.bin?v=${encodeURIComponent(manifest.builtAt)}`)
        .then((r) => (r.status === 404 ? new ArrayBuffer(0) : r.ok ? r.arrayBuffer() : Promise.reject(new Error('bucket ' + r.status)))));
    }
    return new DataView(await buckets.get(key));
  }

  async function lookup(epic) {
    const h = new Uint8Array(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(epic)));
    const hex = (b) => b.toString(16).padStart(2, '0');
    const dv = await bucket(hex(h[0]), hex(h[1]));
    const want = ((h[2] << 24) | (h[3] << 16) | (h[4] << 8) | h[5]) >>> 0;
    const n = dv.byteLength / REC;
    let lo = 0, hi = n;
    while (lo < hi) {               // first record with suffix >= want
      const mid = (lo + hi) >> 1;
      if (dv.getUint32(mid * REC, false) < want) lo = mid + 1; else hi = mid;
    }
    const hits = [];
    for (let i = lo; i < n && dv.getUint32(i * REC, false) === want; i++) {
      const o = i * REC;
      const s = dv.getUint16(o + 7, true);
      hits.push({ ac: dv.getUint8(o + 4), part: dv.getUint16(o + 5, true), serial: s & 0x7fff, approx: !!(s & 0x8000) });
    }
    return hits;
  }

  // ------------------------------------------------------------- render
  let last = null;

  function renderMeta() {
    const m = manifest;
    $('roll-label').textContent = (lang === 'kn' && m.labelKn) ? m.labelKn : m.label;
    $('stats').hidden = false;
    $('s-electors').textContent = fmt(m.electors);
    $('s-acs').textContent = `${m.acs.filter((a) => a.status === 'verified').length}/${m.acs.length}`;
    $('s-cov').textContent = (Math.floor(m.coverage * 1000) / 10) + '%';
    $('built').textContent = t('Data updated ', 'ಮಾಹಿತಿ ನವೀಕರಿಸಲಾಗಿದೆ ') +
      new Date(m.builtAt).toLocaleString(lang === 'kn' ? 'kn-IN' : 'en-IN', { dateStyle: 'medium', timeStyle: 'short' });
    renderTable();
  }

  function renderTable() {
    $('coverage-wrap').hidden = false;
    const q = $('filter').value.trim().toLowerCase();
    const rows = manifest.acs.filter((a) => !q || String(a.ac) === q ||
      a.name?.toLowerCase().includes(q) || a.nameKn?.includes(q) || a.district?.toLowerCase().includes(q));
    // Only verified constituencies are searchable; the others say why not yet.
    const state = (a) => a.status === 'verified'
      ? `${a.partsRead}/${a.parts}<span class="bar"><i style="width:${((a.parts ? a.partsRead / a.parts : 0) * 100).toFixed(1)}%"></i></span>`
      : a.status === 'held'
        ? `<span class="tag hold">${t('under review', 'ಪರಿಶೀಲನೆಯಲ್ಲಿದೆ')}</span>`
        : `<span class="tag">${t('processing', 'ಪ್ರಕ್ರಿಯೆಯಲ್ಲಿದೆ')}</span>`;
    $('cov-table').tBodies[0].innerHTML = rows.map((a) => `<tr><td>${a.ac}</td><td>${esc(lang === 'kn' && a.nameKn ? a.nameKn : a.name)}</td>
        <td>${esc(lang === 'kn' && a.districtKn ? a.districtKn : title(a.district))}</td><td class="r">${a.status === 'verified' ? fmt(a.electors) : '—'}</td>
        <td class="r">${state(a)}</td></tr>`).join('');
  }
  $('filter').addEventListener('input', () => manifest && renderTable());

  const esc = (s) => String(s ?? '').replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const title = (s) => String(s ?? '').toLowerCase().replace(/\b\w/g, (c) => c.toUpperCase());
  const pdfUrl = (ac, part) => manifest.url.replace(/\{ac\}/g, ac).replace(/\{part\}/g, part);

  function render(state) {
    last = state;
    const el = $('result');
    if (state.kind === 'loading') {
      el.innerHTML = `<div class="res"><div class="res-head"><span class="spin"></span>${t('Searching…', 'ಹುಡುಕಲಾಗುತ್ತಿದೆ…')}</div></div>`;
      return;
    }
    if (state.kind === 'invalid') {
      el.innerHTML = card('bad', '!', t('That doesn\'t look like an EPIC number', 'ಇದು EPIC ಸಂಖ್ಯೆಯಂತೆ ಕಾಣುತ್ತಿಲ್ಲ'),
        `<p class="note">${t('An EPIC number is 3 letters followed by 7 digits, like ABC1234567. Check the front of your voter ID card.',
          'EPIC ಸಂಖ್ಯೆ 3 ಅಕ್ಷರಗಳು ಮತ್ತು 7 ಅಂಕಿಗಳನ್ನು ಹೊಂದಿರುತ್ತದೆ, ಉದಾ. ABC1234567. ನಿಮ್ಮ ಗುರುತಿನ ಚೀಟಿಯ ಮುಂಭಾಗವನ್ನು ನೋಡಿ.')}</p>`);
      return;
    }
    if (state.kind === 'error') {
      el.innerHTML = card('warn', '!', t('Couldn\'t load the data', 'ಮಾಹಿತಿ ಲೋಡ್ ಆಗಲಿಲ್ಲ'),
        `<p class="note">${t('Check your connection and try again.', 'ನಿಮ್ಮ ಸಂಪರ್ಕ ಪರಿಶೀಲಿಸಿ ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ.')}</p>`);
      return;
    }
    const { epic, hits } = state;
    if (!hits.length) {
      const complete = manifest.coverage >= 0.99;
      el.innerHTML = complete
        ? card('bad', '✕', t('Not found on this roll', 'ಈ ಪಟ್ಟಿಯಲ್ಲಿ ಸಿಗಲಿಲ್ಲ'),
          `<div class="epic-echo">${epic}</div>
           <p class="note">${t('First re-check every character. A small share of cards could not be read clearly from the PDFs, so if you believe you are registered, confirm at voters.eci.gov.in or call 1950 before assuming you have been removed.',
             'ಪ್ರತಿಯೊಂದು ಅಕ್ಷರವನ್ನು ಮತ್ತೊಮ್ಮೆ ಪರಿಶೀಲಿಸಿ. ಕೆಲವು ಕಾರ್ಡ್‌ಗಳನ್ನು PDF ನಿಂದ ಸ್ಪಷ್ಟವಾಗಿ ಓದಲಾಗಲಿಲ್ಲ — ನೀವು ನೋಂದಾಯಿತರು ಎಂದು ಭಾವಿಸಿದರೆ voters.eci.gov.in ನಲ್ಲಿ ಪರಿಶೀಲಿಸಿ ಅಥವಾ 1950 ಗೆ ಕರೆ ಮಾಡಿ.')}</p>
           <div class="actions"><a class="btn primary" href="https://electoralsearch.eci.gov.in/" target="_blank" rel="noopener">${t('Search on ECI', 'ECI ಯಲ್ಲಿ ಹುಡುಕಿ')} ↗</a>
           <a class="btn" href="tel:1950">${t('Call 1950', '1950 ಗೆ ಕರೆ')}</a></div>`)
        : card('warn', '…', t('Can\'t say yet', 'ಈಗಲೇ ಹೇಳಲಾಗದು'),
          `<div class="epic-echo">${epic}</div>
           <p class="note">${t(`Not found in the ${Math.floor(manifest.coverage * 100)}% of booths loaded so far. The rest is still being processed — please check again later today.`,
             `ಈವರೆಗೆ ಲೋಡ್ ಆದ ${Math.floor(manifest.coverage * 100)}% ಮತಗಟ್ಟೆಗಳಲ್ಲಿ ಸಿಗಲಿಲ್ಲ. ಉಳಿದವು ಪ್ರಕ್ರಿಯೆಯಲ್ಲಿವೆ — ಸ್ವಲ್ಪ ಸಮಯದ ನಂತರ ಮತ್ತೆ ಪರಿಶೀಲಿಸಿ.`)}</p>`);
      return;
    }
    const blocks = hits.map((h) => {
      const a = manifest.byAc.get(h.ac) || { name: '', nameKn: '', district: '' };
      const name = lang === 'kn' && a.nameKn ? a.nameKn : a.name;
      return `<div class="multi">
        <p class="place">${h.ac} · ${esc(name)}</p>
        <p class="place-sub">${esc(lang === 'kn' && a.districtKn ? a.districtKn : title(a.district))} ${t('district', 'ಜಿಲ್ಲೆ')}</p>
        <div class="ticket">
          <div class="tk"><span class="k">${t('Constituency', 'ಕ್ಷೇತ್ರ')}</span><span class="v">${h.ac}</span></div>
          <div class="tk"><span class="k">${t('Part', 'ಭಾಗ')}</span><span class="v">${h.part}</span></div>
          <div class="tk"><span class="k">${t('Serial', 'ಕ್ರಮ ಸಂಖ್ಯೆ')}</span><span class="v">${h.approx ? '~' : ''}${h.serial}</span></div>
        </div>
        ${h.approx ? `<p class="note">${t('~ The serial number could not be fully confirmed by the reader; it is very likely right, but check it in the PDF.', '~ ಕ್ರಮ ಸಂಖ್ಯೆಯನ್ನು ಸಂಪೂರ್ಣವಾಗಿ ದೃಢೀಕರಿಸಲಾಗಲಿಲ್ಲ; PDF ನಲ್ಲಿ ಪರಿಶೀಲಿಸಿ.')}</p>` : ''}
        <div class="actions">
          <a class="btn primary" href="${pdfUrl(h.ac, h.part)}" target="_blank" rel="noopener">${t('Open official PDF', 'ಅಧಿಕೃತ PDF ತೆರೆಯಿರಿ')} ↗</a>
          <button class="btn" type="button" data-share>${t('Share', 'ಹಂಚಿಕೊಳ್ಳಿ')}</button>
        </div></div>`;
    }).join('');
    const head = hits.length > 1
      ? t(`Found in ${hits.length} places`, `${hits.length} ಸ್ಥಳಗಳಲ್ಲಿ ಸಿಕ್ಕಿದೆ`)
      : t('You\'re on the roll', 'ನೀವು ಪಟ್ಟಿಯಲ್ಲಿದ್ದೀರಿ');
    el.innerHTML = card('ok', '✓', head, `<div class="epic-echo">${epic}</div>${blocks}`);
    el.querySelectorAll('[data-share]').forEach((b) => b.addEventListener('click', share));
  }

  function card(kind, icon, head, body) {
    return `<div class="res ${kind}"><div class="res-head"><span class="dot">${icon}</span>${head}</div><div class="res-body">${body}</div></div>`;
  }

  async function share() {
    const u = location.origin + location.pathname;
    const text = t('Check your name on the Karnataka electoral roll with your EPIC number:', 'ನಿಮ್ಮ EPIC ಸಂಖ್ಯೆಯಿಂದ ಕರ್ನಾಟಕ ಮತದಾರರ ಪಟ್ಟಿಯಲ್ಲಿ ನಿಮ್ಮ ಹೆಸರು ಪರಿಶೀಲಿಸಿ:');
    try {
      if (navigator.share) await navigator.share({ title: document.title, text, url: u });
      else { await navigator.clipboard.writeText(`${text} ${u}`); }
    } catch { /* dismissed */ }
  }

  // ------------------------------------------------------------- search
  const clean = (s) => s.toUpperCase().replace(/[^A-Z0-9]/g, '');
  $('epic').addEventListener('input', (e) => {
    const c = clean(e.target.value);
    if (c !== e.target.value) e.target.value = c;
  });

  $('search').addEventListener('submit', async (e) => {
    e.preventDefault();
    const epic = clean($('epic').value);
    if (!EPIC_RE.test(epic)) { render({ kind: 'invalid' }); return; }
    // Keep the number out of the URL and history: it stays on this device.
    $('go').disabled = true;
    render({ kind: 'loading' });
    try {
      if (!manifest) await loadManifest();
      render({ kind: 'done', epic, hits: await lookup(epic) });
    } catch (err) {
      console.error(err);
      render({ kind: 'error' });
    } finally {
      $('go').disabled = false;
    }
  });

  // ---------------------------------------------------------------- boot
  const saved = store.get('lang');
  applyLang(saved || 'kn'); // Kannada first; the toggle remembers a switch to English
  loadManifest().catch((err) => console.error(err));
  $('epic').focus({ preventScroll: true });
})();
