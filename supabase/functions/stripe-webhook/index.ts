// Supabase Edge Function: stripe-webhook
// Valida a assinatura do Stripe, marca o pedido como 'paid' e dispara:
//  - Facebook Conversions API (Purchase, dedup pelo event_id = order.id)
//  - UTMify Orders API (pedido pago + UTMs)
// Deploy com "Verify JWT" DESLIGADO.
// Secrets: STRIPE_WEBHOOK_SECRET, FB_CAPI_TOKEN, UTMIFY_API_TOKEN
import { serve } from "https://deno.land/std@0.224.0/http/server.ts";

const WEBHOOK_SECRET = Deno.env.get("STRIPE_WEBHOOK_SECRET")!;
const SUPABASE_URL = Deno.env.get("SUPABASE_URL")!;
const SERVICE_ROLE = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
const FB_PIXEL_ID = "28181409881448447";                 // público
const FB_CAPI_TOKEN = Deno.env.get("FB_CAPI_TOKEN") || "";
const UTMIFY_API_TOKEN = Deno.env.get("UTMIFY_API_TOKEN") || "";

const sb = { apikey: SERVICE_ROLE, Authorization: `Bearer ${SERVICE_ROLE}`, "Content-Type": "application/json" };
const enc = new TextEncoder();

async function verify(rawBody: string, sigHeader: string): Promise<boolean> {
  if (!sigHeader) return false;
  const parts: Record<string, string> = {};
  for (const kv of sigHeader.split(",")) { const i = kv.indexOf("="); if (i > 0) parts[kv.slice(0, i).trim()] = kv.slice(i + 1).trim(); }
  const t = parts["t"], v1 = parts["v1"];
  if (!t || !v1) return false;
  const key = await crypto.subtle.importKey("raw", enc.encode(WEBHOOK_SECRET), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  const mac = await crypto.subtle.sign("HMAC", key, enc.encode(`${t}.${rawBody}`));
  const hex = [...new Uint8Array(mac)].map((b) => b.toString(16).padStart(2, "0")).join("");
  return hex === v1;
}

async function sha256(s: string): Promise<string> {
  const b = await crypto.subtle.digest("SHA-256", enc.encode(s));
  return [...new Uint8Array(b)].map((x) => x.toString(16).padStart(2, "0")).join("");
}

const fmtUTC = (d: Date) => d.toISOString().slice(0, 19).replace("T", " ");

async function sendFacebook(order: any, items: any[]) {
  if (!FB_CAPI_TOKEN) return;
  const email = (order.email || "").trim().toLowerCase();
  const tp = order.tracking_params || {};
  const user_data: any = {};
  if (email) user_data.em = [await sha256(email)];
  if (tp.fbp) user_data.fbp = tp.fbp;                          // cookie do Pixel -> match exato
  if (tp.fbc) user_data.fbc = tp.fbc;
  else if (tp.fbclid) user_data.fbc = `fb.1.${Math.floor(Date.now() / 1000)}.${tp.fbclid}`;
  const body = {
    data: [{
      event_name: "Purchase",
      event_time: Math.floor(Date.now() / 1000),
      event_id: order.id,                       // mesmo id do navegador -> deduplica
      action_source: "website",
      user_data,
      custom_data: {
        currency: (order.currency || "usd").toUpperCase(),
        value: order.total_cents / 100,
        content_type: "product",
        content_ids: items.map((it) => it.products && it.products.slug).filter(Boolean),
      },
    }],
  };
  try {
    await fetch(`https://graph.facebook.com/v21.0/${FB_PIXEL_ID}/events?access_token=${FB_CAPI_TOKEN}`,
      { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  } catch (_) { /* não bloqueia */ }
}

async function sendUtmify(order: any, items: any[]) {
  if (!UTMIFY_API_TOKEN) return;
  const tp = order.tracking_params || {};
  const now = fmtUTC(new Date());
  const body = {
    orderId: order.id,
    platform: "PaniniStore",
    paymentMethod: "credit_card",
    status: "paid",
    createdAt: order.created_at ? fmtUTC(new Date(order.created_at)) : now,
    approvedDate: now,
    refundedAt: null,
    customer: { name: order.shipping_name || null, email: order.email || null, phone: null, document: null, country: "US" },
    products: items.map((it) => ({
      id: (it.products && it.products.slug) || "item", name: it.name,
      planId: null, planName: null, quantity: it.quantity, priceInCents: it.unit_price_cents,
    })),
    trackingParameters: {
      src: tp.src || null, sck: tp.sck || null,
      utm_source: tp.utm_source || null, utm_campaign: tp.utm_campaign || null,
      utm_medium: tp.utm_medium || null, utm_content: tp.utm_content || null, utm_term: tp.utm_term || null,
    },
    commission: { totalPriceInCents: order.total_cents, gatewayFeeInCents: 0, userCommissionInCents: order.total_cents },
    isTest: true, // <-- trocar para false quando for produção (live)
  };
  try {
    await fetch("https://api.utmify.com.br/api-credentials/orders", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-api-token": UTMIFY_API_TOKEN,
        // UTMify fica atrás do Cloudflare e bloqueia requisições sem UA de navegador (erro 1010)
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
      },
      body: JSON.stringify(body),
    });
  } catch (_) { /* não bloqueia */ }
}

serve(async (req) => {
  const sig = req.headers.get("stripe-signature") || "";
  const raw = await req.text();
  if (!(await verify(raw, sig))) return new Response("invalid signature", { status: 400 });

  let event: any;
  try { event = JSON.parse(raw); } catch { return new Response("bad json", { status: 400 }); }

  if (event.type === "payment_intent.succeeded") {
    const pi = event.data.object;
    const orderId = pi?.metadata?.order_id;
    if (orderId) {
      // 1) marca como paid
      await fetch(`${SUPABASE_URL}/rest/v1/orders?id=eq.${orderId}`, {
        method: "PATCH", headers: { ...sb, Prefer: "return=minimal" },
        body: JSON.stringify({ status: "paid", stripe_payment_intent: pi.id, email: pi.receipt_email || undefined }),
      });
      // 2) busca pedido + itens
      const order = (await (await fetch(`${SUPABASE_URL}/rest/v1/orders?id=eq.${orderId}&select=*`, { headers: sb })).json())[0];
      const items = await (await fetch(`${SUPABASE_URL}/rest/v1/order_items?order_id=eq.${orderId}&select=name,quantity,unit_price_cents,products(slug)`, { headers: sb })).json();
      // 3) dispara Facebook + UTMify
      if (order) await Promise.allSettled([sendFacebook(order, items), sendUtmify(order, items)]);
    }
  }

  return new Response(JSON.stringify({ received: true }), { status: 200, headers: { "Content-Type": "application/json" } });
});
