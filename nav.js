/* Shared site nav — injected on every page. Links point at the home page's
   grouped sections (index.html#<section>); the current page's section is
   highlighted. On the full-viewport map apps (.app { height:100vh }) the nav
   shrinks the app to sit below it so nothing overflows. */
(function () {
  if (document.querySelector('nav.stnav')) return; // idempotent

  var LINKS = [
    ['Chronicle', 'chronicle'],
    ['Covenant', 'covenant'],
    ['Normandy Tribunal', 'tribunal'],
    ['Reference', 'reference'],
    ['Tools', 'tools'],
    ['Storyteller', 'storyteller', true] // gm-styled
  ];
  // which home section each page belongs to (for the active highlight)
  var PAGE_SECTION = {
    'sjorseidr_chronicle.html': 'chronicle', 'fleet_timeline.html': 'chronicle',
    'covenant.html': 'covenant', 'ships.html': 'covenant', 'xp_tracker.html': 'covenant',
    'normandy_tribunal_1223.html': 'tribunal', 'tribunal_workbook.html': 'tribunal',
    'normandy_tribunal_reference.html': 'tribunal',
    'hiberian.html': 'reference', 'reference.html': 'reference', 'integrating_magic.html': 'reference',
    'chargen.html': 'tools',
    'open_questions.html': 'storyteller', 'next_session_scenes.html': 'storyteller'
  };
  var here = (location.pathname.split('/').pop() || 'index.html');
  var active = PAGE_SECTION[here];
  var onHome = (here === 'index.html' || here === '');

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
    '.stnav a.gm.active{color:#f2c1b6;border-bottom-color:#b54a32}';
  var style = document.createElement('style');
  style.textContent = css;
  document.head.appendChild(style);

  var nav = document.createElement('nav');
  nav.className = 'stnav';
  var html = '<a class="stnav-brand" href="index.html">Sjórseiðr</a>';
  LINKS.forEach(function (l) {
    var cls = (l[2] ? 'gm' : '') + ((active === l[1]) ? ' active' : '');
    var href = onHome ? ('#' + l[1]) : ('index.html#' + l[1]);
    html += '<a class="' + cls.trim() + '" href="' + href + '">' + l[0] + '</a>';
  });
  nav.innerHTML = html;
  document.body.insertBefore(nav, document.body.firstChild);

  // Full-viewport flex apps (the map pages): shrink so the app fits under the nav.
  // The nav can wrap to 2 rows on narrow screens, and its height settles after
  // the webfont loads, so track it with a ResizeObserver rather than measuring once.
  var app = document.querySelector('.app');
  if (app && Math.abs(app.getBoundingClientRect().height - window.innerHeight) < 3) {
    var fit = function () {
      app.style.height = 'calc(100vh - ' + nav.offsetHeight + 'px)';
      window.dispatchEvent(new Event('resize')); // let the map re-fit to the new height
    };
    fit();
    if (window.ResizeObserver) { new ResizeObserver(fit).observe(nav); }
    else { window.addEventListener('resize', fit); }
    if (document.fonts && document.fonts.ready) { document.fonts.ready.then(fit); }
  }
})();
