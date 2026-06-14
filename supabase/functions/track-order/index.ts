// Supabase Edge Function: track-order
// Recebe { order_id, email } e devolve o status + rastreio do pedido.
// A tabela orders é privada (RLS) — esta função lê com service_role com segurança.
// (Verify JWT pode ficar LIGADO — o site chama com a chave anon.)
import { serve } from "https://deno.land/std@0.224.0/http/server.ts";

const SUPABASE_URL = Deno.env.get("SUPABASE_URL")!;
const SERVICE_ROLE = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
const sb = { apikey: SERVICE_ROLE, Authorization: `Bearer ${SERVICE_ROLE}` };

const cors = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};
const json = (o: unknown, s = 200) =>
  new Response(JSON.stringify(o), { status: s, headers: { ...cors, "Content-Type": "application/json" } });

const SEL = "select=id,email,status,total_cents,currency,tracking_number,carrier,tracking_url,created_at," +
  "shipping_name,shipping_address,shipping_city,shipping_state,shipping_zip,shipping_country";

serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: cors });
  try {
    const { order_id, email } = await req.json();
    let url: string;
    if (order_id) {
      url = `${SUPABASE_URL}/rest/v1/orders?id=eq.${encodeURIComponent(String(order_id).trim())}&${SEL}`;
    } else if (email) {
      url = `${SUPABASE_URL}/rest/v1/orders?email=eq.${encodeURIComponent(String(email).trim())}&status=neq.pending&order=created_at.desc&limit=1&${SEL}`;
    } else {
      return json({ error: "Informe o número do pedido ou o email." }, 400);
    }

    const rows = await (await fetch(url, { headers: sb })).json();
    const o = rows[0];
    if (!o) return json({ error: "Pedido não encontrado." }, 404);

    // se buscou por order_id e passou email, valida que confere
    if (order_id && email && o.email &&
        String(email).trim().toLowerCase() !== String(o.email).trim().toLowerCase()) {
      return json({ error: "O email não confere com este pedido." }, 403);
    }

    const items = await (await fetch(
      `${SUPABASE_URL}/rest/v1/order_items?order_id=eq.${o.id}&select=name,quantity,unit_price_cents,products(image,slug)`,
      { headers: sb },
    )).json();

    return json({
      id: o.id, status: o.status, total_cents: o.total_cents, currency: o.currency,
      tracking_number: o.tracking_number, carrier: o.carrier, tracking_url: o.tracking_url,
      created_at: o.created_at,
      shipping_name: o.shipping_name, shipping_address: o.shipping_address,
      shipping_city: o.shipping_city, shipping_state: o.shipping_state,
      shipping_zip: o.shipping_zip, shipping_country: o.shipping_country,
      items,
    });
  } catch (e) {
    return json({ error: String(e) }, 500);
  }
});
