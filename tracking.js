/* Panini Store — tracking (Facebook Pixel + dedup com Conversions API + UTMify)
   IDs de pixel são públicos (front-end). Tokens secretos ficam no Supabase. */
(function () {
  var FB_PIXEL_ID = '28181409881448447';
  var UTMIFY_PIXEL_ID = '6a2f3103c73734b77d230cfe';

  /* ---------------- Facebook Pixel ---------------- */
  !function (f, b, e, v, n, t, s) {
    if (f.fbq) return; n = f.fbq = function () { n.callMethod ? n.callMethod.apply(n, arguments) : n.queue.push(arguments); };
    if (!f._fbq) f._fbq = n; n.push = n; n.loaded = !0; n.version = '2.0'; n.queue = [];
    t = b.createElement(e); t.async = !0; t.src = v; s = b.getElementsByTagName(e)[0]; s.parentNode.insertBefore(t, s);
  }(window, document, 'script', 'https://connect.facebook.net/en_US/fbevents.js');
  fbq('init', FB_PIXEL_ID);
  fbq('track', 'PageView');

  /* ---------------- UTMify (captura de UTM + pixel) ---------------- */
  var u = document.createElement('script');
  u.src = 'https://cdn.utmify.com.br/scripts/utms/latest.js';
  u.setAttribute('data-utmify-prevent-xcod-sck', '');
  u.setAttribute('data-utmify-prevent-subids', '');
  u.async = true; u.defer = true; document.head.appendChild(u);
  window.pixelId = UTMIFY_PIXEL_ID;
  var pp = document.createElement('script');
  pp.async = true; pp.defer = true;
  pp.src = 'https://cdn.utmify.com.br/scripts/pixel/pixel.js';
  document.head.appendChild(pp);

  /* ---------------- captura/persistência de UTMs ---------------- */
  (function () {
    var q = new URLSearchParams(location.search);
    var keys = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term', 'fbclid', 'gclid', 'src', 'sck'];
    var got = {}, has = false;
    keys.forEach(function (k) { var v = q.get(k); if (v) { got[k] = v; has = true; } });
    if (has) { try { localStorage.setItem('paniniUTM', JSON.stringify(got)); } catch (e) {} }
  })();
  function cookie(n) { var m = document.cookie.match('(^|;)\\s*' + n + '\\s*=\\s*([^;]+)'); return m ? decodeURIComponent(m.pop()) : ''; }
  function getUTMs() {
    var u = {};
    try { u = JSON.parse(localStorage.getItem('paniniUTM')) || {}; } catch (e) {}
    var fbp = cookie('_fbp'), fbc = cookie('_fbc');   // cookies do Pixel -> match exato no servidor
    if (fbp) u.fbp = fbp;
    if (fbc) u.fbc = fbc;
    return u;
  }

  /* ---------------- helpers de evento ---------------- */
  window.Track = {
    viewContent: function (o) {
      if (window.fbq) fbq('track', 'ViewContent', { content_ids: [o.id], content_name: o.name, content_type: 'product', value: o.value, currency: 'USD' });
    },
    addToCart: function (o) {
      if (window.fbq) fbq('track', 'AddToCart', { content_ids: [o.id], content_name: o.name, content_type: 'product', value: o.value, currency: 'USD' });
    },
    initiateCheckout: function (o) {
      if (window.fbq) fbq('track', 'InitiateCheckout', { value: o.value, currency: 'USD', num_items: o.num_items, content_ids: o.ids || [], content_type: 'product' });
    },
    purchase: function (o) {
      if (window.fbq) fbq('track', 'Purchase', { value: o.value, currency: 'USD', content_ids: o.ids || [], content_type: 'product' }, { eventID: o.eventID });
    },
    getUTMs: getUTMs
  };

  /* ViewContent automático nas páginas de produto */
  if (window.__PRODUCT__) Track.viewContent(window.__PRODUCT__);
})();
