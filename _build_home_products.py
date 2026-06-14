# -*- coding: utf-8 -*-
"""Create sale pages for the (non-Copa) products on the home page: each gets its
own product page at HALF PRICE (original struck through, SAVE 50%). Also rewrites
the home-page cards to show the half price and link to the local sale page.
Copa / FIFA World Cup products are intentionally left untouched."""
import io, re, json
from decimal import Decimal, ROUND_HALF_UP

INDEX = r"C:\Users\Vetz\Desktop\panini-offline\index.html"
HIMG = "./assets-store/"

src = io.open(INDEX, "r", encoding="utf-8", errors="replace").read()
PREFIX = src[:src.index("</header>") + len("</header>")]
SUFFIX = src[src.index("<footer"):]


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def half(price):
    v = Decimal(price.replace(",", "")) / 2
    return v.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def money(d):
    return "{:,.2f}".format(d)


def slug(t):
    s = re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")
    return "sale-" + s[:55].strip("-")


# idx, full title, original price, image file
RAW = [
    (20, 'Carter Bryant Autographed Wilson All Star 2026 Replica White Panel Basketball with "26\' Slam Dunk" Inscription ~Limited Edition to 25~', "399.99", "3.10.26_basketballs-1.jpg"),
    (21, "Carter Bryant Autographed Wilson Replica Basketball ~Open Edition Item~", "299.99", "7.31.25_items-17.jpg"),
    (22, "Carter Bryant Autographed Wilson San Antonio Spurs Team Alliance Replica Basketball ~Open Edition Item~", "299.99", "7.31.25_items-15.jpg"),
    (23, "Angel Reese Autographed Wilson WNBA Replica Basketball ~Open Edition Item~", "349.99", "9.25.25_items-70.jpg"),
    (24, "Angel Reese Autographed Wilson WNBA Commissioner's Cup Authentic Basketball ~Open Edition Item~", "549.99", "9.25.25_items-74.jpg"),
    (25, "Jeremiah Fears Autographed Wilson All Star 2026 Replica White Panel Basketball ~Limited Edition to 25~", "399.99", "3.10.26_basketballs-7.jpg"),
    (26, "Tre Johnson III Autographed Wilson 2026 All Star Replica White Panel Basketball ~Limited Edition to 25~", "399.99", "3.10.26_basketballs-4.jpg"),
    (27, "Jared McCain Autographed Wilson Replica Basketball ~Open Edition Item~", "299.99", "6.12.25_mccain_items-33.jpg"),
    (30, "2025 Panini Prizm WNBA Trading Card Box (Hobby)", "749.95", "25_prizm_wnba_bk_hobby_c2049-i.png"),
    (31, "2025 Panini One and One WNBA Trading Card Box (Hobby)", "574.95", "25-26_one_and_one_wnba_hobby_a6935_01_.png"),
    (32, "2025 Panini Impeccable LIV Golf Trading Card Box (Hobby)", "500.00", "25_impeccable_golf_hobby_lid_65958.png"),
]

# Copa products that appear on the home page — FULL price (no discount, no SAVE badge)
COPA_RAW = [
    (28, "FIFA World Cup 2026™ Official Sticker Collection - Tin Starter Kit (Online Exclusive)", "60.00", "wc_tin.png"),
    (29, "2026 Panini Prizm Monopoly FIFA World Cup 2026™ Trading Card Box (Blaster)", "34.95", "25-26_monopoly_fifa_blaster_c2919.png"),
]

products = []
for idx, title, price, img in RAW:                       # 50% OFF
    products.append(dict(idx=idx, title=title, img=img, slug=slug(title),
                         sale=money(half(price)), compare=money(Decimal(price.replace(",", ""))), badge=True))
for idx, title, price, img in COPA_RAW:                   # preço cheio
    products.append(dict(idx=idx, title=title, img=img, slug=slug(title),
                         sale=money(Decimal(price.replace(",", ""))), compare=None, badge=False))

# -------------------------------------------------------------------- styles
STYLE = (
    "<style>"
    "#relScroller{scrollbar-width:none;-ms-overflow-style:none;scroll-snap-type:x mandatory}"
    "#relScroller::-webkit-scrollbar{display:none}"
    ".rel-nav{position:absolute;top:40%;z-index:5;width:46px;height:46px;border-radius:50%;background:#fff;"
    "border:0;box-shadow:0 2px 14px rgba(0,0,0,.18);display:flex;align-items:center;justify-content:center}"
    ".rel-prev{left:-12px}.rel-next{right:-12px}.rel-card{width:300px;flex:0 0 auto;scroll-snap-align:start}"
    ".pdp-acc>summary{list-style:none;cursor:pointer;display:flex;align-items:center;justify-content:space-between;padding:1rem 0}"
    ".pdp-acc>summary::-webkit-details-marker{display:none}"
    ".pdp-acc>summary::after{content:'';width:.6rem;height:.6rem;border-right:2px solid #14142b;border-bottom:2px solid #14142b;"
    "transform:rotate(45deg);transition:transform .2s;flex:0 0 auto;margin-left:1rem}"
    ".pdp-acc[open]>summary::after{transform:rotate(-135deg)}"
    ".upsell{background:#f4f5f7;border-radius:12px;padding:16px;}"
    ".upsell-title{font-weight:700;text-transform:uppercase;font-size:15px;margin:0 0 12px;letter-spacing:.04em;}"
    ".upsell-item{display:flex;align-items:center;gap:10px;background:#fff;border:1px solid #e3e3e3;border-radius:8px;padding:8px 10px;margin-bottom:8px;cursor:pointer;}"
    ".upsell-item:last-child{margin-bottom:0;}"
    ".up-thumb{width:46px;height:46px;object-fit:contain;flex:0 0 auto;}"
    ".up-info{flex:1;min-width:0;}"
    ".up-name{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;font-size:12px;line-height:1.3;color:#14142b;}"
    ".up-price{white-space:nowrap;font-weight:700;font-size:13px;color:#14142b;}"
    ".up-was{color:#9aa0a6;font-weight:400;font-size:11px;}"
    ".up-check{width:18px;height:18px;flex:0 0 auto;}"
    "</style>"
)


def build_upsell(current):
    others = [q for q in products if q["slug"] != current][:3]
    rows = ""
    for q in others:
        price_html = '<span class="up-now">$%s</span>' % q["sale"]
        if q["compare"]:
            price_html += ' <s class="up-was">$%s</s>' % q["compare"]
        rows += (
            '<label class="upsell-item" data-slug="%s" data-name="%s" data-price="%s" data-img="%s%s">'
            '<input type="checkbox" class="up-check">'
            '<img src="%s%s" class="up-thumb" alt="">'
            '<div class="up-info"><span class="up-name">%s</span></div>'
            '<span class="up-price">%s</span></label>'
        ) % (q["slug"], esc(q["title"]), q["sale"], HIMG, q["img"], HIMG, q["img"], esc(q["title"]), price_html)
    return ('<div class="upsell mt-4"><p class="upsell-title">You might also like these</p>'
            '<div class="upsell-list">%s</div></div>') % rows

_SV = '<svg viewBox="0 0 24 24" fill="none" stroke="#14142b" stroke-width="1.4" width="44" height="44">'
F_TRUCK = _SV + '<rect x="2.5" y="6.5" width="11" height="9" rx="1"/><path d="M13.5 9.5h3.5l3 3v3h-6.5z"/><circle cx="7" cy="18" r="1.7"/><circle cx="17.5" cy="18" r="1.7"/></svg>'
F_LOCK = _SV + '<rect x="4.5" y="10" width="15" height="10.5" rx="2"/><path d="M8 10V7a4 4 0 0 1 8 0v3"/><circle cx="12" cy="15" r="1.3"/></svg>'
F_AWARD = _SV + '<circle cx="12" cy="8.5" r="5"/><path d="M8.6 12.8 7 21l5-2.6L17 21l-1.6-8.2"/></svg>'
F_SHIELD = _SV + '<path d="M12 3l7 3v5c0 4.5-3 7.5-7 9-4-1.5-7-4.5-7-9V6z"/><path d="M9 12l2 2 4-4"/></svg>'
FEATURES = [(F_TRUCK, "Free Shipping"), (F_SHIELD, "Panini Authentic"), (F_LOCK, "Secure Payment"), (F_AWARD, "Premium Quality")]


def describe(title):
    if "Autographed" in title:
        return ("This officially licensed collectible is hand-signed and authenticated by <strong>Panini Authentic</strong>. "
                "Every autograph is witnessed and sealed with a tamper-evident hologram and backed by a matching certificate "
                "of authenticity, so you can collect with total confidence. A premium centerpiece for any collection.")
    if "Sticker" in title:
        return ("An <strong>Officially Licensed FIFA World Cup&trade;</strong> sticker product from Panini, the world&#39;s "
                "leading sticker publisher. Collect, stick and trade officially licensed stickers of national teams, star "
                "players and unforgettable tournament moments.")
    return ("A factory-sealed <strong>Panini America</strong> trading card box. Chase autographs, memorabilia cards, parallels "
            "and sought-after inserts from one of the hobby's most popular releases. Sealed product, ready for breaking or "
            "long-term collecting.")


def feature_row():
    cells = ""
    for svg, label in FEATURES:
        cells += ('<div class="col-6 col-lg-3 text-center mb-4"><div class="text-neutral-900 mb-2">%s</div>'
                  '<p class="ff_akira_bold text-uppercase fs-6 text-neutral-900 mb-0">%s</p></div>') % (svg, esc(label))
    return '<div class="row justify-content-center align-items-start py-4 my-2 border-top border-bottom">%s</div>' % cells


def related(current):
    cards = ""
    for q in products:
        if q["slug"] == current:
            continue
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
            '<div class="px-3 pb-3 mt-auto"><p class="ff_made fs-7 text-neutral-900 mb-1 text-uppercase">Price</p>'
            '<p class="fs-18 ff_made_medium text-neutral-900 mb-1">%s</p>'
            '<span class="btn btn-outline-primary w-100">Add to cart</span></div></a></div>'
        ) % (q["slug"], HIMG, q["img"], esc(q["title"]), esc(q["title"]),
             ('$%s <span class="fs-6 text-decoration-line-through text-gray-4">$%s</span>' % (q["sale"], q["compare"])) if q["compare"] else ('$%s' % q["sale"]))
    return (
        '<section class="container py-5 border-top"><h2 class="ff_akira_bold text-uppercase fs-2 text-neutral-900 text-center mb-4">Related Products</h2>'
        '<div class="position-relative">'
        '<button type="button" aria-label="Previous" class="rel-nav rel-prev" onclick="document.getElementById(\'relScroller\').scrollBy({left:-330,behavior:\'smooth\'})">'
        '<span class="iconP_backward_arrow_circle fs-2 text-dark"></span></button>'
        '<div id="relScroller" class="d-flex gap-4 overflow-auto pb-3 px-1">%s</div>'
        '<button type="button" aria-label="Next" class="rel-nav rel-next" onclick="document.getElementById(\'relScroller\').scrollBy({left:330,behavior:\'smooth\'})">'
        '<span class="iconP_forward_arrow_circle fs-2 text-dark"></span></button></div></section>'
    ) % cards


def build_main(p):
    t = esc(p["title"])
    price_block = '<span class="fs-1 ff_made_medium text-neutral-900">$%s</span>' % p["sale"]
    if p["compare"]:
        price_block += '<span class="fs-3 text-decoration-line-through text-gray-4 ff_made">$%s</span>' % p["compare"]
    if p["badge"]:
        price_block += '<span class="badge bg-primary text-white ff_akira_bold ls-2 px-3 py-2">SAVE 50%</span>'
    return u'''<main class="main_blk" id="main-content" role="main" style="min-height: 90vh;">{style}
<div class="container py_spacer py-4 py-lg-5">
<nav aria-label="breadcrumb"><ol class="breadcrumb py-2 m-0 px-0">
<li class="breadcrumb-item ff_made fw-light text-uppercase fs-6"><a class="text-decoration-none text-neutral-900" href="/">Home</a></li>
<li class="breadcrumb-item active ff_made fw-light text-uppercase fs-6" aria-current="page" style="max-width:60ch;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{t}</li>
</ol></nav>
<div class="row g-4 g-lg-5 mt-1">
<div class="col-12 col-lg-6">
<div class="border rounded-3 p-3 d-flex align-items-center justify-content-center bg-white" style="min-height:440px;">
<img src="{img}" alt="{t}" class="img-fluid" style="max-height:540px;width:auto;object-fit:contain;"></div></div>
<div class="col-12 col-lg-6">
<p class="ff_made fw-light text-uppercase fs-7 ls-4 text-primary mb-2">Panini America &middot; Officially Licensed</p>
<h1 class="ff_akira_bold text-neutral-900 fs-2 mb-3">{t}</h1>
<div class="d-flex align-items-center flex-wrap gap-3 mb-2">{price_block}</div>
<p class="ff_akira_bold text-uppercase ls-2 text-success mb-3">In stock</p>
<div class="mb-3"><label class="ff_made fw-light text-uppercase fs-7 ls-4 mb-2 d-block">Quantity</label>
<input type="number" id="pdp-qty" min="1" value="1" class="form-control rounded-2" style="max-width:120px;" aria-label="Quantity"></div>
{upsell}
<div class="d-grid gap-2">
<button type="button" aria-label="Add to cart" class="btn btn-primary btn-large w-100" style="min-height:48px;" data-add-to-cart data-slug="{slug}" data-name="{t}" data-price="{sale}" data-img="{img}">Add to cart</button>
<button type="button" aria-label="Buy it now" class="btn btn-outline-primary btn-large w-100" style="min-height:48px;" data-add-to-cart data-buy-now data-slug="{slug}" data-name="{t}" data-price="{sale}" data-img="{img}">Buy it now</button></div>
<div class="mt-4"><details class="pdp-acc border-top border-bottom" open>
<summary class="ff_akira_bold text-uppercase fs-5 text-neutral-900">Description</summary>
<div class="pb-3"><p class="ff_made fs-6 text-neutral-900 mb-0">{desc}</p></div></details>
<details class="pdp-acc border-bottom" open>
<summary class="ff_akira_bold text-uppercase fs-5 text-neutral-900">Shipping &amp; Returns</summary>
<div class="pb-3"><p class="ff_made fs-6 text-neutral-900 mb-1">Free shipping on all US orders over $50 for registered users.</p>
<p class="ff_made fs-6 text-neutral-900 mb-0">All sales are final. Authenticity guaranteed by Panini Authentic.</p></div></details></div>
</div>
</div>
{features}
</div>
{related}
</main>'''.format(style=STYLE, t=t, img=HIMG + p["img"], price_block=price_block,
                  desc=describe(p["title"]), features=feature_row(), related=related(p["slug"]), slug=p["slug"], sale=p["sale"],
                  upsell=build_upsell(p["slug"]))


# ----------------------------------------------------------- write sale pages
for p in products:
    prod_js = ('<script>window.__PRODUCT__=%s;</script><script src="tracking.js"></script>'
               % json.dumps({"id": p["slug"], "name": p["title"], "value": float(p["sale"].replace(",", ""))}))
    html = PREFIX + build_main(p) + '\n<script src="cart.js"></script>\n' + prod_js + '\n' + SUFFIX
    html = re.sub(r"<title>.*?</title>", "<title>%s | Panini America</title>" % esc(p["title"]),
                  html, count=1, flags=re.IGNORECASE | re.DOTALL)
    io.open(r"C:\Users\Vetz\Desktop\panini-offline\%s.html" % p["slug"], "w", encoding="utf-8").write(html)
    print("wrote", p["slug"] + ".html  ($%s%s)" % (p["sale"], "  (de $" + p["compare"] + ")" if p["compare"] else ""))

# --------------------------------------------- rewrite home cards (link + half price)
h = io.open(INDEX, "r", encoding="utf-8", errors="replace").read()
starts = [m.start() for m in re.finditer(r"homeCard", h)]
by_idx = {p["idx"]: p for p in products}
result = h[:starts[0]]
for i in range(len(starts)):
    seg = h[starts[i]: starts[i + 1] if i + 1 < len(starts) else len(h)]
    if i in by_idx:
        p = by_idx[i]
        seg = re.sub(r'href="https://www\.paniniamerica\.net/[^"]*"',
                     'href="%s.html" target="_self"' % p["slug"], seg, count=1)
        seg = re.sub(r'(<span>\$</span>\s*<span>)[\d.,]+(</span>)',
                     r'\g<1>%s\g<2>' % p["sale"], seg, count=1)
    result += seg
io.open(INDEX, "w", encoding="utf-8").write(result)
print("rewrote", len(products), "home cards (linked + half price)")
