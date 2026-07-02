// Supabase Edge Function: pagou-webhook
// Recebe eventos da pagou.ai. Como a pagou não expõe publicamente o formato da
// assinatura, confirmamos o pagamento por RECONCILIAÇÃO: ao chegar o evento,
// consultamos GET /v2/transactions/:id na própria pagou e só marcamos o pedido
// como 'paid' se a API confirmar status pago (paid/captured).
// Depois dispara:
//  - Facebook Conversions API (Purchase, dedup pelo event_id = order.id)
//  - UTMify Orders API (pedido pago + UTMs)
// Deploy com "Verify JWT" DESLIGADO.
// Secrets: PAGOU_SECRET_KEY, FB_CAPI_TOKEN, UTMIFY_API_TOKEN
//          (PAGOU_API_BASE opcional — default https://api.pagou.ai)
import { serve } from "https://deno.land/std@0.224.0/http/server.ts";

const PAGOU_SECRET = Deno.env.get("PAGOU_SECRET_KEY")!;
const PAGOU_API_BASE = Deno.env.get("PAGOU_API_BASE") || "https://api.pagou.ai";
const SUPABASE_URL = Deno.env.get("SUPABASE_URL")!;
const SERVICE_ROLE = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
const FB_PIXEL_ID = "28181409881448447";                 // público
const FB_CAPI_TOKEN = Deno.env.get("FB_CAPI_TOKEN") || "";
const UTMIFY_API_TOKEN = Deno.env.get("UTMIFY_API_TOKEN") || "";
const IS_SANDBOX = /sandbox|local/i.test(PAGOU_API_BASE);

const sb = { apikey: SERVICE_ROLE, Authorization: `Bearer ${SERVICE_ROLE}`, "Content-Type": "application/json" };
const enc = new TextEncoder();

// status que contam como pago na pagou
const PAID = new Set(["paid", "captured", "authorized", "approved", "succeeded"]);

async function sha256(s: string): Promise<string> {
  const b = await crypto.subtle.digest("SHA-256", enc.encode(s));
  return [...new Uint8Array(b)].map((x) => x.toString(16).padStart(2, "0")).join("");
}

const fmtUTC = (d: Date) => d.toISOString().slice(0, 19).replace("T", " ");

// cotação USD -> BRL ao vivo (UTMify trabalha em Reais)
async function usdToBrl(): Promise<number> {
  try {
    const r = await fetch("https://api.frankfurter.app/latest?from=USD&to=BRL");
    const d = await r.json();
    return d && d.rates && d.rates.BRL ? d.rates.BRL : 5.5;
  } catch (_) { return 5.5; }
}

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
    const resp = await fetch(`https://graph.facebook.com/v21.0/${FB_PIXEL_ID}/events?access_token=${FB_CAPI_TOKEN}`,
      { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    console.log("FB CAPI", resp.status, (await resp.text()).slice(0, 300));
  } catch (e) { console.log("FB CAPI ERROR", String(e)); }
}

async function sendUtmify(order: any, items: any[], isTest: boolean) {
  if (!UTMIFY_API_TOKEN) return;
  const tp = order.tracking_params || {};
  const now = fmtUTC(new Date());
  const rate = await usdToBrl();                 // converte USD -> BRL (UTMify usa Reais)
  const toBrl = (cents: number) => Math.round(cents * rate);
  const body = {
    orderId: order.id,
    platform: "PaniniStore",
    paymentMethod: "credit_card",
    status: "paid",
    createdAt: order.created_at ? fmtUTC(new Date(order.created_at)) : now,
    approvedDate: now,
    refundedAt: null,
    customer: {
      name: order.shipping_name || (order.email ? order.email.split("@")[0] : "Cliente"),
      email: order.email || "sem-email@panini.store",
      phone: null, document: null, country: "US",
    },
    products: items.map((it) => ({
      id: (it.products && it.products.slug) || "item", name: it.name,
      planId: null, planName: null, quantity: it.quantity, priceInCents: toBrl(it.unit_price_cents),
    })),
    trackingParameters: {
      src: tp.src || null, sck: tp.sck || null,
      utm_source: tp.utm_source || null, utm_campaign: tp.utm_campaign || null,
      utm_medium: tp.utm_medium || null, utm_content: tp.utm_content || null, utm_term: tp.utm_term || null,
    },
    commission: { totalPriceInCents: toBrl(order.total_cents), gatewayFeeInCents: 0, userCommissionInCents: toBrl(order.total_cents) },
    isTest: isTest, // sandbox conta como teste; produção conta como venda real
  };
  try {
    const resp = await fetch("https://api.utmify.com.br/api-credentials/orders", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-api-token": UTMIFY_API_TOKEN,
        // UTMify fica atrás do Cloudflare e bloqueia requisições sem UA de navegador (erro 1010)
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
      },
      body: JSON.stringify(body),
    });
    console.log("UTMIFY", resp.status, "isTest=" + isTest, "USD->BRL=" + rate, (await resp.text()).slice(0, 400));
  } catch (e) { console.log("UTMIFY ERROR", String(e)); }
}

// Confirma o pagamento direto na pagou (não confia só no corpo do webhook)
async function confirmPaid(txId: string): Promise<{ ok: boolean; status: string; metadata?: string }> {
  try {
    const r = await fetch(`${PAGOU_API_BASE}/v2/transactions/${txId}`, {
      headers: { Authorization: `Bearer ${PAGOU_SECRET}` },
    });
    const t = await r.json();
    const status = String(t.status || "").toLowerCase();
    return { ok: r.ok && PAID.has(status), status, metadata: t.metadata != null ? String(t.metadata) : undefined };
  } catch (e) {
    console.log("PAGOU confirm ERROR", String(e));
    return { ok: false, status: "error" };
  }
}

serve(async (req) => {
  const raw = await req.text();
  let event: any;
  try { event = JSON.parse(raw); } catch { return new Response("bad json", { status: 400 }); }

  // Envelope de pagamentos da pagou: { id, event:"transaction", data:{ id, event_type, status, metadata } }
  const data = event.data || {};
  const eventType = String(data.event_type || event.type || "");
  const txId = data.id || event.id;

  // só nos interessa transação paga
  if (event.event === "transaction" && eventType === "transaction.paid" && txId) {
    // reconciliação: confirma na API antes de marcar
    const chk = await confirmPaid(txId);
    const orderId = chk.metadata || (data.metadata != null ? String(data.metadata) : "");
    console.log("WEBHOOK pagou tx", txId, "confirmed", chk.ok, "status", chk.status, "order", orderId);

    if (chk.ok && orderId) {
      // 1) marca como paid (reaproveita a coluna de id de pagamento existente)
      await fetch(`${SUPABASE_URL}/rest/v1/orders?id=eq.${orderId}`, {
        method: "PATCH", headers: { ...sb, Prefer: "return=minimal" },
        body: JSON.stringify({ status: "paid", stripe_payment_intent: txId }),
      });
      // 2) busca pedido + itens
      const order = (await (await fetch(`${SUPABASE_URL}/rest/v1/orders?id=eq.${orderId}&select=*`, { headers: sb })).json())[0];
      const items = await (await fetch(`${SUPABASE_URL}/rest/v1/order_items?order_id=eq.${orderId}&select=name,quantity,unit_price_cents,products(slug)`, { headers: sb })).json();
      // 3) dispara Facebook + UTMify
      if (order) await Promise.allSettled([sendFacebook(order, items), sendUtmify(order, items, IS_SANDBOX)]);
    }
  }

  return new Response(JSON.stringify({ received: true }), { status: 200, headers: { "Content-Type": "application/json" } });
});
