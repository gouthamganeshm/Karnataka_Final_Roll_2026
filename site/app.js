/* Karnataka roll search — static client.
 *
 * Lookup without a server: SHA-256(EPIC) in the browser; bytes 0..1 pick the
 * bucket data/roll/<ab>/<cd>.bin, bytes 2..5 are binary-searched inside it.
 * The EPIC itself is never sent anywhere. Record layout: see scripts/ci/build.mjs.
 */
(() => {
  const REC = 9;
  const FORMAT = 2; // record layout this script reads; see scripts/ci/build.mjs
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
    if ((manifest.format ?? 1) > FORMAT) {
      // Newer data than this (cached) script understands: fetch the page again, once.
      let tried = null;
      try { tried = sessionStorage.getItem('reloaded'); sessionStorage.setItem('reloaded', manifest.builtAt); } catch { /* ignore */ }
      if (tried !== manifest.builtAt) { location.reload(); return new Promise(() => {}); }
    }
    manifest.byAc = new Map(manifest.acs.map((a) => [a.ac, a]));
    renderMeta();
  }

  const buckets = new Map();
  async function bucket(ab, cd) {
    const key = ab + cd;
    const get = () => fetch(`data/roll/${ab}/${cd}.bin?v=${encodeURIComponent(manifest.builtAt)}`)
      .then((r) => (r.status === 404 ? new ArrayBuffer(0) : r.ok ? r.arrayBuffer() : Promise.reject(new Error('bucket ' + r.status))));
    if (!buckets.has(key)) {
      // One retry after a pause; a failure is not remembered, so the next
      // search tries again instead of failing until the page is reloaded.
      buckets.set(key, get().catch(() => new Promise((ok) => setTimeout(ok, 1500)).then(get))
        .catch((err) => { buckets.delete(key); throw err; }));
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
      const p = dv.getUint16(o + 5, true);
      const s = dv.getUint16(o + 7, true);
      hits.push({ ac: dv.getUint8(o + 4), part: p & 0x7fff, deleted: !!(p & 0x8000), serial: s & 0x7fff, approx: !!(s & 0x8000) });
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
    // Searchable electors against the CEO's official count for the AC.
    const match = (a) => (a.status === 'verified' && a.official ? (Math.floor(1000 * a.electors / a.official) / 10).toFixed(1) + '%' : '—');
    $('cov-table').tBodies[0].innerHTML = rows.map((a) => `<tr><td>${a.ac}</td><td>${esc(lang === 'kn' && a.nameKn ? a.nameKn : a.name)}</td>
        <td>${esc(lang === 'kn' && a.districtKn ? a.districtKn : title(a.district))}</td><td class="r">${a.status === 'verified' ? fmt(a.electors) : '—'}</td>
        <td class="r">${a.official ? fmt(a.official) : '—'}</td><td class="r">${match(a)}</td>
        <td class="r">${state(a)}</td></tr>`).join('');
    const live = manifest.acs.filter((a) => a.status === 'verified' && a.official);
    const sum = (k) => live.reduce((n, a) => n + a[k], 0);
    $('cov-table').tFoot.innerHTML = live.length
      ? `<tr><td></td><td colspan="2">${t(`${live.length} constituencies loaded`, `${live.length} ಕ್ಷೇತ್ರಗಳು ಲೋಡ್ ಆಗಿವೆ`)}</td>
         <td class="r">${fmt(sum('electors'))}</td><td class="r">${fmt(sum('official'))}</td>
         <td class="r">${(Math.floor(1000 * sum('electors') / sum('official')) / 10).toFixed(1)}%</td><td></td></tr>`
      : '';
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
    const { epic } = state;
    // A card the final roll stamps DELETED is published too, flagged, so a
    // struck-off EPIC can be told apart from one that is simply not loaded.
    const hits = state.hits.filter((h) => !h.deleted);
    const gone = state.hits.filter((h) => h.deleted);
    if (!hits.length && gone.length) {
      const more = manifest.coverage < 0.99
        ? t(' Not every constituency is loaded yet, so check again later.', ' ಎಲ್ಲಾ ಕ್ಷೇತ್ರಗಳು ಇನ್ನೂ ಲೋಡ್ ಆಗಿಲ್ಲ — ಸ್ವಲ್ಪ ಸಮಯದ ನಂತರ ಮತ್ತೆ ಪರಿಶೀಲಿಸಿ.')
        : '';
      el.innerHTML = card('bad', '✕', t('Marked DELETED in the final roll', 'ಅಂತಿಮ ಪಟ್ಟಿಯಲ್ಲಿ ಅಳಿಸಲಾಗಿದೆ (DELETED)'),
        `<div class="epic-echo">${epic}</div>${gone.map(place).join('')}
         <p class="note">${t('This EPIC is in the final roll at the place above, but the entry is struck off with a DELETED stamp, so it is not on the roll there. Open the PDF to see the card and the reason code beside the serial. If you moved, you may be enrolled elsewhere.' + more + ' If you think the deletion is wrong, call 1950 or contact your Electoral Registration Officer; you can apply again with Form 6.',
           'ಈ EPIC ಅಂತಿಮ ಪಟ್ಟಿಯಲ್ಲಿ ಮೇಲಿನ ಸ್ಥಳದಲ್ಲಿದೆ, ಆದರೆ ಆ ನಮೂದನ್ನು DELETED ಮುದ್ರೆಯೊಂದಿಗೆ ಅಳಿಸಲಾಗಿದೆ — ಅಲ್ಲಿ ನೀವು ಪಟ್ಟಿಯಲ್ಲಿಲ್ಲ. ಕಾರ್ಡ್ ಮತ್ತು ಕ್ರಮ ಸಂಖ್ಯೆಯ ಪಕ್ಕದ ಕಾರಣ ಸಂಕೇತವನ್ನು ನೋಡಲು PDF ತೆರೆಯಿರಿ. ನೀವು ಸ್ಥಳಾಂತರಗೊಂಡಿದ್ದರೆ ಬೇರೆಡೆ ನೋಂದಾಯಿತರಾಗಿರಬಹುದು.' + more + ' ಅಳಿಸುವಿಕೆ ತಪ್ಪು ಎಂದು ಭಾವಿಸಿದರೆ 1950 ಗೆ ಕರೆ ಮಾಡಿ ಅಥವಾ ಮತದಾರರ ನೋಂದಣಿ ಅಧಿಕಾರಿಯನ್ನು ಸಂಪರ್ಕಿಸಿ; ನಮೂನೆ 6 ಮೂಲಕ ಮತ್ತೆ ಅರ್ಜಿ ಸಲ್ಲಿಸಬಹುದು.')}</p>
         <div class="actions"><a class="btn" href="tel:1950">${t('Call 1950', '1950 ಗೆ ಕರೆ')}</a></div>`);
      return;
    }
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
    const blocks = hits.map((h, i) => place(h, i)).join('');
    const head = hits.length > 1
      ? t(`Found in ${hits.length} places`, `${hits.length} ಸ್ಥಳಗಳಲ್ಲಿ ಸಿಕ್ಕಿದೆ`)
      : t('You\'re on the roll', 'ನೀವು ಪಟ್ಟಿಯಲ್ಲಿದ್ದೀರಿ');
    const struck = gone.length
      ? `<p class="note">${t('Also listed as DELETED at ', 'ಇಲ್ಲಿ DELETED ಎಂದೂ ಇದೆ: ')}${gone.map((h) =>
          `${h.ac} · ${t('part', 'ಭಾಗ')} ${h.part} · ${t('serial', 'ಕ್ರಮ ಸಂಖ್ಯೆ')} ${h.serial}`).join(', ')}${
          t(' — an older entry struck off, usually because the voter moved.', ' — ಹಳೆಯ ನಮೂದು, ಸಾಮಾನ್ಯವಾಗಿ ಸ್ಥಳಾಂತರದಿಂದಾಗಿ ಅಳಿಸಲಾಗಿದೆ.')}</p>`
      : '';
    el.innerHTML = card('ok', '✓', head, `<div class="epic-echo">${epic}</div>${blocks}${struck}`);
    el.querySelectorAll('[data-share]').forEach((b) => b.addEventListener('click', () => share(hits[+b.dataset.share], epic, b)));
  }

  function place(h, i) {
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
        ${h.deleted || i === undefined ? '' : `<button class="btn" type="button" data-share="${i}">${t('Share', 'ಹಂಚಿಕೊಳ್ಳಿ')}</button>`}
      </div></div>`;
  }

  function card(kind, icon, head, body) {
    return `<div class="res ${kind}"><div class="res-head"><span class="dot">${icon}</span>${head}</div><div class="res-body">${body}</div></div>`;
  }

  // Share the result as a picture (sharecard.js), not just the address: the
  // phone's share sheet where it takes files, else a preview to save or send.
  async function share(h, epic, btn) {
    const u = location.origin + location.pathname.replace(/index\.html$/, '');
    const text = t('I found my name on the Karnataka electoral roll. Check yours with your EPIC number:',
      'ಕರ್ನಾಟಕ ಮತದಾರರ ಪಟ್ಟಿಯಲ್ಲಿ ನನ್ನ ಹೆಸರು ಸಿಕ್ಕಿದೆ. ನಿಮ್ಮ EPIC ಸಂಖ್ಯೆಯಿಂದ ನಿಮ್ಮದನ್ನೂ ಪರಿಶೀಲಿಸಿ:');
    const a = manifest.byAc.get(h.ac) || {};
    btn.disabled = true;
    let file = null;
    try {
      const png = await window.ShareCard.draw({
        kn: lang === 'kn',
        brand: t('Karnataka Roll Search', 'ಕರ್ನಾಟಕ ಮತದಾರರ ಪಟ್ಟಿ ಹುಡುಕಾಟ'),
        roll: (lang === 'kn' && manifest.labelKn) ? manifest.labelKn : manifest.label,
        headline: t('I\'m on the roll!', 'ನಾನು ಪಟ್ಟಿಯಲ್ಲಿದ್ದೇನೆ!'),
        verified: t('Found on the final electoral roll', 'ಅಂತಿಮ ಮತದಾರರ ಪಟ್ಟಿಯಲ್ಲಿ ಸಿಕ್ಕಿದೆ'),
        place: `${h.ac} · ${lang === 'kn' && a.nameKn ? a.nameKn : a.name || ''}`,
        district: `${lang === 'kn' && a.districtKn ? a.districtKn : title(a.district)} ${t('district', 'ಜಿಲ್ಲೆ')}`,
        tiles: [[t('Constituency', 'ಕ್ಷೇತ್ರ'), h.ac], [t('Part', 'ಭಾಗ'), h.part],
          [t('Serial', 'ಕ್ರಮ ಸಂಖ್ಯೆ'), `${h.approx ? '~' : ''}${h.serial}`]],
        epicLabel: 'EPIC',
        epicMasked: `•••••• ${epic.slice(-4)}`,
        cta: t('Are you on it? Check in seconds.', 'ನಿಮ್ಮ ಹೆಸರು ಇದೆಯೇ? ಕ್ಷಣದಲ್ಲಿ ಪರಿಶೀಲಿಸಿ.'),
        url: u.replace(/^https?:\/\//, '').replace(/\/$/, ''),
        privacy: t('Your EPIC number never leaves your phone.', 'ನಿಮ್ಮ EPIC ಸಂಖ್ಯೆ ನಿಮ್ಮ ಫೋನ್‌ನಿಂದ ಹೊರಹೋಗುವುದಿಲ್ಲ.')
      });
      if (png) file = new File([png], `karnataka-roll-${h.ac}-${h.part}.png`, { type: 'image/png' });
    } catch (err) { console.error(err); }
    btn.disabled = false;
    try {
      if (file && navigator.canShare?.({ files: [file] })) {
        await navigator.share({ files: [file], title: document.title, text: `${text} ${u}` });
        return;
      }
    } catch (err) { if (err.name === 'AbortError') return; }
    sheet(file, text, u);
  }

  function sheet(file, text, u) {
    document.querySelector('.sheet')?.remove();
    const img = file ? URL.createObjectURL(file) : null;
    const box = document.createElement('div');
    box.className = 'sheet';
    box.innerHTML = `<div class="sheet-card" role="dialog" aria-modal="true" aria-label="${t('Share', 'ಹಂಚಿಕೊಳ್ಳಿ')}">
        <button class="chip icon sheet-x" type="button" aria-label="${t('Close', 'ಮುಚ್ಚಿ')}">✕</button>
        <p class="sheet-title">${t('Share your result', 'ನಿಮ್ಮ ಫಲಿತಾಂಶ ಹಂಚಿಕೊಳ್ಳಿ')}</p>
        ${img ? `<img class="sheet-img" src="${img}" alt="${t('Your result card', 'ನಿಮ್ಮ ಫಲಿತಾಂಶ ಕಾರ್ಡ್')}">` : ''}
        <div class="actions">
          ${img ? `<a class="btn primary" href="${img}" download="${file.name}">${t('Save image', 'ಚಿತ್ರ ಉಳಿಸಿ')}</a>` : ''}
          <a class="btn" href="https://wa.me/?text=${encodeURIComponent(`${text} ${u}`)}" target="_blank" rel="noopener">WhatsApp ↗</a>
          <button class="btn" type="button" data-copy>${t('Copy link', 'ಲಿಂಕ್ ನಕಲಿಸಿ')}</button>
        </div>
        ${img ? `<p class="note">${t('Save the image, then attach it to your post or chat.', 'ಚಿತ್ರವನ್ನು ಉಳಿಸಿ, ನಂತರ ನಿಮ್ಮ ಪೋಸ್ಟ್ ಅಥವಾ ಚಾಟ್‌ಗೆ ಸೇರಿಸಿ.')}</p>` : ''}
      </div>`;
    const close = () => { box.remove(); if (img) URL.revokeObjectURL(img); document.removeEventListener('keydown', onKey); };
    const onKey = (e) => { if (e.key === 'Escape') close(); };
    box.addEventListener('click', (e) => { if (e.target === box) close(); });
    box.querySelector('.sheet-x').addEventListener('click', close);
    box.querySelector('[data-copy]').addEventListener('click', async (e) => {
      try { await navigator.clipboard.writeText(`${text} ${u}`); e.target.textContent = t('Copied ✓', 'ನಕಲಿಸಲಾಗಿದೆ ✓'); } catch { /* no clipboard */ }
    });
    document.addEventListener('keydown', onKey);
    document.body.appendChild(box);
    box.querySelector('.sheet-x').focus();
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
