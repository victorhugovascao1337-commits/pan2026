# -*- coding: utf-8 -*-
"""Generate local product-detail pages (akgstore products) that reuse the
Panini offline site's head/header/footer, replicating the full akgstore
description layout (How It Works, Collecting Experience stats, feature row,
and customer reviews). Also repoints the FIFA grid cards at these pages."""
import io, re, json

FIFA = r"C:\Users\Vetz\Desktop\panini-offline\fifa-world-cup-2026.html"
IMG = "./assets-fifa/"

src = io.open(FIFA, "r", encoding="utf-8", errors="replace").read()
hclose = src.index("</header>") + len("</header>")
PREFIX = src[:hclose]
SUFFIX = src[src.index("<footer"):]


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

# ---------------------------------------------------------------- shared blocks
STAR = ('<svg viewBox="0 0 24 24" fill="currentColor" width="18" height="18">'
        '<path d="M12 2l2.9 6.3 6.9.8-5.1 4.7 1.4 6.8L12 18l-6 3.4 1.4-6.8L2.3 9.1l6.9-.8z"/></svg>')
STARS = '<div class="text-warning mb-2" aria-label="5 out of 5 stars">' + STAR * 5 + '</div>'

ICON_TRUCK = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" width="44" height="44">'
              '<rect x="2.5" y="6.5" width="11" height="9" rx="1"/><path d="M13.5 9.5h3.5l3 3v3h-6.5z"/>'
              '<circle cx="7" cy="18" r="1.7"/><circle cx="17.5" cy="18" r="1.7"/></svg>')
ICON_COMPASS = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" width="44" height="44">'
                '<circle cx="12" cy="4.6" r="1.7"/><path d="M11 6.2 4.5 20"/><path d="M13 6.2 19.5 20"/><path d="M8.3 14h7.4"/></svg>')
ICON_LOCK = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" width="44" height="44">'
             '<rect x="4.5" y="10" width="15" height="10.5" rx="2"/><path d="M8 10V7a4 4 0 0 1 8 0v3"/>'
             '<circle cx="12" cy="15" r="1.3"/></svg>')
ICON_AWARD = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" width="44" height="44">'
              '<circle cx="12" cy="8.5" r="5"/><path d="M8.6 12.8 7 21l5-2.6L17 21l-1.6-8.2"/></svg>')

FEATURES = [(ICON_TRUCK, "Free Shipping"), (ICON_COMPASS, "Seamless Modern Design"),
            (ICON_LOCK, "Secure Payment"), (ICON_AWARD, "Premium Quality")]

STATS = [
    ("98%", "Enjoyed the excitement of opening packs and discovering new stickers."),
    ("96%", u"Said collecting brought them closer to the FIFA World Cup™ experience."),
    ("95%", "Loved trading duplicates with friends and fellow collectors."),
    ("94%", "Considered the completed album a memorable keepsake of the tournament."),
]

STEPS = [
    ("1. Collect Official Stickers",
     u"Each pack contains officially licensed stickers featuring players, teams, stadiums, emblems, and special moments from the FIFA World Cup™ 2026."),
    ("2. Fill Your Album",
     "Place your stickers in the official album and watch the tournament come to life page by page as your collection grows."),
    ("3. Trade & Complete Your Collection",
     "Exchange duplicate stickers with friends, family, and fellow collectors to complete your album and find the rare stickers you need."),
    ("4. Celebrate Football's Biggest Event",
     u"The collection captures the excitement, passion, and history of the FIFA World Cup™, making it a keepsake that can be enjoyed long after the tournament ends."),
]

REVIEWS = [
    ("akg_rev1.png", "Perfect for World Cup Fans!",
     u"I bought this collection for my son, and we have been opening packs together every evening. The hardcover album is excellent quality, and the stickers look amazing. It's a great way to enjoy the excitement leading up to the FIFA World Cup™. Highly recommended for collectors of all ages!",
     "Robert S."),
    ("akg_rev2.webp", "Fantastic Collector's Item",
     "The stickers are vibrant, well-designed, and feature many of the world's biggest football stars. The album is sturdy and beautifully made. Having multiple boxes gave me a great start toward completing the collection. Definitely worth it for any football fan.",
     "Gabriel R."),
    ("akg_rev3.jpg", "Brings Back Great Memories",
     u"As someone who has collected Panini stickers since childhood, this collection exceeded my expectations. Opening packs, finding special stickers, and trading duplicates with friends has been so much fun. The hardcover album makes it feel like a premium collector's edition that I'll keep for years. \U0001F389⚽\U0001F30D",
     "Daniel L."),
]


def build_rich():
    # Intro
    intro = (
        '<div class="text-center mb-5">'
        '<h2 class="ff_akira_bold text-uppercase fs-2 text-neutral-900 mb-3">Officially Licensed FIFA World Cup&trade; Collection</h2>'
        '<p class="ff_made fs-5 text-neutral-900 mx-auto" style="max-width:820px;">As the world&#39;s leading sticker publisher, '
        'Panini has been creating iconic football collections for generations. The 2026 FIFA World Cup&trade; Official Sticker '
        'Collection features officially licensed stickers showcasing national teams, star players, and tournament moments.</p></div>'
    )
    # How it works (text left, image right)
    steps = ""
    for title, body in STEPS:
        steps += ('<h3 class="ff_akira_bold text-uppercase fs-4 text-neutral-900 mt-4 mb-2">%s</h3>'
                  '<p class="ff_made fs-6 text-neutral-900 mb-0">%s</p>') % (esc(title), esc(body))
    howit = (
        '<div class="row align-items-center g-4 g-lg-5 mb-5 py_spacer">'
        '<div class="col-12 col-lg-6">'
        '<h2 class="ff_akira_bold text-uppercase fs-2 text-neutral-900 mb-3">How It Works</h2>'
        '<p class="ff_made fs-5 text-neutral-900 mb-1">Experience the excitement of collecting and completing the official FIFA World Cup&trade; sticker album.</p>'
        '<p class="ff_made fs-6 text-neutral-900">Here&#39;s what happens:</p>%s</div>'
        '<div class="col-12 col-lg-6 text-center"><div class="bg-black rounded-3 p-3 p-lg-4">'
        '<img src="%sakg_collectorbox.webp" alt="FIFA World Cup 2026 Collector\'s Box - 1000+ stickers inside" class="img-fluid rounded-2"></div></div>'
        '</div>'
    ) % (steps, IMG)
    # Stats (stats left, heading right)
    stat_rows = ""
    for pct, txt in STATS:
        stat_rows += (
            '<div class="d-flex align-items-center py-3 border-bottom">'
            '<span class="ff_akira_bold fs-1 text-neutral-900 me-4" style="min-width:90px;">%s</span>'
            '<span class="ff_made fs-6 text-neutral-900">%s</span></div>'
        ) % (esc(pct), esc(txt))
    stats = (
        '<div class="rounded-4 bg-primary-50 p-4 p-lg-5 mb-5"><div class="row align-items-center g-4">'
        '<div class="col-12 col-lg-7">%s</div>'
        '<div class="col-12 col-lg-5 text-center text-lg-end">'
        '<h2 class="ff_akira_bold text-uppercase display-5 text-neutral-900 mb-0">The FIFA World Cup&trade; Collecting Experience</h2>'
        '</div></div></div>'
    ) % stat_rows
    # Features
    cells = ""
    for svg, label in FEATURES:
        cells += ('<div class="col-6 col-lg-3 text-center mb-4"><div class="text-neutral-900 mb-2">%s</div>'
                  '<p class="ff_akira_bold text-uppercase fs-6 text-neutral-900 mb-0">%s</p></div>') % (svg, esc(label))
    features = '<div class="row justify-content-center align-items-start py-4 mb-4 border-top border-bottom">%s</div>' % cells
    # Reviews
    cards = ""
    for img, title, body, author in REVIEWS:
        cards += (
            '<div class="col-12 col-md-4 mb-4"><div class="bg-primary-50 rounded-3 h-100 overflow-hidden d-flex flex-column">'
            '<img src="%s%s" alt="Customer photo - %s" class="w-100" style="height:230px;object-fit:cover;">'
            '<div class="p-4 d-flex flex-column flex-grow-1">%s'
            '<h3 class="ff_akira_bold text-uppercase fs-5 text-neutral-900 mb-2">%s</h3>'
            '<p class="ff_made fs-6 text-neutral-900 flex-grow-1">%s</p>'
            '<p class="ff_made_medium fs-6 text-neutral-900 mb-0 mt-2"><em>%s</em></p></div></div></div>'
        ) % (IMG, img, esc(author), STARS, esc(title), esc(body), esc(author))
    reviews = ('<div class="py_spacer"><h2 class="ff_akira_bold text-uppercase fs-2 text-neutral-900 text-center mb-4">What Collectors Are Saying</h2>'
               '<div class="row">%s</div></div>') % cards

    return ('<section class="container py-5 mt-4 border-top">%s%s%s%s%s</section>'
            % (intro, howit, stats, features, reviews))


RICH = build_rich()

# ------------------------------------------------------ styles, accordion, carousel
STYLE = (
    "<style>"
    ".pdp-acc>summary{list-style:none;cursor:pointer;display:flex;align-items:center;"
    "justify-content:space-between;padding:1rem 0;}"
    ".pdp-acc>summary::-webkit-details-marker{display:none}"
    ".pdp-acc>summary::after{content:'';width:.6rem;height:.6rem;border-right:2px solid #14142b;"
    "border-bottom:2px solid #14142b;transform:rotate(45deg);transition:transform .2s;flex:0 0 auto;margin-left:1rem}"
    ".pdp-acc[open]>summary::after{transform:rotate(-135deg)}"
    ".acc-icon{width:48px;height:48px;flex:0 0 auto}"
    "#relScroller{scrollbar-width:none;-ms-overflow-style:none;scroll-snap-type:x mandatory}"
    "#relScroller::-webkit-scrollbar{display:none}"
    ".rel-nav{position:absolute;top:40%;z-index:5;width:46px;height:46px;border-radius:50%;background:#fff;"
    "border:0;box-shadow:0 2px 14px rgba(0,0,0,.18);display:flex;align-items:center;justify-content:center}"
    ".rel-prev{left:-12px}.rel-next{right:-12px}"
    ".rel-card{width:300px;flex:0 0 auto;scroll-snap-align:start}"
    ".upsell{background:#f4f5f7;border-radius:12px;padding:16px;}"
    ".upsell-title{font-weight:700;text-transform:uppercase;font-size:15px;margin:0 0 12px;letter-spacing:.04em;}"
    ".upsell-item{display:flex;align-items:center;gap:10px;background:#fff;border:1px solid #e3e3e3;border-radius:8px;padding:8px 10px;margin-bottom:8px;cursor:pointer;}"
    ".upsell-item:last-child{margin-bottom:0;}"
    ".up-thumb{width:46px;height:46px;object-fit:contain;flex:0 0 auto;}"
    ".up-info{flex:1;min-width:0;}"
    ".up-name{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;font-size:12px;line-height:1.3;color:#14142b;}"
    ".up-variant{margin-top:5px;max-width:170px;font-size:12px;}"
    ".up-price{white-space:nowrap;font-weight:700;font-size:13px;color:#14142b;}"
    ".up-was{color:#9aa0a6;font-weight:400;font-size:11px;}"
    ".up-check{width:18px;height:18px;flex:0 0 auto;}"
    "</style>"
)


def build_upsell(current, products, imgdir):
    others = [q for q in products if q["slug"] != current][:3]
    rows = ""
    for q in others:
        is_copa = "price" in q
        if is_copa:
            sale = ("From " if q.get("frm") else "") + "$" + q["price"]
            dprice = q["price"]
            compare = q["compare"]
            variants = q.get("variants") or []
            img = q["imgs"][0]
        else:  # home product dict
            sale = "$" + q["sale"]
            dprice = q["sale"]
            compare = q["compare"]
            variants = []
            img = q["img"]
        price_html = '<span class="up-now">%s</span>' % esc(sale)
        if compare:
            price_html += ' <s class="up-was">$%s</s>' % esc(compare)
        variant_sel = ""
        if variants:
            opts = "".join("<option>%s</option>" % esc(v) for v in variants)
            variant_sel = '<select class="up-variant form-select form-select-sm" onclick="event.preventDefault();">%s</select>' % opts
        rows += (
            '<label class="upsell-item" data-slug="%s" data-name="%s" data-price="%s" data-img="%s%s">'
            '<input type="checkbox" class="up-check">'
            '<img src="%s%s" class="up-thumb" alt="">'
            '<div class="up-info"><span class="up-name">%s</span>%s</div>'
            '<span class="up-price">%s</span></label>'
        ) % (q["slug"], esc(q["title"]), dprice, imgdir, img, imgdir, img, esc(q["title"]), variant_sel, price_html)
    return ('<div class="upsell mt-4"><p class="upsell-title">You might also like these</p>'
            '<div class="upsell-list">%s</div></div>') % rows

_SV = '<svg viewBox="0 0 24 24" fill="none" stroke="#14142b" stroke-width="1.4" width="22" height="22">'
IC_BOX = _SV + '<path d="M3 7l9-4 9 4-9 4z"/><path d="M3 7v10l9 4 9-4V7"/><path d="M12 11v10"/></svg>'
IC_RETURN = _SV + '<path d="M9 14 4 9l5-5"/><path d="M4 9h11a5 5 0 0 1 0 10h-4"/></svg>'
IC_DOC = _SV + '<path d="M7 3h7l4 4v14H7z"/><path d="M14 3v4h4"/><path d="M9.5 13h6M9.5 16.5h6"/></svg>'
IC_LOOK = _SV + '<circle cx="10.5" cy="10.5" r="6"/><path d="m20 20-4.2-4.2"/></svg>'


def acc_item(icon, html):
    return ('<div class="bg-primary-50 rounded-2 p-3 mb-2 d-flex align-items-center">'
            '<span class="acc-icon d-inline-flex align-items-center justify-content-center rounded-circle '
            'border border-2 me-3">%s</span><div class="ff_made fs-6 text-neutral-900">%s</div></div>') % (icon, html)


def build_accordions():
    config_body = (
        '<div class="bg-primary-50 rounded-2 p-3 d-flex align-items-start">'
        '<span class="acc-icon d-inline-flex align-items-center justify-content-center rounded-circle border border-2 me-3">%s</span>'
        '<div><p class="ff_akira_bold text-primary text-uppercase fs-6 mb-2">Look For</p>'
        '<p class="ff_made fs-6 text-neutral-900 mb-1">&#9656;&nbsp; Officially licensed FIFA World Cup 2026&trade; stickers!</p>'
        '<p class="ff_made fs-6 text-neutral-900 mb-0">&#9656;&nbsp; PRE-SALE. PRODUCT EXPECTED TO SHIP IN JULY 2026</p></div></div>'
    ) % IC_LOOK
    shipping_body = (
        acc_item(IC_BOX, "FREE SHIPPING ON ALL US ORDERS OVER $50 FOR REGISTERED USERS.")
        + acc_item(IC_RETURN, "PRE-SALE. PRODUCT EXPECTED TO SHIP IN JULY 2026")
        + acc_item(IC_DOC, "FOR STICKER ITEMS WE HAVE A NO RETURN POLICY IN PLACE.<br><br>ALL SALES ARE FINAL.")
    )
    return (
        '<div class="mt-4">'
        '<details class="pdp-acc border-top border-bottom" open>'
        '<summary class="ff_akira_bold text-uppercase fs-5 text-neutral-900">Configuration</summary>'
        '<div class="acc-body">%s</div></details>'
        '<details class="pdp-acc border-bottom" open>'
        '<summary class="ff_akira_bold text-uppercase fs-5 text-neutral-900">Shipping &amp; Returns</summary>'
        '<div class="acc-body">%s</div></details>'
        '</div>'
    ) % (config_body, shipping_body)


def build_related(current_slug, products):
    cards = ""
    for q in products:
        if q["slug"] == current_slug:
            continue
        price = ("From " if q["frm"] else "") + "$" + q["price"]
        cards += (
            '<div class="rel-card card homeCard rounded-3 border">'
            '<a href="%s.html" class="text-decoration-none d-flex flex-column h-100">'
            '<div class="position-relative p-3">'
            '<button type="button" aria-label="Add to wishlist" class="iconP_love position-absolute top-0 end-0 m-2 '
            'bg-white rounded-circle border-0 fs-3 text-dark p-2" style="z-index:2;"></button>'
            '<div class="d-flex align-items-center justify-content-center" style="height:220px;">'
            '<img src="%s%s" alt="%s" class="img-fluid" style="max-height:210px;width:auto;object-fit:contain;"></div></div>'
            '<div class="px-3"><p class="ff_akira_bold text-neutral-900 fs-6 text-uppercase text-truncate-3 mb-3" '
            'style="min-height:3.4em;">%s</p></div>'
            '<div class="px-3 pb-3 mt-auto">'
            '<p class="ff_made fs-7 text-neutral-900 mb-1 text-uppercase">Price</p>'
            '<p class="fs-18 ff_made_medium text-neutral-900 mb-3">%s</p>'
            '<span class="btn btn-outline-primary w-100">Add to cart</span></div></a></div>'
        ) % (q["slug"], IMG, q["imgs"][0], esc(q["title"]), esc(q["title"]), esc(price))
    return (
        '<section class="container py-5 border-top">'
        '<h2 class="ff_akira_bold text-uppercase fs-2 text-neutral-900 text-center mb-4">Related Products</h2>'
        '<div class="position-relative">'
        '<button type="button" aria-label="Previous" class="rel-nav rel-prev" '
        'onclick="document.getElementById(\'relScroller\').scrollBy({left:-330,behavior:\'smooth\'})">'
        '<span class="iconP_backward_arrow_circle fs-2 text-dark"></span></button>'
        '<div id="relScroller" class="d-flex gap-4 overflow-auto pb-3 px-1">%s</div>'
        '<button type="button" aria-label="Next" class="rel-nav rel-next" '
        'onclick="document.getElementById(\'relScroller\').scrollBy({left:330,behavior:\'smooth\'})">'
        '<span class="iconP_forward_arrow_circle fs-2 text-dark"></span></button>'
        '</div></section>'
    ) % cards

# ----------------------------------------------------------------- product data
products = [
 dict(slug="product-gold-hardcover-album",
      title=u"Panini FIFA World Cup 2026 Premium Gold Hardcover Album",
      price="114.90", compare="57.90", save="49%", frm=False, sold=True, variants=[],
      imgs=["akg1.webp"],
      ext="https://akgstore.com/products/panini-fifa-world-cup-2026-premium-gold-hardcover-album"),
 dict(slug="product-premium-hardcover-album",
      title=u"Panini FIFA World Cup 2026 Premium Hardcover Album",
      price="69.80", compare="34.90", save="50%", frm=False, sold=True, variants=[],
      imgs=["akg2.jpg", "akg_02a_alt.jpg", "akg_collectorbox.webp"],
      ext="https://akgstore.com/products/panini-fifa-world-cup-2026-premium-hardcover-album"),
 dict(slug="product-soft-cover-album",
      title=u"Panini FIFA World Cup 2026™ Official Sticker Collection - Soft Cover Album",
      price="14.90", compare="", save="", frm=False, sold=True, variants=[],
      imgs=["akg3.jpg"],
      ext="https://akgstore.com/products/panini-fifa-world-cup-2026%E2%84%A2-official-sticker-collection-soft-cover-album"),
 dict(slug="product-1box-soft-cover-album",
      title=u"Panini FIFA World Cup 2026™ Official Sticker Collection 1 Box of 50 + a Soft Cover Album",
      price="112.00", compare="47.90", save="", frm=False, sold=False, variants=[],
      imgs=["akg4.webp", "akg_02a_alt.jpg", "akg_collectorbox.webp"],
      ext="https://akgstore.com/products/50packets-album"),
 dict(slug="product-3box-soft-cover-album",
      title=u"Panini FIFA World Cup 2026™ Official Sticker Collection 3 Box of 50 + a Soft Cover Album",
      price="221.90", compare="147.90", save="33%", frm=False, sold=True, variants=[],
      imgs=["akg5.webp", "akg_02a_alt.jpg", "akg_collectorbox.webp"],
      ext="https://akgstore.com/products/the-panini-fifa-world-cup-2026%E2%84%A2-official-sticker-collection-is-here-3-boxes-of-50-packets-and-a-hard-cover-album"),
 dict(slug="product-50-count-box",
      title=u"Panini FIFA World Cup 2026™ Official Sticker Collection 50 Count Box",
      price="105.00", compare="42.90", save="59%", frm=True, sold=True,
      variants=["1 Box (50 Count)", "2 Box (100 Count)", "3 Box (150 Count)"],
      imgs=["akg6.jpg", "akg_b2.jpg", "akg_b3.jpg"],
      ext="https://akgstore.com/products/50countbox"),
 dict(slug="product-packets-individual",
      title=u"Panini FIFA World Cup 2026™ Official Sticker Collection Packets (Individual)",
      price="11.90", compare="", save="", frm=True, sold=True,
      variants=["10 Packets (70 Stickers)", "20 Packets (140 Stickers)", "30 Packets (210 Stickers)"],
      imgs=["akg7.jpg", "akg_20x.jpg", "akg_30x.jpg"],
      ext="https://akgstore.com/products/2026-panini-fifa-world-cup-sticker-exclusive-box"),
 dict(slug="product-gold-limited-50-pack",
      title=u"Panini FIFA World Cup Sticker Box Collection - 50 Pack Box Gold Limited",
      price="52.90", compare="", save="", frm=True, sold=True,
      variants=["1 Box (50 Count)", "2 Box (100 Count)", "3 Box (150 Count)"],
      imgs=["akg8.jpg", "akg_2g.jpg", "akg_3g.jpg"],
      ext="https://akgstore.com/products/panini-fifa-world-cup-sticker-box-collection-50-pack-box-gold-limited"),
 # ----- original Panini cards on the FIFA page (full price, no discount) -----
 dict(slug="product-update-set",
      title=u"PRE-SALE - FIFA World Cup 2026™ Official Sticker Collection - Update Set",
      price="35.00", compare="", save="", frm=False, sold=False, variants=[],
      imgs=["updatedset.jpg"],
      ext="https://www.paniniamerica.net/pre-sale-fifa-world-cup-2026tm-official-sticker-collection-update-set.html"),
 dict(slug="product-50-count-box-panini",
      title=u"FIFA World Cup 2026™ Official Sticker Collection - 50 Count Box",
      price="100.00", compare="", save="", frm=False, sold=False, variants=[],
      imgs=["world_cup_sticker_box_50.png"],
      ext="https://www.paniniamerica.net/fifa-world-cup-2026-official-sticker-collection-50-count-box.html"),
 dict(slug="product-25-pack-box",
      title=u"FIFA World Cup 2026™ Official Sticker Collection - 25 Pack Box",
      price="50.00", compare="", save="", frm=False, sold=False, variants=[],
      imgs=["wc_sticker_box_25_retail.png"],
      ext="https://www.paniniamerica.net/fifa-world-cup-2026-official-sticker-collection-25-pack-box.html"),
]


def build_main(p):
    t = esc(p["title"])
    main_src = IMG + p["imgs"][0]
    thumbs = ""
    if len(p["imgs"]) > 1:
        cells = ""
        for i, im in enumerate(p["imgs"]):
            border = "border-primary" if i == 0 else "border-gray-4"
            cells += (
                '<button type="button" class="btn p-0 border %s rounded-2 overflow-hidden" style="width:78px;height:78px;" '
                'onclick="document.getElementById(\'pdpMain\').src=this.firstElementChild.src;'
                'for(var n of this.parentNode.children){n.classList.remove(\'border-primary\');n.classList.add(\'border-gray-4\');}'
                'this.classList.remove(\'border-gray-4\');this.classList.add(\'border-primary\');">'
                '<img src="%s" alt="%s thumbnail %d" class="w-100 h-100" style="object-fit:cover;"></button>'
            ) % (border, IMG + im, t, i + 1)
        thumbs = '<div class="d-flex gap-2 mt-3 flex-wrap">%s</div>' % cells

    cur = ("From " if p["frm"] else "") + "$" + p["price"]
    price_html = '<span class="fs-2 ff_made_medium text-neutral-900">%s</span>' % esc(cur)
    if p["compare"]:
        price_html += '<span class="fs-4 text-decoration-line-through text-gray-4 ff_made">$%s</span>' % esc(p["compare"])
    if p["save"]:
        price_html += '<span class="badge bg-primary text-white ff_akira_bold ls-2 px-3 py-2">SAVE %s</span>' % esc(p["save"])

    # Sold out removed from every product -> always purchasable
    stock = '<p class="ff_akira_bold text-uppercase ls-2 text-success mb-3">In stock</p>'
    btn_label, btn_cls = "Add to cart", "btn btn-primary"

    variants_html = ""
    if p["variants"]:
        opts = ""
        for i, v in enumerate(p["variants"]):
            active = " active border-primary text-primary" if i == 0 else " border-gray-4 text-neutral-900"
            opts += (
                '<button type="button" class="btn border ff_made_medium fs-7 text-uppercase px-3 py-2 rounded-2%s" '
                'onclick="for(var n of this.parentNode.children){n.classList.remove(\'active\',\'border-primary\',\'text-primary\');'
                'n.classList.add(\'border-gray-4\',\'text-neutral-900\');}'
                'this.classList.add(\'active\',\'border-primary\',\'text-primary\');'
                'this.classList.remove(\'border-gray-4\',\'text-neutral-900\');">%s</button>'
            ) % (active, esc(v))
        variants_html = ('<div class="mb-4"><p class="ff_made fw-light text-uppercase fs-7 ls-4 mb-2">Size</p>'
                         '<div class="d-flex gap-2 flex-wrap">%s</div></div>') % opts

    top = u'''<main class="main_blk" id="main-content" role="main" style="min-height: 90vh;">{style}
<div class="container py_spacer py-4 py-lg-5">
<nav aria-label="breadcrumb"><ol class="breadcrumb py-2 m-0 px-0">
<li class="breadcrumb-item ff_made fw-light text-uppercase fs-6"><a class="text-decoration-none text-neutral-900" href="fifa-world-cup-2026.html">FIFA World Cup 2026</a></li>
<li class="breadcrumb-item active ff_made fw-light text-uppercase fs-6" aria-current="page">{t}</li>
</ol></nav>
<div class="row g-4 g-lg-5 mt-1">
<div class="col-12 col-lg-6">
<div class="border rounded-3 p-3 d-flex align-items-center justify-content-center bg-white" style="min-height:420px;">
<img id="pdpMain" src="{main}" alt="{t}" class="img-fluid" style="max-height:520px;width:auto;object-fit:contain;"></div>
{thumbs}
</div>
<div class="col-12 col-lg-6">
<p class="ff_made fw-light text-uppercase fs-7 ls-4 text-primary mb-2">Panini &middot; Officially Licensed</p>
<h1 class="ff_akira_bold text-neutral-900 fs-2 mb-3">{t}</h1>
<div class="d-flex align-items-center flex-wrap gap-3 mb-2">{price}</div>
{stock}
{variants}
<div class="mb-3"><label class="ff_made fw-light text-uppercase fs-7 ls-4 mb-2 d-block">Quantity</label>
<input type="number" id="pdp-qty" min="1" value="1" class="form-control rounded-2" style="max-width:120px;" aria-label="Quantity"></div>
{upsell}
<div class="d-grid gap-2">
<button type="button" aria-label="{label}" class="{btncls} btn-large w-100" style="min-height:48px;" data-add-to-cart data-slug="{slug}" data-name="{t}" data-price="{dprice}" data-img="{main}">{label}</button>
<button type="button" aria-label="Buy it now" class="btn btn-outline-primary btn-large w-100" style="min-height:48px;" data-add-to-cart data-buy-now data-slug="{slug}" data-name="{t}" data-price="{dprice}" data-img="{main}">Buy it now</button>
</div>
{accordions}
</div>
</div>
</div>
{rich}
{related}
</main>'''.format(t=t, main=main_src, thumbs=thumbs, price=price_html, stock=stock,
                  variants=variants_html, label=btn_label, btncls=btn_cls, ext=p["ext"], rich=RICH,
                  style=STYLE, accordions=build_accordions(), related=build_related(p["slug"], products),
                  slug=p["slug"], dprice=p["price"], upsell=build_upsell(p["slug"], products, IMG))
    return top


for p in products:
    prod_js = ('<script>window.__PRODUCT__=%s;</script><script src="tracking.js"></script>'
               % json.dumps({"id": p["slug"], "name": p["title"], "value": float(p["price"])}))
    html = PREFIX + build_main(p) + '\n<script src="cart.js"></script>\n' + prod_js + '\n' + SUFFIX
    html = re.sub(r"<title>.*?</title>", "<title>%s | Panini America</title>" % esc(p["title"]),
                  html, count=1, flags=re.IGNORECASE | re.DOTALL)
    out = r"C:\Users\Vetz\Desktop\panini-offline\%s.html" % p["slug"]
    io.open(out, "w", encoding="utf-8").write(html)
    print("wrote", p["slug"] + ".html", "(%d bytes)" % len(html))

# repoint FIFA cards (idempotent)
fifa = io.open(FIFA, "r", encoding="utf-8", errors="replace").read()
n = 0
for p in products:
    needle = 'target="_blank" rel="noopener noreferrer" href="%s"' % p["ext"]
    repl = 'target="_self" rel="noopener noreferrer" href="%s.html"' % p["slug"]
    if needle in fifa:
        fifa = fifa.replace(needle, repl); n += 1

# original Panini cards on the FIFA grid -> local pages (Tin reuses the home page)
ORIG_REPOINT = {
    "https://www.paniniamerica.net/pre-sale-fifa-world-cup-2026tm-official-sticker-collection-update-set.html": "product-update-set.html",
    "https://www.paniniamerica.net/fifa-world-cup-2026-official-sticker-collection-50-count-box.html": "product-50-count-box-panini.html",
    "https://www.paniniamerica.net/fifa-world-cup-2026-official-sticker-collection-25-pack-box.html": "product-25-pack-box.html",
    "https://www.paniniamerica.net/fifa-world-cup-2026-official-sticker-collection-tin-starter-kit.html": "sale-fifa-world-cup-2026-official-sticker-collection-tin-sta.html",
}
for ext, local in ORIG_REPOINT.items():
    needle = 'href="%s"' % ext
    if needle in fifa:
        fifa = fifa.replace(needle, 'href="%s"' % local); n += 1
io.open(FIFA, "w", encoding="utf-8").write(fifa)
print("repointed", n, "card links")
