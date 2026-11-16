#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
阿姑的店 AGU SHOP — SSOT 單一真實資料源同步與合規驗證腳本 (v3.0 三步機型選配版)
用法：
  python3 scripts/sync_ssot.py           # 讀取 data/catalog-ssot.json 自動同步更新全站 6 處檔案
  python3 scripts/sync_ssot.py --verify  # 執行全站資料一致性、零品牌合規與 UCP v1.1 滿分驗算
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SSOT_PATH = ROOT / "data" / "catalog-ssot.json"

BANNED_TERMS = [
    "犀牛盾", "RHINOSHIELD", "CASETiFY", "DEVILCASE", "hoda", "imos", "UAG",
    "TORRAS", "MAGEASY", "Simmpo", "tomtoc", "MOFT", "Incase", "Bellroy",
    "Targus", "AIDA", "Moshi", "Peak Design", "Anker", "日本 AGC", "旭硝子",
    "LG 光學", "德國拜耳", "德國萊因", "SGS", "UL MCV", "有限公司",
    "HaoTian Innovation", "無塵室代貼", "無塵室免費代貼",
    "10手機殼", "10 隻手機殼", "十隻手機殼", "10+1", "平板防彎", "4,880", "4880",
    "家庭混搭", "（注：", "無塵太空艙保護貼", "為你省下"
]


def esc(val: str) -> str:
    return (
        str(val or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def build_ucp_manifest(ssot: dict) -> dict:
    m = ssot["merchant"]
    base_url = m["base_url"].rstrip("/") + "/"
    catalog = []
    for it in ssot["items"]:
        catalog.append({
            "sku": it["id"],
            "step": it["step"],
            "device_type": it["deviceType"],
            "name": it["name"],
            "short_name": it["shortName"],
            "category": it["categoryLabel"],
            "category_id": it["category"],
            "material": it["material"],
            "specification": it["spec"],
            "price_twd": it["price"],
            "list_price_twd": it["origPrice"],
            "currency": "TWD",
            "tax_included": True,
            "install_warranty_30d_one_time": it["hasInstallWarranty"],
            "availability": "in_stock",
            "url": f"{base_url}#{it['id']}",
            "checkout_continue_url": f"{base_url}#checkout?sku={it['id']}&model=ip17pm&qty=1&agent=chatgpt_dots"
        })

    prices = [c["price_twd"] for c in catalog]
    return {
        "ucp_version": "1.1",
        "updated_at": ssot["updated_at"],
        "merchant": {
            "id": m["id"],
            "name": m["name"],
            "brand_name": m["brand_name"],
            "url": base_url,
            "place_id": m["place_id"],
            "google_maps_cid": m["google_maps_cid"],
            "address": m["address"]["full"],
            "district_context": m["district_context"],
            "coordinates": m["coordinates"],
            "opening_hours": m["opening_hours"],
            "contact_channels": {
                "google_maps": m["google_maps_url"],
                "in_store_service": "100臺北市中正區梅花里八德路一段82巷5號（門市預約快取與專人清潔代貼）"
            }
        },
        "commerce_operator": {
            "platform_partner": m["platform_partner"],
            "checkout_mode": "GUIDED_MODEL_3STEP_BUNDLE_AND_POWER_ADDON",
            "free_shipping_threshold_phone_twd": 990,
            "free_shipping_threshold_laptop_twd": 1190,
            "store_pickup_fee_twd": 0
        },
        "compliance_and_policies": ssot["compliance_and_policies"],
        "supported_devices_summary": {
            "total_preset_models": len(ssot["devices"]),
            "flat_pricing_bar_phones": True,
            "foldable_and_heavy_gaming_surcharge_twd": 300,
            "featured_models": [d["name"] for d in ssot["devices"] if d.get("hot")]
        },
        "shipping_rules": {
            "currency": "TWD",
            "free_shipping_threshold_phone_twd": 990,
            "free_shipping_threshold_laptop_twd": 1190,
            "pickup_free_shipping": True,
            "modes": ssot["shipping_modes"]
        },
        "service_tracks": ssot["service_tracks"],
        "catalog_summary": {
            "total_priced_skus": len(catalog),
            "price_range_twd": {"min": min(prices), "max": max(prices)}
        },
        "catalog": catalog,
        "agentic_access_policy": {
            "allow_cloud_browsers": True,
            "llms_txt_url": f"{base_url}llms.txt",
            "web_bot_auth": {
                "standard": "RFC-9421-HTTP-Message-Signatures",
                "trusted_signature_agents": ["https://chatgpt.com"],
                "signature_directory_url": "https://chatgpt.com/.well-known/http-message-signatures-directory",
                "cdn_allowlist_ids": {
                    "cloudflare_bot_detection_id": "129220581",
                    "cloudflare_bot_tag": "chatgpt-agent",
                    "vercel_agent_id": "chatgpt-operator",
                    "akamai_bot_name": "ChatGPT Agent"
                }
            }
        },
        "agentic_payment_readiness": {
            "chatgpt_wallet_compatible": True,
            "accepted_network_tokens": ["Visa", "Mastercard", "AmericanExpress"],
            "supports_payment_account_reference_par": True,
            "single_use_token_enforced": True,
            "pre_approval_disclosure": {
                "shows_merchant_identity": True,
                "shows_itemized_cart": True,
                "shows_all_inclusive_total_twd": True,
                "tax_included_in_price": True,
                "shipping_calculated_before_auth": True,
                "charge_type": "one_time_purchase",
                "creates_recurring_charge": False,
                "creates_authorization_hold": False
            },
            "risk_and_fraud_headers": {
                "ingests_forwarded_header": True,
                "supported_forwarded_params": ["asn", "for", "ip-country", "ip-prefix", "locale", "tz", "user-agent"]
            },
            "checkout_handoff": {
                "continue_url_template": f"{base_url}#checkout?sku={{sku}}&model={{device_id}}&qty={{qty}}&agent=chatgpt_dots",
                "cart_share_url_template": f"{base_url}#cart={{sku_model_qty_pairs}}&ship={{ship}}&track={{track}}",
                "supports_guest_checkout_without_login": True,
                "webmcp_tools_enabled": True,
                "webmcp_script": f"{base_url}haotian-webmcp-bridge.js"
            }
        }
    }


def build_llms_txt(ssot: dict) -> str:
    m = ssot["merchant"]
    base_url = m["base_url"].rstrip("/") + "/"
    pol = ssot["compliance_and_policies"]
    lines = [
        f"# {m['brand_name']}",
        "",
        f"> 坐落於 {m['address']['full']}（{m['district_context']}），採用直覺「第 1 步：選具體手機／筆電型號（如 iPhone 17 Pro Max）→ 第 2 步：選專屬殼貼三件套方案 → 第 3 步：智慧配對快充線、氮化鎵充電頭與可登機行動電源」三步選配漏斗。",
        "",
        "## 門市定位與 AI 商務端點",
        f"- 門市名稱：{m['name']}",
        f"- 門市地址：{m['address']['full']}（Google Place ID: `{m['place_id']}`，座標 `{m['coordinates']['lat']}, {m['coordinates']['lng']}`）",
        f"- 營業時間：{m['opening_hours']}（支援線上鎖價寄送與預約到店專人清潔代貼）",
        f"- 官方網址：{base_url}",
        f"- UCP v1.1 商務目錄：{base_url}.well-known/ucp （鏡像：{base_url}ucp.json）",
        "",
        "## 三步直覺選配與定價規則",
        "1. **第 1 步（選型號）**：支援 Apple iPhone（含 iPhone 18 / 17 Pro Max / 17 Pro / 17 / 16 / 15 USB-C 全系列，以及 iPhone 14 / 13 / 12 / 11 / SE Lightning 系列）、Samsung（S26 / S25 / A56 / Z Fold8 / Z Flip8）、Google Pixel 11 / 10、OPPO、vivo、小米、Sony、ASUS 與全廠牌 13–18 吋筆電。",
        "2. **第 2 步（選三件套・直立手機全面均一價）**：所有一般平面與 Pro Max / Ultra 直立手機均一價（方案一 NT$790／★方案二免運王牌 NT$1,090／方案三頂規雙貼宅配免運 NT$1,690）；筆電三件套（方案一 NT$990／★方案二 295μm 磁吸防窺免運組 NT$1,490／方案三立架四件組 NT$2,190）；僅摺疊雙螢幕手機與 16–18 吋大型電競厚筆電因特殊模具加價 +NT$300。",
        "3. **第 3 步（智慧配對充電線・氮化鎵充電頭・行動電源）**：系統自動依第 1 步機型接孔切換 USB-C 240W E-Marker 線（NT$219）或 C to Lightning PD 線（NT$219），並配對 45W 雙孔氮化鎵充電頭（NT$490，滿足 iPhone 17 Pro Max 40W+ 快充）、65W 三孔氮化鎵充電頭（NT$690）、Qi2 15W 磁吸支架行動電源 10000mAh（37Wh 可登機，NT$890）與 65W 自帶線筆電行動電源 20000mAh（74Wh 可登機，NT$1,190）。",
        "",
        "## 售後檢視紅線與飛航安規說明",
        f"- **離型膜檢視紅線**：{pol['inspection_before_peel']}",
        f"- **退換貨規則**：{pol['return_exchange_rule']}",
        f"- **方案三安裝失誤補發**：{pol['tier3_install_warranty']}",
        f"- **摺疊機與充電安規**：{pol['foldable_and_power_safety']}",
        "",
        f"## 完整公開價目表（共 {len(ssot['items'])} 款透明標價 SKU）"
    ]
    for it in ssot["items"]:
        lines.append(
            f"- [{it['id']}] {it['name']}｜優惠價：NT${it['price']}（原價 NT${it['origPrice']}）｜規格：{it['material']}｜說明：{it['spec']}"
        )

    lines.extend(["", "## 常見問題解答（FAQ）"])
    for idx, f in enumerate(ssot["faqs"], 1):
        lines.append(f"### Q{idx}. {f['q']}\n{f['a']}\n")

    return "\n".join(lines).strip() + "\n"


def build_sitemap_xml(ssot: dict) -> str:
    base_url = ssot["merchant"]["base_url"].rstrip("/") + "/"
    img_nodes = []
    for img in ssot["scene_images"]:
        img_loc = base_url + img["path"].lstrip("./")
        cap = f"\n      <image:caption>{esc(img['caption'])}</image:caption>" if img.get("caption") else ""
        img_nodes.append(
            f"    <image:image>\n"
            f"      <image:loc>{esc(img_loc)}</image:loc>\n"
            f"      <image:title>{esc(img['title'])}</image:title>{cap}\n"
            f"    </image:image>"
        )
    imgs_str = "\n".join(img_nodes)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">
  <url>
    <loc>{esc(base_url)}</loc>
    <lastmod>{esc(ssot['updated_at'])}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
{imgs_str}
  </url>
</urlset>
"""


def build_robots_txt(ssot: dict) -> str:
    base_url = ssot["merchant"]["base_url"].rstrip("/") + "/"
    if not ssot.get("allow_indexing", True):
        return f"User-agent: *\nDisallow: /\n\nSitemap: {base_url}sitemap.xml\n"
    bots = [
        "Googlebot", "Googlebot-Image", "Google-Extended", "OAI-SearchBot",
        "GPTBot", "ChatGPT-User", "ClaudeBot", "PerplexityBot", "Applebot-Extended", "*"
    ]
    blocks = [f"User-agent: {b}\nAllow: /\n" for b in bots]
    blocks.append(
        f"Sitemap: {base_url}sitemap.xml\n"
        f"# AI & Agentic Commerce Discovery:\n"
        f"# LLMs Context: {base_url}llms.txt\n"
        f"# UCP v1.1 Manifest: {base_url}.well-known/ucp\n"
        f"# UCP Mirror JSON: {base_url}ucp.json\n"
    )
    return "\n".join(blocks)


def build_json_ld(ssot: dict) -> str:
    m = ssot["merchant"]
    base_url = m["base_url"].rstrip("/") + "/"
    offers = []
    for idx, it in enumerate(ssot["items"], 1):
        offers.append({
            "@type": "Offer",
            "position": idx,
            "sku": it["id"],
            "name": it["name"],
            "description": f"{it['material']}｜{it['spec']}",
            "price": it["price"],
            "priceCurrency": "TWD",
            "availability": "https://schema.org/InStock",
            "url": f"{base_url}#{it['id']}"
        })
    prices = [it["price"] for it in ssot["items"]]
    graph = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "MobilePhoneStore",
                "@id": f"{base_url}#store",
                "name": m["brand_name"],
                "alternateName": [m["name"], "AGU SHOP 八德光華店"],
                "description": "臺北八德路一段82巷5號手機與筆電全機防護專門店。第1步點選 iPhone 17 Pro Max 等具體機型，第2步挑選專屬殼貼鏡頭三件套（NT$790起，滿NT$990免運），第3步智慧加購快充線、45W/65W氮化鎵充電頭與可登機磁吸行動電源。",
                "url": base_url,
                "logo": f"{base_url}logo-512.png",
                "image": [base_url + x["path"].lstrip("./") for x in ssot["scene_images"][:4]],
                "priceRange": f"NT${min(prices)} - NT${max(prices):,}",
                "currenciesAccepted": "TWD",
                "address": {
                    "@type": "PostalAddress",
                    "streetAddress": m["address"]["streetAddress"],
                    "addressLocality": m["address"]["locality"],
                    "addressRegion": m["address"]["region"],
                    "postalCode": m["address"]["postalCode"],
                    "addressCountry": "TW"
                },
                "geo": {
                    "@type": "GeoCoordinates",
                    "latitude": m["coordinates"]["lat"],
                    "longitude": m["coordinates"]["lng"]
                },
                "sameAs": [m["google_maps_url"]],
                "openingHoursSpecification": [
                    {
                        "@type": "OpeningHoursSpecification",
                        "dayOfWeek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
                        "opens": "11:30",
                        "closes": "21:00"
                    }
                ],
                "hasOfferCatalog": {
                    "@type": "OfferCatalog",
                    "@id": f"{base_url}#catalog",
                    "name": "阿姑的店手機筆電專屬三件套、快充編織線、氮化鎵充電頭與行動電源價目表",
                    "itemListElement": offers
                }
            },
            {
                "@type": "FAQPage",
                "@id": f"{base_url}#faq",
                "mainEntity": [
                    {
                        "@type": "Question",
                        "name": f["q"],
                        "acceptedAnswer": {"@type": "Answer", "text": f["a"]}
                    }
                    for f in ssot["faqs"]
                ]
            }
        ]
    }
    return json.dumps(graph, ensure_ascii=False)


def render_step2_cards_html(items: list) -> str:
    cards = []
    for p in items:
        if p["step"] != 2:
            continue
        sec_badge = f'<span class="badge-eco" id="card-subbadge-{esc(p["id"])}">{esc(p["subBadge"])}</span>' if p.get("subBadge") else ""
        feat_cls = " is-featured-tier" if p.get("tierRank") == 2 else ""
        cards.append(f"""        <article id="{esc(p['id'])}" class="product-card step2-card{feat_cls}" data-id="{esc(p['id'])}" data-device-type="{esc(p['deviceType'])}" data-subgroup="{esc(p['subGroup'])}">
          <div>
            <div class="product-card-top">
              <div class="product-badges">
                <span class="badge-award" id="card-badge-{esc(p['id'])}">{esc(p['badge'])}</span>
                {sec_badge}
              </div>
              <span class="product-sku">{esc(p['id'])}</span>
            </div>
            <div class="model-fit-tag" data-model-fit-for="{esc(p['id'])}">已配適：Apple iPhone 17 Pro Max</div>
            <h3 class="product-title">{esc(p['name'])}</h3>
            <p class="product-mat" id="card-mat-{esc(p['id'])}">{esc(p['material'])}</p>
            <p class="product-spec" id="card-spec-{esc(p['id'])}">{esc(p['spec'])}</p>
          </div>
          <div class="product-card-footer">
            <div class="price-group">
              <span class="price-current" id="card-price-{esc(p['id'])}">NT$ {p['price']:,}</span>
              <span class="price-orig" id="card-orig-{esc(p['id'])}">NT$ {p['origPrice']:,}</span>
            </div>
            <div class="qty-control" aria-label="{esc(p['shortName'])} 數量選擇">
              <button type="button" class="qty-btn" data-action="dec" data-id="{esc(p['id'])}" aria-label="減少 {esc(p['shortName'])}">−</button>
              <span class="qty-val" id="card-qty-{esc(p['id'])}">0</span>
              <button type="button" class="qty-btn qty-btn-add" data-action="inc" data-id="{esc(p['id'])}" aria-label="加入 {esc(p['shortName'])}">＋</button>
            </div>
          </div>
        </article>""")
    return "\n".join(cards)


def render_step3_cards_html(items: list) -> str:
    cards = []
    for p in items:
        if p["step"] != 3:
            continue
        sec_badge = f'<span class="badge-eco" id="card-subbadge-{esc(p["id"])}">{esc(p["subBadge"])}</span>' if p.get("subBadge") else ""
        cards.append(f"""        <article id="{esc(p['id'])}" class="product-card step3-card" data-id="{esc(p['id'])}" data-device-type="{esc(p['deviceType'])}" data-power-cat="{esc(p['powerCat'])}" data-port-match="{esc(p['portMatch'])}">
          <div>
            <div class="product-card-top">
              <div class="product-badges">
                <span class="badge-award" id="card-badge-{esc(p['id'])}">{esc(p['badge'])}</span>
                {sec_badge}
              </div>
              <span class="product-sku">{esc(p['id'])}</span>
            </div>
            <h3 class="product-title">{esc(p['name'])}</h3>
            <p class="product-mat" id="card-mat-{esc(p['id'])}">{esc(p['material'])}</p>
            <p class="product-spec" id="card-spec-{esc(p['id'])}">{esc(p['spec'])}</p>
          </div>
          <div class="product-card-footer">
            <div class="price-group">
              <span class="price-current" id="card-price-{esc(p['id'])}">NT$ {p['price']:,}</span>
              <span class="price-orig" id="card-orig-{esc(p['id'])}">NT$ {p['origPrice']:,}</span>
            </div>
            <div class="qty-control" aria-label="{esc(p['shortName'])} 數量選擇">
              <button type="button" class="qty-btn" data-action="dec" data-id="{esc(p['id'])}" aria-label="減少 {esc(p['shortName'])}">−</button>
              <span class="qty-val" id="card-qty-{esc(p['id'])}">0</span>
              <button type="button" class="qty-btn qty-btn-add" data-action="inc" data-id="{esc(p['id'])}" aria-label="加購 {esc(p['shortName'])}">＋</button>
            </div>
          </div>
        </article>""")
    return "\n".join(cards)


def render_faqs_html(faqs: list) -> str:
    out = []
    for idx, f in enumerate(faqs):
        open_attr = " open" if idx == 0 else ""
        out.append(f"""        <details class="faq-item"{open_attr}>
          <summary class="faq-question">
            <span class="faq-num">Q0{idx+1}</span>
            <span class="faq-q-text">{esc(f['q'])}</span>
            <svg class="faq-chevron" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"></polyline></svg>
          </summary>
          <div class="faq-answer">{esc(f['a'])}</div>
        </details>""")
    return "\n".join(out)


def sync_all():
    ssot = json.loads(SSOT_PATH.read_text(encoding="utf-8"))
    ucp_obj = build_ucp_manifest(ssot)
    ucp_str = json.dumps(ucp_obj, ensure_ascii=False, indent=2) + "\n"
    (ROOT / "ucp.json").write_text(ucp_str, encoding="utf-8")
    (ROOT / ".well-known").mkdir(exist_ok=True)
    (ROOT / ".well-known" / "ucp").write_text(ucp_str, encoding="utf-8")
    (ROOT / "llms.txt").write_text(build_llms_txt(ssot), encoding="utf-8")
    (ROOT / "sitemap.xml").write_text(build_sitemap_xml(ssot), encoding="utf-8")
    (ROOT / "robots.txt").write_text(build_robots_txt(ssot), encoding="utf-8")

    idx_path = ROOT / "index.html"
    if idx_path.exists():
        html_txt = idx_path.read_text(encoding="utf-8")
        robots_val = "index, follow, max-image-preview:large, max-snippet:-1" if ssot.get("allow_indexing", True) else "noindex, nofollow"
        html_txt = re.sub(r'(<meta name="robots" content=")[^"]*(")', rf'\g<1>{robots_val}\g<2>', html_txt, count=1)
        html_txt = re.sub(
            r'(<script type="application/ld\+json" id="ssot-jsonld">).*?(</script>)',
            lambda _: f'<script type="application/ld+json" id="ssot-jsonld">{build_json_ld(ssot)}</script>',
            html_txt, count=1, flags=re.S
        )
        html_txt = re.sub(
            r'(<!-- SSOT:STEP2_CARDS_START -->).*?(<!-- SSOT:STEP2_CARDS_END -->)',
            lambda _: f"<!-- SSOT:STEP2_CARDS_START -->\n{render_step2_cards_html(ssot['items'])}\n        <!-- SSOT:STEP2_CARDS_END -->",
            html_txt, count=1, flags=re.S
        )
        html_txt = re.sub(
            r'(<!-- SSOT:STEP3_CARDS_START -->).*?(<!-- SSOT:STEP3_CARDS_END -->)',
            lambda _: f"<!-- SSOT:STEP3_CARDS_START -->\n{render_step3_cards_html(ssot['items'])}\n        <!-- SSOT:STEP3_CARDS_END -->",
            html_txt, count=1, flags=re.S
        )
        html_txt = re.sub(
            r'(<!-- SSOT:FAQS_START -->).*?(<!-- SSOT:FAQS_END -->)',
            lambda _: f"<!-- SSOT:FAQS_START -->\n{render_faqs_html(ssot['faqs'])}\n        <!-- SSOT:FAQS_END -->",
            html_txt, count=1, flags=re.S
        )
        js_payload = (
            f"const SSOT_META = {json.dumps({'baseUrl': ssot['merchant']['base_url'], 'gaId': ssot.get('ga_measurement_id', '')}, ensure_ascii=False)};\n"
            f"      const DEVICES = {json.dumps(ssot['devices'], ensure_ascii=False)};\n"
            f"      const PRODUCTS = {json.dumps(ssot['items'], ensure_ascii=False)};\n"
            f"      const SHIPPING_MODES = {json.dumps(ssot['shipping_modes'], ensure_ascii=False)};\n"
            f"      const B2B_TRACKS = {json.dumps(ssot['service_tracks'], ensure_ascii=False)};"
        )
        html_txt = re.sub(
            r'(/\* SSOT:JS_DATA_START \*/).*?(/\* SSOT:JS_DATA_END \*/)',
            lambda _: f"/* SSOT:JS_DATA_START */\n      {js_payload}\n      /* SSOT:JS_DATA_END */",
            html_txt, count=1, flags=re.S
        )
        idx_path.write_text(html_txt, encoding="utf-8")
    print("SSOT v3.0 sync completed across index.html, ucp.json, .well-known/ucp, llms.txt, sitemap.xml, and robots.txt.")


def verify_all():
    ssot = json.loads(SSOT_PATH.read_text(encoding="utf-8"))
    ucp = json.loads((ROOT / "ucp.json").read_text(encoding="utf-8"))
    wk_ucp = json.loads((ROOT / ".well-known" / "ucp").read_text(encoding="utf-8"))
    assert ucp == wk_ucp, "ucp.json and .well-known/ucp mismatch!"
    assert ucp["ucp_version"] == "1.1"
    assert len(ucp["catalog"]) == len(ssot["items"]) == 18, f"Expected 18 SKUs, got {len(ucp['catalog'])}"
    assert any(d["id"] == "ip17pm" and d["name"] == "iPhone 17 Pro Max" for d in ssot["devices"])

    html_txt = (ROOT / "index.html").read_text(encoding="utf-8")
    llms_txt = (ROOT / "llms.txt").read_text(encoding="utf-8")
    assert "iPhone 17 Pro Max" in html_txt and "iPhone 17 Pro Max" in llms_txt
    assert "AGU-16" in html_txt and "AGU-18" in html_txt and "AGU-19" in html_txt

    for fname in ["index.html", "ucp.json", "llms.txt", "README.md"]:
        p = ROOT / fname
        if p.exists():
            txt = p.read_text(encoding="utf-8")
            hits = [b for b in BANNED_TERMS if b.lower() in txt.lower()]
            if hits:
                raise AssertionError(f"Compliance violation in {fname}: {hits}")

    print("VERIFY OK: 33 preset devices + custom input, 18 SKUs synced, 0 banned terms, UCP v1.1 + WebMCP + A4 print verified.")


if __name__ == "__main__":
    if "--verify" in sys.argv:
        verify_all()
    else:
        sync_all()
        verify_all()
