/* Shared site nav — injected on content subpages, driven by sitemap.json so it
   can never drift from the home page / section landings. A section with a
   top-level "href" is a direct nav item (its link goes straight to that page);
   otherwise the link points at its section landing (section.html?sec=<id>).
   The current page's section is highlighted by matching the filename against
   each section's href or its cards' hrefs.

   Some page pairs get an in-page toggle rendered as a second row inside the nav
   (Chronicle of Events <-> Fleet Voyages, Covenant Sheet <-> XP Tracker). It
   lives inside nav.stnav so the .app fit math (which subtracts nav.offsetHeight)
   stays correct on the full-viewport map pages.

   On the full-viewport map apps (.app { height:100vh }) the nav shrinks the app
   to sit below it so nothing overflows. */
(function () {
  if (document.querySelector('nav.stnav')) return; // idempotent

  var here = (location.pathname.split('/').pop() || 'index.html');

  // In-page pair toggles, keyed by filename. Each entry lists the two members
  // (in display order); the current page's button renders active, the other links.
  var PAIRS = {
    'sjorseidr_chronicle.html': 'chronicle', 'fleet_timeline.html': 'chronicle',
    'covenant_ledger.html': 'covenant', 'xp_tracker.html': 'covenant'
  };
  var PAIR_MEMBERS = {
    chronicle: [
      { href: 'sjorseidr_chronicle.html', label: 'Chronicle of Events', icon: '📖' },
      { href: 'fleet_timeline.html', label: 'Fleet Voyages by Season', icon: '🚢' }
    ],
    covenant: [
      { href: 'covenant_ledger.html', label: 'Covenant Sheet', icon: '🏛️' },
      { href: 'xp_tracker.html', label: 'XP Tracker', icon: '📈' }
    ]
  };

  var css =
    '.stnav{position:sticky;top:0;z-index:1000;display:flex;flex-wrap:wrap;align-items:center;gap:2px;' +
      'padding:8px 16px;background:rgba(56,38,18,.92);-webkit-backdrop-filter:blur(5px);backdrop-filter:blur(5px);' +
      'border-bottom:2px solid #6b5436;box-shadow:0 2px 12px rgba(50,32,12,.45);' +
      "font-family:'Cinzel','Trajan Pro',Georgia,serif}" +
    '.stnav .stnav-brand{font-weight:600;letter-spacing:.06em;color:#c69b3f;margin-right:auto;font-size:14.5px;text-decoration:none}' +
    '.stnav .stnav-brand::before{content:"\\2693";margin-right:.45em;color:#b54a32;font-size:.85em}' +
    '.stnav a{font-size:12.5px;letter-spacing:.04em;color:#e9d8b2;text-decoration:none;padding:6px 11px;' +
      'border-radius:6px;border-bottom:2px solid transparent;transition:.15s}' +
    '.stnav a:hover{color:#fff6df;background:rgba(255,255,255,.07)}' +
    '.stnav a.active{color:#fff6df;border-bottom-color:#c69b3f}' +
    '.stnav a.gm{color:#e2a99c}' +
    '.stnav a.gm::before{content:"\\2694 "}' +
    '.stnav a.gm:hover{color:#f2c1b6}' +
    '.stnav a.gm.active{color:#f2c1b6;border-bottom-color:#b54a32}' +
    /* pair toggle: full-width second row inside the nav */
    '.stnav .stnav-toggle{flex-basis:100%;display:flex;justify-content:center;gap:0;' +
      'margin:7px 0 1px;padding-top:8px;border-top:1px solid rgba(198,155,63,.28)}' +
    '.stnav .stnav-toggle .seg{display:inline-flex;border:1px solid #6b5436;border-radius:8px;overflow:hidden;' +
      'box-shadow:0 1px 6px rgba(50,32,12,.35)}' +
    '.stnav .stnav-toggle a,.stnav .stnav-toggle span{font-size:12px;letter-spacing:.03em;padding:6px 15px;' +
      'border:0;border-radius:0;border-bottom:0;color:#e9d8b2;text-decoration:none;background:rgba(30,20,8,.35);' +
      'display:inline-flex;align-items:center;gap:.4em;transition:.15s}' +
    '.stnav .stnav-toggle a+a,.stnav .stnav-toggle a+span,.stnav .stnav-toggle span+a{border-left:1px solid #6b5436}' +
    '.stnav .stnav-toggle a:hover{background:rgba(255,255,255,.08);color:#fff6df}' +
    '.stnav .stnav-toggle .cur{background:#c69b3f;color:#2a1c0a;font-weight:600;cursor:default}';
  var style = document.createElement('style');
  style.textContent = css;
  document.head.appendChild(style);

  var nav = document.createElement('nav');
  nav.className = 'stnav';
  nav.innerHTML = '<a class="stnav-brand" href="index.html">Sjórseiðr</a>';
  document.body.insertBefore(nav, document.body.firstChild);

  function fitApp() {
    var app = document.querySelector('.app');
    if (app && Math.abs(app.getBoundingClientRect().height - window.innerHeight) < 3 + nav.offsetHeight) {
      var fit = function () {
        app.style.height = 'calc(100vh - ' + nav.offsetHeight + 'px)';
        window.dispatchEvent(new Event('resize')); // let the map re-fit to the new height
      };
      fit();
      if (window.ResizeObserver) { new ResizeObserver(fit).observe(nav); }
      else { window.addEventListener('resize', fit); }
      if (document.fonts && document.fonts.ready) { document.fonts.ready.then(fit); }
    }
  }

  function esc(s){ return (s==null?'':String(s)).replace(/[&<>"']/g, function(c){ return ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'})[c]; }); }

  function render(sections) {
    // active section: the one whose href, or one of whose card hrefs, is this page
    var active = null;
    sections.forEach(function (s) {
      if (s.href === here) active = s.id;
      (s.cards || []).forEach(function (c) { if (c.href === here) active = active || s.id; });
    });

    var html = '';
    sections.forEach(function (s) {
      var cls = (s.gm ? 'gm' : '') + ((active === s.id) ? ' active' : '');
      var href = s.href ? s.href : 'section.html?sec=' + encodeURIComponent(s.id);
      html += '<a class="' + cls.trim() + '" href="' + esc(href) + '">' + esc(s.title) + '</a>';
    });

    // in-page pair toggle (second row)
    var pairId = PAIRS[here];
    if (pairId && PAIR_MEMBERS[pairId]) {
      var seg = PAIR_MEMBERS[pairId].map(function (m) {
        if (m.href === here) return '<span class="cur">' + esc(m.icon) + ' ' + esc(m.label) + '</span>';
        return '<a href="' + esc(m.href) + '">' + esc(m.icon) + ' ' + esc(m.label) + '</a>';
      }).join('');
      html += '<div class="stnav-toggle"><div class="seg">' + seg + '</div></div>';
    }

    nav.insertAdjacentHTML('beforeend', html);
    fitApp();
  }

  fetch('./sitemap.json', { cache: 'no-store' })
    .then(function (r) { return r.json(); })
    .then(function (map) { render(map.sections || []); })
    .catch(function () {
      // Fallback: sitemap unavailable (e.g. file://). Render a minimal static nav
      // so the page is still navigable; keeps direct links + the pair toggle.
      render([
        { id: 'chronicle', title: 'Chronicle', href: 'sjorseidr_chronicle.html', cards: [{ href: 'fleet_timeline.html' }] },
        { id: 'dramatis', title: 'Dramatis Personae', href: 'dramatis_personae.html' },
        { id: 'covenant', title: 'Covenant', href: 'covenant_ledger.html', cards: [{ href: 'xp_tracker.html' }] },
        { id: 'reference', title: 'Reference' },
        { id: 'tools', title: 'Tools' },
        { id: 'storyteller', title: 'Storyteller', gm: true }
      ]);
    });
})();
