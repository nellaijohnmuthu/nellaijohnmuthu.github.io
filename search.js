/* Panchayat directory: search with highlighting, transliteration aliases,
   category filters, URL state and share links. No dependencies. */
(function () {
  var q = document.getElementById('q');
  if (!q) return;

  var note = document.getElementById('note'),
      empty = document.getElementById('empty'),
      clear = document.getElementById('clear'),
      typeChips = [].slice.call(document.querySelectorAll('.chip[data-f]')),
      catChips = [].slice.call(document.querySelectorAll('.cat-chip')),
      items = [].slice.call(document.querySelectorAll('.lb')),
      groups = [].slice.call(document.querySelectorAll('.lb-group')),
      type = 'all', cat = '';

  var SYN = {
    'தண்ணீர்': 'குடிநீர்', 'water': 'குடிநீர்', 'drinking water': 'குடிநீர்',
    'drain': 'வடிகால்', 'drainage': 'வடிகால்', 'road': 'சாலை', 'street light': 'தெருவிளக்கு',
    'school': 'பள்ளி', 'patta': 'பட்டா', 'tank': 'தொட்டி', 'bus': 'பேருந்து'
  };

  function norm(s) {
    return (s || '').normalize('NFC').toLowerCase().replace(/\s+/g, ' ').trim();
  }

  // cache the searchable text and the original HTML of every issue line
  items.forEach(function (el) {
    el.dataset.hay = norm(el.textContent + ' ' + (el.dataset.alias || ''));
    [].forEach.call(el.querySelectorAll('.cat li'), function (li) { li.dataset.orig = li.innerHTML; });
  });

  function unmark(el) {
    [].forEach.call(el.querySelectorAll('.cat li'), function (li) {
      if (li.innerHTML !== li.dataset.orig) li.innerHTML = li.dataset.orig;
    });
  }

  function mark(el, term) {
    var re;
    try { re = new RegExp('(' + term.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + ')', 'gi'); }
    catch (e) { return; }
    [].forEach.call(el.querySelectorAll('.cat li'), function (li) {
      var t = li.dataset.orig;
      if (t.toLowerCase().indexOf(term) > -1) li.innerHTML = t.replace(re, '<mark>$1</mark>');
    });
  }

  function apply(push) {
    var raw = norm(q.value), term = SYN[raw] ? norm(SYN[raw]) : raw,
        shownBodies = 0, shownIssues = 0;

    items.forEach(function (el) {
      var okType = type === 'all' || el.dataset.type === type;
      var okCat = !cat || el.querySelector('.cat[data-c="' + cat + '"]');
      var okText = !term || el.dataset.hay.indexOf(term) > -1;
      var vis = okType && okCat && okText;
      el.hidden = !vis;
      unmark(el);

      // show only the chosen category inside an open body
      [].forEach.call(el.querySelectorAll('.cat'), function (c) {
        c.hidden = !!cat && c.dataset.c !== cat;
      });

      if (vis) {
        shownBodies++;
        var lis = [].slice.call(el.querySelectorAll('.cat:not([hidden]) li'));
        shownIssues += lis.length;
        if (term) { mark(el, term); el.open = true; }
        else if (!location.hash) { el.open = false; }
      }
    });

    groups.forEach(function (g) { g.hidden = !g.querySelector('.lb:not([hidden])'); });
    empty.hidden = shownBodies > 0;

    var active = term || cat || type !== 'all';
    clear.hidden = !active;
    note.textContent = active
      ? shownIssues + ' பதிவு · ' + shownBodies + ' உள்ளாட்சி அமைப்பு'
      : '';

    if (push) {
      var p = new URLSearchParams();
      if (raw) p.set('q', q.value.trim());
      if (type !== 'all') p.set('type', type);
      if (cat) p.set('cat', cat);
      var url = location.pathname + (p.toString() ? '?' + p : '');
      history.replaceState(null, '', url);
    }
  }

  function readURL() {
    var p = new URLSearchParams(location.search);
    q.value = p.get('q') || '';
    type = p.get('type') || 'all';
    cat = p.get('cat') || '';
    typeChips.forEach(function (c) { c.setAttribute('aria-pressed', String(c.dataset.f === type)); });
    catChips.forEach(function (c) { c.setAttribute('aria-pressed', String(c.dataset.c === cat)); });
  }

  q.addEventListener('input', function () { apply(true); });
  typeChips.forEach(function (c) {
    c.addEventListener('click', function () {
      type = c.dataset.f;
      typeChips.forEach(function (o) { o.setAttribute('aria-pressed', String(o === c)); });
      apply(true);
    });
  });
  catChips.forEach(function (c) {
    c.addEventListener('click', function () {
      cat = (cat === c.dataset.c) ? '' : c.dataset.c;
      catChips.forEach(function (o) { o.setAttribute('aria-pressed', String(o.dataset.c === cat)); });
      apply(true);
    });
  });
  clear.addEventListener('click', function () {
    q.value = ''; type = 'all'; cat = '';
    typeChips.forEach(function (o) { o.setAttribute('aria-pressed', String(o.dataset.f === 'all')); });
    catChips.forEach(function (o) { o.setAttribute('aria-pressed', 'false'); });
    apply(true); q.focus();
  });

  // category chips inside an open village jump to that filter
  document.addEventListener('click', function (e) {
    var m = e.target.closest('.minicat');
    if (!m) return;
    e.preventDefault(); e.stopPropagation();
    cat = m.dataset.c;
    catChips.forEach(function (o) { o.setAttribute('aria-pressed', String(o.dataset.c === cat)); });
    apply(true);
    document.querySelector('.cat-filters').scrollIntoView({ block: 'center' });
  });

  // share a single village
  document.addEventListener('click', function (e) {
    var b = e.target.closest('.sharebtn');
    if (!b) return;
    e.preventDefault();
    var url = location.origin + location.pathname + '#' + b.dataset.slug;
    var data = { title: b.dataset.name, text: b.dataset.name + ' — களப் பிரச்சினைகள்', url: url };
    if (navigator.share) { navigator.share(data).catch(function () {}); return; }
    var done = function () { b.textContent = 'இணைப்பு நகலெடுக்கப்பட்டது'; setTimeout(function () { b.textContent = 'இந்தப் பட்டியலைப் பகிர'; }, 2500); };
    if (navigator.clipboard) navigator.clipboard.writeText(url).then(done, function () {});
    else { prompt('இணைப்பு:', url); }
  });

  readURL();
  apply(false);

  // open and scroll to a deep-linked village
  if (location.hash) {
    var el = document.getElementById(location.hash.slice(1));
    if (el && el.classList.contains('lb')) {
      el.open = true;
      setTimeout(function () { el.scrollIntoView({ block: 'start' }); }, 60);
    }
  }
})();
