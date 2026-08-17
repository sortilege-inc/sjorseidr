/* Storyteller rail — a sticky table-of-contents down the left margin of the
   two Storyteller pages (Open Questions, Next-Session Scenes). It links the
   whole Storyteller area: the two pages, plus the Open-Questions type views.
   On Open Questions the type links switch the view in-place (via window.stSetType);
   from the Scenes page they deep-link with ?type=. Hidden when the window is
   too narrow to hold a rail beside the centred column. */
(function () {
  if (document.querySelector('.st-rail')) return;
  var here = (location.pathname.split('/').pop() || '');
  var onOQ = here === 'open_questions.html';
  var onNS = here === 'next_session_scenes.html';
  if (!onOQ && !onNS) return;

  var TYPES = [
    ['all', 'All', '▦'], ['Question', 'Questions', '❓'], ['Thread', 'Threads', '🧵'],
    ['Consequence', 'Consequences', '⚖️'], ['Tool', 'Tools', '🔧'], ['reference', 'GM Reference', '📚']
  ];

  var css =
    '.st-rail{position:fixed;top:74px;left:calc(50% - 640px);width:160px;z-index:900;' +
      "font-family:'Cinzel','Trajan Pro',Georgia,serif;" +
      'background:linear-gradient(180deg,#f1e6c9,#e4d3a8);border:1.5px solid rgba(120,90,40,.45);' +
      'border-radius:10px;box-shadow:0 3px 10px rgba(50,32,12,.3);padding:11px 10px 12px;max-height:calc(100vh - 92px);overflow-y:auto}' +
    '.st-rail .str-title{font-size:11px;letter-spacing:.06em;text-transform:uppercase;color:#8a3324;' +
      'border-bottom:1px solid rgba(120,90,40,.35);padding-bottom:6px;margin-bottom:7px}' +
    '.st-rail .str-page{display:block;font-size:12.5px;letter-spacing:.02em;color:#4a3c2c;text-decoration:none;' +
      'padding:6px 7px;border-radius:6px;border-left:3px solid transparent}' +
    '.st-rail .str-page:hover{background:rgba(198,155,63,.16);color:#221a12}' +
    '.st-rail .str-page.cur{color:#8a3324;border-left-color:#b54a32;font-weight:600;background:rgba(181,74,50,.08)}' +
    '.st-rail .str-subs{margin:2px 0 8px 6px;display:flex;flex-direction:column;gap:1px;' +
      'border-left:1px dotted rgba(120,90,40,.4);padding-left:5px}' +
    '.st-rail .str-sub{font-family:"EB Garamond",Georgia,serif;font-size:12.5px;color:#4a3c2c;text-decoration:none;' +
      'padding:3px 7px;border-radius:5px;display:flex;align-items:center;gap:6px}' +
    '.st-rail .str-sub:hover{background:rgba(198,155,63,.16);color:#221a12}' +
    '.st-rail .str-sub.on{background:rgba(154,107,31,.16);color:#8a3324;font-weight:600}' +
    '.st-rail .str-sub.disabled{opacity:.5;pointer-events:none}' +
    '@media (max-width:1279px){.st-rail{display:none}}';
  var style = document.createElement('style');
  style.textContent = css;
  document.head.appendChild(style);

  var subs = TYPES.map(function (t) {
    var href = onOQ ? ('#' + t[0]) : ('open_questions.html?type=' + t[0]);
    return '<a class="str-sub" data-type="' + t[0] + '" href="' + href + '"><span>' + t[2] + '</span>' + t[1] + '</a>';
  }).join('');

  var nav = document.createElement('nav');
  nav.className = 'st-rail';
  nav.innerHTML =
    '<div class="str-title">⚔ Storyteller</div>' +
    '<a class="str-page ' + (onOQ ? 'cur' : '') + '" href="open_questions.html">❓ Open Questions</a>' +
    '<div class="str-subs">' + subs + '</div>' +
    '<a class="str-page ' + (onNS ? 'cur' : '') + '" href="next_session_scenes.html">🎬 Next-Session Scenes</a>';
  document.body.appendChild(nav);

  function highlight(t) {
    nav.querySelectorAll('.str-sub').forEach(function (x) { x.classList.toggle('on', x.dataset.type === t); });
  }
  window.stRailHighlight = highlight;

  if (onOQ) {
    nav.querySelectorAll('.str-sub').forEach(function (a) {
      a.addEventListener('click', function (e) {
        if (window.stSetType) { e.preventDefault(); window.stSetType(a.dataset.type); }
      });
    });
    var initial = new URLSearchParams(location.search).get('type');
    if (!initial && window.stGetType) initial = window.stGetType();
    highlight(initial || 'all');
  }
})();
