# -*- coding: utf-8 -*-
import io, json, urllib.request, urllib.error
token = io.open('_utmify_key.txt', 'r', encoding='utf-8-sig').read().strip()
body = {
  "orderId": "panini-test-001",
  "platform": "PaniniStore",
  "paymentMethod": "credit_card",
  "status": "paid",
  "createdAt": "2026-06-14 18:00:00",
  "approvedDate": "2026-06-14 18:00:00",
  "refundedAt": None,
  "customer": {"name": "Teste", "email": "teste@example.com", "phone": None, "document": None, "country": "US"},
  "products": [{"id": "product-50-count-box", "name": "50 Count Box", "planId": None, "planName": None, "quantity": 1, "priceInCents": 10500}],
  "trackingParameters": {"src": None, "sck": None, "utm_source": "facebook", "utm_campaign": "copa2026", "utm_medium": "cpc", "utm_content": None, "utm_term": None},
  "commission": {"totalPriceInCents": 10500, "gatewayFeeInCents": 0, "userCommissionInCents": 10500},
  "isTest": True,
}
req = urllib.request.Request("https://api.utmify.com.br/api-credentials/orders", data=json.dumps(body).encode())
req.add_header("Content-Type", "application/json")
req.add_header("x-api-token", token)
req.add_header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36")
try:
    resp = urllib.request.urlopen(req)
    print("STATUS", resp.status)
    print(resp.read().decode()[:800])
except urllib.error.HTTPError as e:
    print("HTTP ERROR", e.code)
    print(e.read().decode()[:1200])
except Exception as e:
    print("ERR", repr(e))
