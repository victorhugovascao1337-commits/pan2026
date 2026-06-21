// Supabase Edge Function: create-checkout
// 1) Recebe o carrinho (slugs + quantidades) e busca o PREÇO REAL no banco
// 2) Cria um pedido (status 'pending') em orders + order_items
// 3) Cria um PaymentIntent no Stripe com metadata.order_id e devolve o clientSecret
// Secrets: STRIPE_SECRET_KEY  (SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY são automáticos)
import { serve } from "https://deno.land/std@0.224.0/http/server.ts";

const STRIPE_SECRET = Deno.env.get("STRIPE_SECRET_KEY")!;
const SUPABASE_URL = Deno.env.get("SUPABASE_URL")!;
const SERVICE_ROLE = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
const SHIPPING: Record<string, number> = { standard: 0, express: 2000 };

const cors = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};
const json = (obj: unknown, status = 200) =>
  new Response(JSON.stringify(obj), { status, headers: { ...cors, "Content-Type": "application/json" } });

// Gera um código de rastreio no estilo USPS (22 dígitos, agrupados de 4 em 4)
function uspsCode(): string {
  let d = "9400";
  for (let i = 0; i < 18; i++) d += Math.floor(Math.random() * 10);
  return d.replace(/(.{4})/g, "$1 ").trim();
}

const sbHeaders = {
  apikey: SERVICE_ROLE,
  Authorization: `Bearer ${SERVICE_ROLE}`,
  "Content-Type": "application/json",
};

serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: cors });
  try {
    const { items = [], shipping = "standard", email, address, utm } = await req.json();
    if (!Array.isArray(items) || items.length === 0) return json({ error: "Empty cart" }, 400);
    const a = address || {};

    // slugs -> produtos reais do banco (preço autoritativo)
    const slugs = items.map((i: any) => String(i.slug));
    const filter = `slug=in.(${slugs.map((s) => `"${s}"`).join(",")})`;
    const pr = await fetch(
      `${SUPABASE_URL}/rest/v1/products?select=id,slug,name,price_cents&active=eq.true&${filter}`,
      { headers: sbHeaders },
    );
    const products = await pr.json();
    const bySlug: Record<string, any> = {};
    for (const p of products) bySlug[p.slug] = p;

    // desconto por volume (variante): 2x = 10% off, 3x = 15% off
    const BULK: Record<number, number> = { 1: 1, 2: 0.90, 3: 0.85 };
    let subtotal = 0;
    const lineItems: any[] = [];
    for (const it of items) {
      const p = bySlug[String(it.slug)];
      if (!p) return json({ error: `Invalid product: ${it.slug}` }, 400);
      const qty = Math.max(1, parseInt(it.quantity) || 1);
      const mult = Math.min(3, Math.max(1, parseInt(it.mult) || 1));
      const unit = Math.round(p.price_cents * mult * (BULK[mult] || 1));
      subtotal += unit * qty;
      const name = it.variant ? `${p.name} - ${it.variant}` : p.name;
      lineItems.push({ product_id: p.id, name, unit_price_cents: unit, quantity: qty });
    }
    const shippingCents = SHIPPING[shipping] ?? 0;
    const total = subtotal + shippingCents;

    // 1) cria o pedido (pending)
    const orderRes = await fetch(`${SUPABASE_URL}/rest/v1/orders`, {
      method: "POST",
      headers: { ...sbHeaders, Prefer: "return=representation" },
      body: JSON.stringify({
        email: email || null, status: "pending", subtotal_cents: subtotal,
        shipping_cents: shippingCents, total_cents: total, currency: "usd",
        tracking_number: uspsCode(), carrier: "USPS",
        shipping_name: a.name || null, shipping_address: a.line1 || null,
        shipping_city: a.city || null, shipping_state: a.state || null,
        shipping_zip: a.zip || null, shipping_country: a.country || "United States",
        tracking_params: utm || {},
      }),
    });
    const orderRow = (await orderRes.json())[0];
    const orderId = orderRow?.id;
    if (!orderId) return json({ error: "Could not create order" }, 500);

    // order_items
    await fetch(`${SUPABASE_URL}/rest/v1/order_items`, {
      method: "POST",
      headers: sbHeaders,
      body: JSON.stringify(lineItems.map((li) => ({ ...li, order_id: orderId }))),
    });

    // 2) PaymentIntent com order_id na metadata
    const body = new URLSearchParams();
    body.set("amount", String(total));
    body.set("currency", "usd");
    body.set("automatic_payment_methods[enabled]", "true");
    if (email) body.set("receipt_email", String(email));
    body.set("metadata[order_id]", String(orderId));
    body.set("metadata[shipping]", String(shipping));
    body.set("description", "mayvul order " + orderId);

    const sr = await fetch("https://api.stripe.com/v1/payment_intents", {
      method: "POST",
      headers: { Authorization: `Bearer ${STRIPE_SECRET}`, "Content-Type": "application/x-www-form-urlencoded" },
      body,
    });
    const pi = await sr.json();
    if (pi.error) return json({ error: pi.error.message }, 400);

    return json({ clientSecret: pi.client_secret, orderId, amount: total, subtotal, shipping: shippingCents });
  } catch (e) {
    return json({ error: String(e) }, 500);
  }
});
