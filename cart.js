/* Panini Store — carrinho (localStorage) compartilhado por todas as páginas.
   - Liga botões com [data-add-to-cart] (data-slug, data-name, data-price, data-img, data-variant)
   - Lê a quantidade de #pdp-qty quando existir
   - Mostra um contador no ícone de carrinho do header (.iconP_grocery_cart) e o leva ao checkout
   - O checkout.html lê o mesmo carrinho (chave 'paniniCart') */
(function () {
  var KEY = 'paniniCart';

  function read() { try { return JSON.parse(localStorage.getItem(KEY)) || []; } catch (e) { return []; } }
  function write(c) { localStorage.setItem(KEY, JSON.stringify(c)); refresh(); }
  function count() { return read().reduce(function (s, i) { return s + (parseInt(i.qty) || 1); }, 0); }

  function add(item) {
    var c = read(), found = null;
    for (var k = 0; k < c.length; k++) {
      if (c[k].slug === item.slug && (c[k].variant || '') === (item.variant || '')) { found = c[k]; break; }
    }
    if (found) found.qty = (parseInt(found.qty) || 1) + (parseInt(item.qty) || 1);
    else c.push(item);
    write(c);
  }

  function refresh() {
    var n = count();
    // ícone de carrinho do header (Panini)
    var icons = document.querySelectorAll('.iconP_grocery_cart');
    for (var i = 0; i < icons.length; i++) {
      var span = icons[i], a = span.closest ? span.closest('a') : null;
      if (a) {
        a.setAttribute('href', 'checkout.html');
        a.removeAttribute('onclick'); a.onclick = null;
        a.style.cursor = 'pointer';
        a.setAttribute('aria-label', 'Cart (' + n + ' items)');
      }
      var badge = span.querySelector('.cart-badge');
      if (!badge) {
        badge = document.createElement('sup');
        badge.className = 'cart-badge';
        badge.style.cssText = 'position:absolute;top:-7px;right:-9px;background:#e3000f;color:#fff;' +
          'font:700 10px/16px sans-serif;min-width:16px;height:16px;border-radius:8px;text-align:center;padding:0 3px;';
        span.appendChild(badge);
      }
      badge.textContent = n;
      badge.style.display = n > 0 ? '' : 'none';
    }
    var holders = document.querySelectorAll('[data-cart-count]');
    for (var j = 0; j < holders.length; j++) holders[j].textContent = n;
  }

  function toast(text) {
    var t = document.createElement('div');
    t.textContent = text;
    t.style.cssText = 'position:fixed;z-index:99999;left:50%;bottom:28px;transform:translateX(-50%);' +
      'background:#111;color:#fff;padding:12px 22px;border-radius:8px;font:600 14px sans-serif;' +
      'box-shadow:0 4px 20px rgba(0,0,0,.25);opacity:0;transition:opacity .2s;';
    document.body.appendChild(t);
    requestAnimationFrame(function () { t.style.opacity = '1'; });
    setTimeout(function () { t.style.opacity = '0'; setTimeout(function () { t.remove(); }, 250); }, 1700);
  }

  function wire() {
    var btns = document.querySelectorAll('[data-add-to-cart]');
    for (var i = 0; i < btns.length; i++) {
      (function (btn) {
        if (btn._cartWired) return; btn._cartWired = true;
        btn.addEventListener('click', function (e) {
          e.preventDefault();
          var qtyEl = document.getElementById(btn.getAttribute('data-qty') || 'pdp-qty');
          var qty = qtyEl ? Math.max(1, parseInt(qtyEl.value) || 1) : 1;
          add({
            slug: btn.getAttribute('data-slug'),
            name: btn.getAttribute('data-name'),
            price: parseFloat(btn.getAttribute('data-price')) || 0,
            img: btn.getAttribute('data-img') || '',
            variant: btn.getAttribute('data-variant') || '',
            qty: qty
          });
          if (window.Track) Track.addToCart({ id: btn.getAttribute('data-slug'), name: btn.getAttribute('data-name'), value: (parseFloat(btn.getAttribute('data-price')) || 0) * qty });
          // add-ons marcados em "You might also like these"
          var ups = document.querySelectorAll('.upsell-item'), extra = 0;
          for (var u = 0; u < ups.length; u++) {
            var it = ups[u], cb = it.querySelector('.up-check');
            if (cb && cb.checked) {
              var sel = it.querySelector('.up-variant');
              add({
                slug: it.getAttribute('data-slug'),
                name: it.getAttribute('data-name'),
                price: parseFloat(it.getAttribute('data-price')) || 0,
                img: it.getAttribute('data-img') || '',
                variant: sel ? sel.value : '',
                qty: 1
              });
              cb.checked = false; extra++;
            }
          }
          if (btn.hasAttribute('data-buy-now')) { location.href = 'checkout.html'; return; }
          toast(extra ? ('✓ Added ' + (extra + 1) + ' items to cart') : '✓ Added to cart');
        });
      })(btns[i]);
    }
    refresh();
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', wire);
  else wire();
  window.PaniniCart = { add: add, read: read, write: write, count: count, refresh: refresh };
})();
