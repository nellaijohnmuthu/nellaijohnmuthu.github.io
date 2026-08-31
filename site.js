/* Mobile menu — used on every page */
(function () {
  var btn = document.getElementById('menuBtn'), nav = document.getElementById('mainnav');
  if (!btn || !nav) return;
  function set(open) {
    btn.setAttribute('aria-expanded', String(open));
    nav.classList.toggle('open', open);
  }
  btn.addEventListener('click', function () {
    set(btn.getAttribute('aria-expanded') !== 'true');
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && btn.getAttribute('aria-expanded') === 'true') { set(false); btn.focus(); }
  });
})();
