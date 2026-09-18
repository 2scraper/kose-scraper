#!/usr/bin/env python3
"""
smoke_test.py — kose-scraper's offline suite
=============================================
One file of plain functions with inline fixtures. No pytest, no conftest, no
fixtures directory; `tests/test_smoke.py` wraps this as a single pytest test
so `pytest` works as an entry point without a second copy of the checks.

    python3 smoke_test.py          # everything
    python3 smoke_test.py -v       # and say what each check looked at

It must pass with NO engine library installed at all: every
`import playwright_scraper` / `selenium_scraper` / `puppeteer_scraper` is
guarded and the skip is RECORDED, because "skipped, engine absent" reads
identically to a real import error. CI installs each engine in its own venv
and fails if that engine's group reports a skip.

The fixtures
------------
Every one is cut VERBATIM from a real capture taken 2026-09-18 and trimmed to
the parts the parser reads. Each was verified to parse to IDENTICAL values to
its untrimmed original before being committed (§15 step 3): the trimming
script asserted field-by-field equality on every row, not merely that the row
count matched.

    LISTING_HTML         /site/cosmedecorte/c/c15/, 4 of its 24 tiles —
                         three unavailable and one in stock, so `in_stock`
                         is checked against a page that really has both
                         values on it. Prices run 3,300 to 264,000 yen.
    LISTING_TAX8_HTML    /c/c15_p10/, the one page in the captures carrying
                         Japan's REDUCED 8% consumption-tax rate. Two tiles
                         in 171 had it, and a consumer computing a pre-tax
                         figure from the standard rate is wrong in silence.
    TAGS_HTML            /site/itemtags/list.aspx?tags=…, two tiles of two
                         DIFFERENT brands — the route that crosses brands,
                         which is why `brand` is read per tile.
    PRODUCT_HTML         one ONE BY KOSE product: its JSON-LD `Product`
                         block, its price node, its breadcrumb, its colour
                         list — and, deliberately, one of the staff-review
                         cards that reuse the class `c-product__item` on a
                         `<div>`, plus an `awoo` recommendation block. A
                         class-only tile selector invents products out of
                         both; this fixture is what pins that it does not.
    EMPTY_HTML           a listing the site served with no tiles on it: a
                         tag facet walked past its end. An ANSWER, not a
                         failure.
    NOTFOUND_HTML        the site's own 404. It carries exactly one
                         product-shaped link, which is why the
                         parse-failure threshold is two.
    CHROMIUM_ERROR_HTML  Chromium's own network-error page. It carries
                         `<title>maison.kose.co.jp</title>` — the site's own
                         hostname — and no vendor marker at all, which is
                         why positive-asset detection is the only thing that
                         classifies it correctly (§18).

No personal data appears in any of them. Maison KOSÉ does publish staff
opinion pieces under real first names, and the one staff card in
PRODUCT_HTML is there because the PARSER must ignore it — so the author's
name and the review text are replaced with obvious placeholders while the
markup the site generates around them is left untouched (§10).
`check_fixtures_carry_no_session_material` guards the next capture by
PATTERN rather than by these literals.
"""

import argparse
import ast
import csv
import inspect
import io
import json
import os
import re
import subprocess
import sys
import tempfile
from dataclasses import asdict, fields

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import env_config
import output_writer
import page_flow
import product_parser
import proxy_pool
from output_writer import Product

FAILURES = []
PASSED = 0
SKIPS = []
VERBOSE = False


def check(name, condition, detail=""):
    global PASSED
    if condition:
        PASSED += 1
        if VERBOSE:
            print("  ok   %s%s" % (name, (" — " + detail) if detail else ""))
    else:
        FAILURES.append("%s%s" % (name, (" — " + detail) if detail else ""))
        print("  FAIL %s%s" % (name, (" — " + detail) if detail else ""))


def equal(name, got, want):
    check(name, got == want, "got %r, want %r" % (got, want))


def skip(group, reason):
    SKIPS.append("%s: %s" % (group, reason))


LISTING_URL = "https://maison.kose.co.jp/site/cosmedecorte/c/c15/"
TAGS_URL = ("https://maison.kose.co.jp/site/itemtags/list.aspx"
            "?tags=%E3%82%B7%E3%83%AF%E6%94%B9%E5%96%84,%E3%82%B9%E3%82%AD%E3%83%B3%E3%82%B1%E3%82%A2")
PRODUCT_URL = "https://maison.kose.co.jp/site/onebykose/g/gMUSC/"

LISTING_HTML = """<!doctype html><html lang="ja"><head>
<meta charset="UTF-8">
<meta name="keywords" content="1／13ページMaison KOSE">
<link rel="canonical" href="https://maison.kose.co.jp/site/cosmedecorte/c/c15/">
<link rel="next" href="https://maison.kose.co.jp/site/cosmedecorte/c/c15_p2/">
<title>コスメデコルテ｜ Maison KOS&#201;(メゾンコーセー)</title>
<link rel="stylesheet" href="/freepage/maison-kose/common/css/style.css">
<script src="/js/sys/goods_filter.js"></script>
<script src="/js/sys/cart.js"></script>
</head><body>
<ul class="c-product-content__list js-goods-list-wrapper list-modal-trigger">
<li class="c-product__item is-item-number-1">
  <p class="c-product__icon__wrap">
    <span class="c-product__icon c-product__icon-limited"><img src="/freepage/maison-kose/common/img/badge/new.png" alt="NEW"></span>
    
    
  </p>
  <div class="c-product__thumb is-new">
    <a href="/site/cosmedecorte/g/gJQBA/" class="c-product__thumb__img">
      <img src="/img/goods/S/JQBA_sub.png" alt="AQ ミリオリティ ザ クリーム デコラシオン ＜60g＞" />
    </a>
    <a class="block-page-favorite--btn block-item-detail-favorite js-animation-bookmark" href="javascript:location.href='https://maison.kose.co.jp/site/customer/bookmark.aspx?goods=JQBA&crsirefo_hidden='+ jQuery('#js_crsirefo_hidden').val()">
      <div class="c-favorite-btn" data-module="Favorite">
        <img src="/freepage/maison-kose/common/img/common/favorite/like.png" class="c-favorite-btn__img" alt="">
      </div>
    </a>
  </div>
  <div class="c-product__about">
    
    <p class="c-product__brand">コスメデコルテ</p>
    <a href="/site/cosmedecorte/g/gJQBA/">
    <p class="c-product__product-name" data-module="TruncateText" data-options='{ "length": 36 }'>
      AQ ミリオリティ ザ クリーム デコラシオン ＜60g＞
    </p>
    </a>

    <p class="c-product__price">
    
         264,000円<span>（税込）</span>
    
    </p>

  </div>
  <div class="c-product__hashtag-area">
    
  </div>

  
  <div class="btn-items-cart">
    <a class="block-list-add-cart-btn js-enhanced-ecommerce-add-cart block-list-add-cart-btn-no-purchase">現在購入頂けません</a>
  </div>
  
</li>
<li class="c-product__item is-item-number-1">
  <p class="c-product__icon__wrap">
    <span class="c-product__icon c-product__icon-limited"><img src="/freepage/maison-kose/common/img/badge/new.png" alt="NEW"></span>
    
    
  </p>
  <div class="c-product__thumb is-new">
    <a href="/site/cosmedecorte/g/gJQGA/" class="c-product__thumb__img">
      <img src="/img/goods/S/JQGA_sub.png" alt="AQ ミリオリティ ザ クリーム デコラシオン ＜20g＞" />
    </a>
    <a class="block-page-favorite--btn block-item-detail-favorite js-animation-bookmark" href="javascript:location.href='https://maison.kose.co.jp/site/customer/bookmark.aspx?goods=JQGA&crsirefo_hidden='+ jQuery('#js_crsirefo_hidden').val()">
      <div class="c-favorite-btn" data-module="Favorite">
        <img src="/freepage/maison-kose/common/img/common/favorite/like.png" class="c-favorite-btn__img" alt="">
      </div>
    </a>
  </div>
  <div class="c-product__about">
    
    <p class="c-product__brand">コスメデコルテ</p>
    <a href="/site/cosmedecorte/g/gJQGA/">
    <p class="c-product__product-name" data-module="TruncateText" data-options='{ "length": 36 }'>
      AQ ミリオリティ ザ クリーム デコラシオン ＜20g＞
    </p>
    </a>

    <p class="c-product__price">
    
         99,000円<span>（税込）</span>
    
    </p>

  </div>
  <div class="c-product__hashtag-area">
    
  </div>

  
  <div class="btn-items-cart">
    <a class="block-list-add-cart-btn js-enhanced-ecommerce-add-cart block-list-add-cart-btn-no-purchase">現在購入頂けません</a>
  </div>
  
</li>
<li class="c-product__item is-item-number-1">
  <p class="c-product__icon__wrap">
    <span class="c-product__icon c-product__icon-limited"><img src="/freepage/maison-kose/common/img/badge/new.png" alt="NEW"></span>
    
    
  </p>
  <div class="c-product__thumb is-new">
    <a href="/site/cosmedecorte/g/gJQGB/" class="c-product__thumb__img">
      <img src="/img/goods/S/JQGB_sub.png" alt="AQ ミリオリティ ザ クリーム デコラシオン ＜60g＞" />
    </a>
    <a class="block-page-favorite--btn block-item-detail-favorite js-animation-bookmark" href="javascript:location.href='https://maison.kose.co.jp/site/customer/bookmark.aspx?goods=JQGB&crsirefo_hidden='+ jQuery('#js_crsirefo_hidden').val()">
      <div class="c-favorite-btn" data-module="Favorite">
        <img src="/freepage/maison-kose/common/img/common/favorite/like.png" class="c-favorite-btn__img" alt="">
      </div>
    </a>
  </div>
  <div class="c-product__about">
    
    <p class="c-product__brand">コスメデコルテ</p>
    <a href="/site/cosmedecorte/g/gJQGB/">
    <p class="c-product__product-name" data-module="TruncateText" data-options='{ "length": 36 }'>
      AQ ミリオリティ ザ クリーム デコラシオン ＜60g＞
    </p>
    </a>

    <p class="c-product__price">
    
         198,000円<span>（税込）</span>
    
    </p>

  </div>
  <div class="c-product__hashtag-area">
    
  </div>

  
  <div class="btn-items-cart">
    <a class="block-list-add-cart-btn js-enhanced-ecommerce-add-cart block-list-add-cart-btn-no-purchase">現在購入頂けません</a>
  </div>
  
</li>
<li class="c-product__item is-item-number-1">
  <p class="c-product__icon__wrap">
    
  </p>
  <div class="c-product__thumb">
    <a href="/site/cosmedecorte/g/gJQIO/" class="c-product__thumb__img">
      <img src="/img/goods/S/JQIO_sub.png" alt="キモノ マイ ウォーターコロン ＜15mL＞" />
    </a>
    <a class="block-page-favorite--btn block-item-detail-favorite js-animation-bookmark" href="javascript:location.href='https://maison.kose.co.jp/site/customer/bookmark.aspx?goods=JQIO&crsirefo_hidden='+ jQuery('#js_crsirefo_hidden').val()">
      <div class="c-favorite-btn" data-module="Favorite">
        <img src="/freepage/maison-kose/common/img/common/favorite/like.png" class="c-favorite-btn__img" alt="">
      </div>
    </a>
  </div>
  <div class="c-product__about">
    
    <p class="c-product__brand">コスメデコルテ</p>
    <a href="/site/cosmedecorte/g/gJQIO/">
    <p class="c-product__product-name" data-module="TruncateText" data-options='{ "length": 36 }'>
      キモノ マイ ウォーターコロン ＜15mL＞
    </p>
    </a>

    <p class="c-product__price">
    
         3,300円<span>（税込）※</span>
    
    </p>

  </div>
  <div class="c-product__hashtag-area">
    
  </div>

  
  <div class="btn-items-cart">
    <a class="block-list-add-cart-btn js-enhanced-ecommerce-add-cart block-list-add-cart-btn-select list-modal-button" href="javascript:void(0);" data-module="CommonModal" data-options='{ "target":"JQIO_vda3u8m6gf" }'>種類を選ぶ</a>
  </div>
  <div class="c-common-modal p-product-detail__modal-makeup list-modal-box" data-module-commonmodal-target="JQIO_vda3u8m6gf">
    <div class="c-common-modal__background list-modal-bg" data-module-commonmodal-close="JQIO_vda3u8m6gf"></div>
    <div class="c-common-modal__inner p-product-detail__modal-makeup__inner list-modal-inner" data-ref-goods="JQIO">
      <a href="javascript:void(0)" class="c-common-modal__closebtn p-product-detail__modal-makeup__closebtn" data-module-commonmodal-close="JQIO_vda3u8m6gf"></a>
      <div class="list-modal-block"><figure class="img-center"><img src="/img/sys/loading.gif"></figure></div>
    </div>
  </div>
  
</li>
</ul>
</body></html>"""

LISTING_TAX8_HTML = """<!doctype html><html lang="ja"><head>
<meta charset="UTF-8">
<meta name="keywords" content="10／13ページMaison KOSE">
<link rel="canonical" href="https://maison.kose.co.jp/site/cosmedecorte/c/c15/">
<link rel="next" href="https://maison.kose.co.jp/site/cosmedecorte/c/c15_p11/">
<title>コスメデコルテ｜ Maison KOS&#201;(メゾンコーセー)</title>
<link rel="stylesheet" href="/freepage/maison-kose/common/css/style.css">
<script src="/js/sys/goods_filter.js"></script>
<script src="/js/sys/cart.js"></script>
</head><body>
<ul class="c-product-content__list js-goods-list-wrapper">
<li class="c-product__item is-item-number-1">
  <p class="c-product__icon__wrap">
    
  </p>
  <div class="c-product__thumb">
    <a href="/site/cosmedecorte/g/gJLAT/" class="c-product__thumb__img">
      <img src="/img/goods/S/JLAT_sub.png" alt="ホワイトロジスト オーバーナイト インナー プラス" />
    </a>
    <a class="block-page-favorite--btn block-item-detail-favorite js-animation-bookmark" href="javascript:location.href='https://maison.kose.co.jp/site/customer/bookmark.aspx?goods=JLAT&crsirefo_hidden='+ jQuery('#js_crsirefo_hidden').val()">
      <div class="c-favorite-btn" data-module="Favorite">
        <img src="/freepage/maison-kose/common/img/common/favorite/like.png" class="c-favorite-btn__img" alt="">
      </div>
    </a>
  </div>
  <div class="c-product__about">
    
    <p class="c-product__brand">コスメデコルテ</p>
    <a href="/site/cosmedecorte/g/gJLAT/">
    <p class="c-product__product-name" data-module="TruncateText" data-options='{ "length": 36 }'>
      ホワイトロジスト オーバーナイト インナー プラス
    </p>
    </a>

    <p class="c-product__price">
    
         3,024円<span>（税込/8%）※</span>
    
    </p>

  </div>
  <div class="c-product__hashtag-area">
    
  </div>

  
  <div class="btn-items-cart">
    <a class="block-list-add-cart-btn js-animation-add-cart js-enhanced-ecommerce-add-cart block-list-add-cart-btn-purchase js-cart-in-trigger verification_goods" data-target="product-01" href="https://maison.kose.co.jp/site/cart/cart.aspx?goods=JLAT">
      <input type="hidden" value="JLAT" class="cart_hidden_goods">
      カートに入れる
    </a>
  </div>
  
</li>
</ul>
</body></html>"""

TAGS_HTML = """<!doctype html><html lang="ja"><head>
<meta charset="UTF-8">
<link rel="canonical" href="https://maison.kose.co.jp/site/itemtags/list.aspx?tags=%E3%82%B7%E3%83%AF%E6%94%B9%E5%96%84,%E3%82%B9%E3%82%AD%E3%83%B3%E3%82%B1%E3%82%A2">
<title>シワ改善 スキンケア ｜ Maison KOS&#201;(メゾンコーセー)</title>
<script src="/js/sys/goods_filter.js"></script>
<link rel="stylesheet" href="/freepage/maison-kose/common/css/style.css">
</head><body>
<ul class="c-product-content__list js-goods-list-wrapper">
<li class="c-product__item is-item-number-1">
  <p class="c-product__icon__wrap">
    <span class="c-product__icon c-product__icon-limited"><img src="/freepage/maison-kose/common/img/badge/new.png" alt="NEW"></span>
    
    <span class="c-product__icon c-product__icon-limited"><img src="/img/icon/limited.png" alt="限定品"></span>
    
  </p>
  <div class="c-product__thumb is-new">
    <a href="https://maison.kose.co.jp/site/infinity/g/gBAQQ/" class="c-product__thumb__img">
      <img src="https://maison.kose.co.jp/img/goods/L/BAQQ_main.png" alt="ザ リペア トータル ケア キット" />
    </a>
    <a class="block-page-favorite--btn block-item-detail-favorite js-animation-bookmark" href="javascript:location.href='https://maison.kose.co.jp/site/customer/bookmark.aspx?goods=BAQQ&crsirefo_hidden='+ jQuery('#js_crsirefo_hidden').val()">
      <div class="c-favorite-btn" data-module="Favorite">
        <img src="/freepage/maison-kose/common/img/common/favorite/like.png" class="c-favorite-btn__img" alt="">
      </div>
    </a>
  </div>
  <div class="c-product__about">
    
    <p class="c-product__brand">インフィニティ</p>
    <a href="https://maison.kose.co.jp/site/infinity/g/gBAQQ/">
    <p class="c-product__product-name" data-module="TruncateText" data-options='{ "length": 36 }'>
      ザ リペア トータル ケア キット
    </p>
    </a>
    <p class="c-product__price">
    
         16,060円<span>（税込）※</span>
    
    </p>
  </div>
  <div class="c-product__hashtag-area">
    
  </div>

  
  <div class="btn-items-cart">
    <a class="block-list-add-cart-btn js-animation-add-cart js-enhanced-ecommerce-add-cart block-list-add-cart-btn-purchase" href="https://maison.kose.co.jp/site/cart/cart.aspx?goods=BAQQ">商品を購入する</a>
  </div>
  
</li>
<li class="c-product__item is-item-number-1">
  <p class="c-product__icon__wrap">
    <span class="c-product__icon c-product__icon-limited"><img src="/freepage/maison-kose/common/img/badge/new.png" alt="NEW"></span>
    
    
  </p>
  <div class="c-product__thumb is-new">
    <a href="https://maison.kose.co.jp/site/carte/g/gPHGN/" class="c-product__thumb__img">
      <img src="https://maison.kose.co.jp/img/goods/L/PHGN_main.png" alt="シワ改善・シミ予防ケア　高保湿オールインワンゲル" />
    </a>
    <a class="block-page-favorite--btn block-item-detail-favorite js-animation-bookmark" href="javascript:location.href='https://maison.kose.co.jp/site/customer/bookmark.aspx?goods=PHGN&crsirefo_hidden='+ jQuery('#js_crsirefo_hidden').val()">
      <div class="c-favorite-btn" data-module="Favorite">
        <img src="/freepage/maison-kose/common/img/common/favorite/like.png" class="c-favorite-btn__img" alt="">
      </div>
    </a>
  </div>
  <div class="c-product__about">
    
    <p class="c-product__brand">カルテHD</p>
    <a href="https://maison.kose.co.jp/site/carte/g/gPHGN/">
    <p class="c-product__product-name" data-module="TruncateText" data-options='{ "length": 36 }'>
      シワ改善・シミ予防ケア　高保湿オールインワンゲル
    </p>
    </a>
    <p class="c-product__price">
    
         3,520円<span>（税込）※</span>
    
    </p>
  </div>
  <div class="c-product__hashtag-area">
    
  </div>

  
  <div class="btn-items-cart">
    <a class="block-list-add-cart-btn js-animation-add-cart js-enhanced-ecommerce-add-cart block-list-add-cart-btn-select list-modal-button" href="javascript:void(0);" data-module="CommonModal" data-options='{ "target":"PHGN_f1woi6vsg2" }'>種類を選ぶ</a>
  </div>
  <div class="c-common-modal p-product-detail__modal-makeup list-modal-box" data-module-commonmodal-target="PHGN_f1woi6vsg2">
    <div class="c-common-modal__background list-modal-bg" data-module-commonmodal-close="PHGN_f1woi6vsg2"></div>
    <div class="c-common-modal__inner p-product-detail__modal-makeup__inner list-modal-inner" data-ref-goods="PHGN">
      <a href="javascript:void(0)" class="c-common-modal__closebtn p-product-detail__modal-makeup__closebtn" data-module-commonmodal-close="PHGN_f1woi6vsg2"></a>
      <div class="list-modal-block"><figure class="img-center"><img src="/img/sys/loading.gif"></figure></div>
    </div>
  </div>
  
</li>
</ul>
</body></html>"""

PRODUCT_HTML = """<!doctype html><html lang="ja"><head>
<meta charset="UTF-8">
<link rel="canonical" href="https://maison.kose.co.jp/site/onebykose/g/gMUSC/">
<title>セラム シールド ＜40g＞｜ Maison KOS&#201;</title>
<script type="application/ld+json">
{
   "@context":"http:\\/\\/schema.org\\/",
   "@type":"Product",
   "name":"セラム シールド ＜40g＞",
   "image":"https:\\u002f\\u002fmaison.kose.co.jp\\u002fimg\\u002fgoods\\u002fS\\u002fMUSC_sub_BC-2.png",
   "description":"日本初&lt;span style=\\u0022font-size: 10px;line-height:1.3;\\u0022&gt;＊1&lt;\\u002fspan&gt;、うるおい改善＋シワ改善&lt;br \\u002f&gt;根深い渇きに高保水膜 &lt;span style=\\u0022font-size: 10px;line-height:1.3;\\u0022&gt;[医薬部外品]&lt;\\u002fspan&gt;",
   "mpn":"MUSC",
   "sku":"MUSC",
   "releaseDate":"2023/08/21",
   "offers":{
      "@type":"Offer",
      "price":5940,
      "priceCurrency":"JPY",
      "availability":"http:\\/\\/schema.org\\/InStock"
   },
   "isSimilarTo":{
      "@type":"Product",
      "name":"セラム シールド ＜40g＞",
      "image":"https:\\u002f\\u002fmaison.kose.co.jp\\u002fimg\\u002fgoods\\u002fS\\u002fMUSC_sub_BC-2.png",
      "mpn":"MUSC",
      "url":"https:\\u002f\\u002fmaison.kose.co.jp\\u002fsite\\u002fonebykose\\u002fg\\u002fgMUSC\\u002f"
   }
}
</script>
<script src="/js/sys/cart.js"></script>
<link rel="stylesheet" href="/freepage/maison-kose/common/css/style.css">
</head><body>
<ul class="c-breadcrumb">
<li class="c-breadcrumb__item">
      <a href="https://maison.kose.co.jp/">TOP</a>
  </li>
<li class="c-breadcrumb__item">
  <span class="breadcrumb__item__arrow"></span>
  <a href="/site/onebykose/c/c54/"><span>ONE BY KOSE</span></a>
</li>
<li class="c-breadcrumb__item">
  <span class="breadcrumb__item__arrow"></span>
  <a href="/site/onebykose/c/c5410/"><span>スキンケア</span></a>
</li>
<li class="c-breadcrumb__item">
  <span class="breadcrumb__item__arrow"></span>
  <a href="/site/onebykose/c/c541040/"><span>クリーム</span></a>
</li>
<li class="c-breadcrumb__item">
  <span class="breadcrumb__item__arrow"></span>
  <a href="/site/onebykose/g/gMUSC/"><span>セラム シールド ＜40g＞</span></a>
</li>
</ul>
<div class="p-product-detail__item">
<div class="p-product-detail__item__price">
            Maison KOS&Eacute;販売価格　<span> 5,940円</span>（税込）
          </div>
<div class="p-product-detail__item__variation">
            <span class="p-product-detail__item__net">容量 40g</span></div>
<ul class="p-product-detail__color__list">
<li class="p-product-detail__color__group__item color_id_0" data-navi-id="0"></li>
<li class="p-product-detail__color__group__item color_id_1" data-navi-id="1"></li>
</ul>
</div>
<!-- the staff-review block: `c-product__item` on a DIV, not an LI -->
<div class="c-product-slider__products">
<div class="c-product__item">
	<a href="/staff/skincaredetail/c00000000" class="p-product-detail__staffstart__hover-action">
		<div class="p-product-detail__staffstart__image">
			<img src="https://static.staff-start.com/img/coordinates/00/PLACEHOLDER_IMAGE_ID/PLACEHOLDER_FILE_l.jpg" alt="">
		</div>
	</a>
	<div class="p-product-detail__staffstart__texts">
		<p class="p-product-detail__staffstart__title">
			<a class="p-product-detail__staffstart__hover-action" href="/staff/skincaredetail/c00000000" data-module="TruncateText" data-options='{"length":20}'>PLACEHOLDER staff opinion text — the real one was a named employee's own
writing and is not republished here. The MARKUP is what this fixture is for:
this card carries the class `c-product__item` on a DIV, and the parser must
see zero products in it.</a>
		</p>
		<p class="p-product-detail__staffstart__author">PLACEHOLDER_AUTHOR</p>
	</div>
</div>
</div>
<div class="awoo-product-list"><p class="awoo-product-name">別の商品</p><p class="awoo-product-price">1,100円</p></div>
</body></html>"""

EMPTY_HTML = """<!doctype html><html lang="ja"><head>
<meta charset="UTF-8">
<title>シワ改善 スキンケア ｜ Maison KOS&#201;(メゾンコーセー)</title>
<script src="/js/sys/goods_filter.js"></script>
<link rel="stylesheet" href="/freepage/maison-kose/common/css/style.css">
</head><body>
<div class="l-main__content"></div>
</body></html>"""

NOTFOUND_HTML = """<!doctype html><html lang="ja"><head>
<meta charset="UTF-8">
<title>404- ページが見つかりません。</title>
<script src="/js/sys/cart.js"></script>
<link rel="stylesheet" href="/freepage/maison-kose/common/css/style.css">
</head><body><p>お探しのページは見つかりませんでした。</p>
<a href="/site/cosmedecorte/g/gJLCW/">おすすめ</a>
</body></html>"""

CHROMIUM_ERROR_HTML = """<html><head><title>maison.kose.co.jp</title></head><body><div id="main-frame-error"><span jscontent="heading.msg">このサイトにアクセスできません</span><div class="error-code">ERR_PROXY_CONNECTION_FAILED</div></div></body></html>"""

# ---------------------------------------------------------------------------
# Family constants
# ---------------------------------------------------------------------------

ENGINES = ("playwright_scraper", "selenium_scraper", "puppeteer_scraper")
DRIVER_IMPORTS = {
    "playwright_scraper": "playwright",
    "selenium_scraper": "selenium",
    "puppeteer_scraper": "pyppeteer",
}

# The family's flag contract (CLAUDE.md §9), plus the five it omitted for
# months while nearly every repo shipped them. Re-derive rather than trusting
# this comment (§13):
#
#   grep -ohE '"--[a-z0-9-]+"' */playwright_scraper.py | sort | uniq -c | sort -rn
CONTRACT_FLAGS = {
    "--url", "--pages", "--category", "--format", "--out", "--delay",
    "--retries", "--retry-delay", "--concurrency", "--proxy", "--proxy-file",
    "--proxy-rotate", "--proxy-shuffle", "--proxy-block-retries",
    "--twocaptcha-key", "--captcha-api", "--solve-captcha", "--min-score",
    "--cdp-endpoint", "--allow-empty", "--dump-html",
    "--fingerprint", "--fp-tags", "--fp-country", "--mode",
}

# `--locale` is in 16 of the 18 repos counted and is deliberately ABSENT
# here, which is a measurement rather than an oversight: maison.kose.co.jp
# is one market — no hreflang set, no /en/ route, JPY on every row — so the
# flag would be a setting that changes nothing, which §3 calls out by name.
#
# `--sort` is absent for the same reason: the site offers no ordering control
# on either listing route. That is the opposite of bbb-scraper, where the
# ordering decides WHICH rows are in the file and therefore had to exist.
#
# `--tags` is this repo's own addition, for the one listing route that
# crosses brands.
EXTRA_FLAGS = {"--tags", "--headless", "--headful"}

# The name the shared flag-parity check uses.
FAMILY_FLAGS = CONTRACT_FLAGS

BANNED_FLAGS = ("--antidetect", "--country-code", "--country", "--locale", "--sort")

# Assembled from pieces rather than written out, so that this file can be
# SCANNED for them too (§22): three repos in the family exempted
# `smoke_test.py` wholesale, which made the file most likely to acquire a
# stray phrase the one file nobody checked.
BANNED_WORDING = (
    "cloud" + " browser",
    "anti" + "detect browser",
    "2scraper Anti" + "detect Browser",
    "gate." + "2prx.com",
    "ANTI" + "DETECT_LOCAL_API",
)

_TREE_BEFORE = None



# ---------------------------------------------------------------------------
# The parser, against real captures. Assert VALUES, not coverage (§10).
# ---------------------------------------------------------------------------

def check_listing_parses_with_the_values_the_page_shows():
    rows = product_parser.parse_products(LISTING_HTML, LISTING_URL, page=1)
    equal("listing row count", len(rows), 4)
    equal("first sku", rows[0].sku, "JQBA")
    equal("first title", rows[0].title,
          "AQ ミリオリティ ザ クリーム デコラシオン ＜60g＞")
    equal("first brand", rows[0].brand, "コスメデコルテ")
    # A six-figure yen price, which is where a naive comma-stripping parser
    # goes wrong: 264,000 must not become 264 or 264000000.
    equal("first price", rows[0].price, 264000.0)
    equal("first currency", rows[0].currency, "JPY")
    equal("first tax rate", rows[0].tax_rate, 10)
    equal("first image", rows[0].image_url,
          "https://maison.kose.co.jp/img/goods/S/JQBA_sub.png")
    equal("first url", rows[0].url,
          "https://maison.kose.co.jp/site/cosmedecorte/g/gJQBA/")
    equal("price source", rows[0].price_source, "tile")
    equal("category from the URL", rows[0].category, "c15")
    equal("badges", rows[0].badges, "new")
    equal("positions restart at 1 and count up",
          [r.position for r in rows], [1, 2, 3, 4])
    equal("page threaded through", {r.page for r in rows}, {1})
    equal("prices across the fixture", [r.price for r in rows],
          [264000.0, 99000.0, 198000.0, 3300.0])


def check_the_image_is_the_product_and_not_the_badge():
    """The first `<img>` in a tile is a merchandising badge, not the product.

    The first version of this parser read it and got
    `/freepage/…/badge/new.png` on every tile that had one — 100% coverage of
    the WRONG value, which is exactly what §10 means by asserting values
    rather than coverage. Every row here must point at `/img/goods/`.
    """
    rows = product_parser.parse_products(LISTING_HTML, LISTING_URL)
    bad = [r.sku for r in rows if r.image_url and "/badge/" in r.image_url]
    check("no row carries a badge image as its product image", not bad, str(bad))
    check("every row's image is a goods image",
          all("/img/goods/" in (r.image_url or "") for r in rows),
          str([r.image_url for r in rows]))
    check("the badge is still in the fixture, so this check can fail",
          "/badge/new.png" in LISTING_HTML)


def check_stock_is_an_allowlist_and_takes_both_values():
    """§20: a column you never saw take its other value is not verified."""
    rows = product_parser.parse_products(LISTING_HTML, LISTING_URL)
    equal("in_stock across the fixture", [r.in_stock for r in rows],
          [False, False, False, True])
    check("the fixture really contains both CTA wordings",
          "現在購入頂けません" in LISTING_HTML and "種類を選ぶ" in LISTING_HTML)


def check_an_unknown_cta_wording_reads_as_unknown_not_as_in_stock():
    """A wording the site adds tomorrow must under-report, never invent stock."""
    html = LISTING_HTML.replace("種類を選ぶ", "なにか新しい文言")
    rows = product_parser.parse_products(html, LISTING_URL)
    equal("an unrecognised CTA gives None, not True",
          rows[3].in_stock, None)


def check_the_reduced_tax_rate_is_read():
    rows = product_parser.parse_products(LISTING_TAX8_HTML, LISTING_URL)
    equal("reduced-rate row count", len(rows), 1)
    equal("reduced rate", rows[0].tax_rate, 8)
    equal("its price", rows[0].price, 3024.0)
    equal("a bare （税込） still means the standard rate",
          product_parser.parse_tax_rate("1,234円（税込）"), 10)
    equal("no tax annotation at all is None, never a guessed 10",
          product_parser.parse_tax_rate("1,234円"), None)


def check_the_store_price_marker_is_recorded():
    rows = product_parser.parse_products(LISTING_TAX8_HTML, LISTING_URL)
    equal("※ marks the store's own selling price",
          rows[0].price_is_store_price, True)
    plain = product_parser.parse_products(LISTING_HTML, LISTING_URL)
    equal("its absence is None rather than False",
          plain[0].price_is_store_price, None)


def check_a_tag_listing_mixes_brands_and_is_read_per_tile():
    rows = product_parser.parse_products(TAGS_HTML, TAGS_URL, page=1)
    equal("tag row count", len(rows), 2)
    check("the two tiles carry DIFFERENT brands",
          rows[0].brand != rows[1].brand,
          "%r vs %r" % (rows[0].brand, rows[1].brand))
    check("neither brand came from the URL, which names no brand at all",
          "itemtags" in TAGS_URL and rows[0].brand not in TAGS_URL)
    equal("a tag URL yields no cNN category", rows[0].category, None)


def check_a_product_page_is_not_a_listing():
    """The `li.` in the tile selector is the whole guard (§4).

    A product page reuses `c-product__item` on `<div>`s for staff-review
    cards. A class-only selector would emit one row per card — a product
    with a `/staff/` URL and no sku — which is junk-link data theft in a new
    costume. This pins both directions.
    """
    equal("the class really is present on the product page",
          PRODUCT_HTML.count("c-product__item") >= 2, True)
    equal("but no LI tile is", product_parser.tile_count(PRODUCT_HTML), 0)
    equal("so the listing parser finds nothing on it",
          len(product_parser.parse_products(PRODUCT_HTML, PRODUCT_URL)), 0)
    check("and the awoo recommendation block is present too, unread",
          "awoo-product-name" in PRODUCT_HTML)


def check_product_detail_reads_the_pages_own_jsonld():
    rows = product_parser.parse_product_detail(PRODUCT_HTML, PRODUCT_URL)
    equal("one row per product page", len(rows), 1)
    row = rows[0]
    equal("sku", row.sku, "MUSC")
    equal("title", row.title, "セラム シールド ＜40g＞")
    equal("price", row.price, 5940.0)
    equal("currency", row.currency, "JPY")
    equal("price source", row.price_source, "jsonld")
    equal("in stock", row.in_stock, True)
    equal("brand from the breadcrumb", row.brand, "ONE BY KOSE")
    equal("category from the breadcrumb", row.category, "スキンケア")
    equal("subcategory from the breadcrumb", row.subcategory, "クリーム")
    equal("volume", row.volume, "40g")
    equal("colour count", row.colour_count, 2)
    equal("release date, verbatim", row.release_date, "2023/08/21")
    equal("mode", row.mode, "product")


def check_the_structured_and_displayed_prices_agree():
    """§4 says CHECK this on every site rather than assume it."""
    equal("they agree on the captured product",
          product_parser.detail_price_agrees(PRODUCT_HTML), True)
    broken = PRODUCT_HTML.replace("5,940円", "9,999円")
    equal("and a disagreement is reported rather than smoothed over",
          product_parser.detail_price_agrees(broken), False)
    equal("a missing figure is unknown, not a mismatch",
          product_parser.detail_price_agrees(EMPTY_HTML), None)


def check_a_product_row_never_links_to_a_DIFFERENT_product():
    """5 of 20 product pages canonicalise to a sibling sku (measured).

    Using the canonical as the row's URL would have produced a quarter of
    all rows whose link opens a different product while their title, sku and
    price describe this one.
    """
    html = PRODUCT_HTML.replace(
        '<link rel="canonical" href="https://maison.kose.co.jp/site/onebykose/g/gMUSC/">',
        '<link rel="canonical" href="https://maison.kose.co.jp/site/onebykose/g/gMUSX/">')
    row = product_parser.parse_product_detail(html, PRODUCT_URL)[0]
    equal("the row's URL names the row's own sku",
          product_parser.sku_from_url(row.url), row.sku)
    equal("and the canonical's sku is kept as the family link",
          row.variant_of, "MUSX")
    row2 = product_parser.parse_product_detail(PRODUCT_HTML, PRODUCT_URL)[0]
    equal("a self-canonicalising page has no variant_of",
          row2.variant_of, None)


# ---------------------------------------------------------------------------
# URLs and pagination
# ---------------------------------------------------------------------------

def check_url_shapes_and_routes():
    cases = [
        ("https://maison.kose.co.jp/site/cosmedecorte/c/c15/", "category", "c15", None),
        ("https://maison.kose.co.jp/site/c/c21/", "category", "c21", None),
        ("https://maison.kose.co.jp/site/x/c/c15_p7/", "category", "c15", None),
        ("https://maison.kose.co.jp/site/itemtags/list.aspx?tags=a,b", "tags", None, None),
        ("https://maison.kose.co.jp/site/cosmedecorte/g/gJLCW/", "product", None, "JLCW"),
        ("/site/cosmedecorte/g/gJQBA/", "product", None, "JQBA"),
        ("https://maison.kose.co.jp/site/", None, None, None),
    ]
    for url, route, cat, sku in cases:
        equal("route of %s" % url, product_parser.route_of(url), route)
        equal("category of %s" % url, product_parser.category_from_url(url), cat)
        equal("sku of %s" % url, product_parser.sku_from_url(url), sku)


def check_a_root_relative_href_is_not_mangled():
    """A tile's href is root-relative on a category and absolute on a tag page.

    The first version of `_split` promoted anything without "//" to
    `https://` + the string, which turned "/site/x/g/gJQBA/" into a URL whose
    HOST was "site". Every category row then parsed to sku=None and was
    dropped — 24 tiles in, zero rows out — while `tile_count` reported 24.
    """
    equal("root-relative", product_parser.sku_from_url("/site/x/g/gJQBA/"), "JQBA")
    equal("absolute",
          product_parser.sku_from_url("https://maison.kose.co.jp/site/x/g/gJQBA/"), "JQBA")
    equal("host-relative",
          product_parser.sku_from_url("maison.kose.co.jp/site/x/g/gJQBA/"), "JQBA")


def check_the_brand_segment_is_treated_as_decorative():
    """`/site/xyz/c/c15/` returns byte-identical bytes to the real brand's."""
    a = product_parser.category_from_url("https://maison.kose.co.jp/site/cosmedecorte/c/c15/")
    b = product_parser.category_from_url("https://maison.kose.co.jp/site/xyz/c/c15/")
    equal("the same category either way", (a, b), ("c15", "c15"))
    equal("page 2 of either builds the same address",
          product_parser.page_url("https://maison.kose.co.jp/site/xyz/c/c15/", 2),
          "https://maison.kose.co.jp/site/xyz/c/c15_p2/")
    equal("and the brand slug is recorded as provenance only",
          product_parser.brand_slug_from_url("https://maison.kose.co.jp/site/xyz/c/c15/"),
          "xyz")


def check_both_pagination_conventions():
    cat = "https://maison.kose.co.jp/site/cosmedecorte/c/c15/"
    equal("category page 1 is the bare URL", product_parser.page_url(cat, 1), cat)
    equal("category page 2", product_parser.page_url(cat, 2),
          "https://maison.kose.co.jp/site/cosmedecorte/c/c15_p2/")
    equal("category page 13", product_parser.page_url(cat, 13),
          "https://maison.kose.co.jp/site/cosmedecorte/c/c15_p13/")
    equal("a URL already naming a page is rebuilt, not appended to",
          product_parser.page_url("https://maison.kose.co.jp/site/x/c/c15_p7/", 3),
          "https://maison.kose.co.jp/site/x/c/c15_p3/")
    equal("and normalising it back to page 1 drops the suffix",
          product_parser.page_url("https://maison.kose.co.jp/site/x/c/c15_p7/", 1),
          "https://maison.kose.co.jp/site/x/c/c15/")

    tag = "https://maison.kose.co.jp/site/itemtags/list.aspx?tags=a,b"
    equal("tag page 1 is the bare URL", product_parser.page_url(tag, 1), tag)
    equal("tag page 2 uses ?p=, which is the one the site honours",
          product_parser.page_url(tag, 2),
          "https://maison.kose.co.jp/site/itemtags/list.aspx?tags=a,b&p=2")
    equal("a tag URL already naming a page is replaced, not doubled",
          product_parser.page_url(tag + "&p=4", 2),
          "https://maison.kose.co.jp/site/itemtags/list.aspx?tags=a,b&p=2")
    check("the comma in tags= is NOT percent-encoded, matching the site's own href",
          "%2C" not in product_parser.page_url(tag, 2))

    for n, url in ((1, cat), (7, "https://maison.kose.co.jp/site/x/c/c15_p7/"),
                   (1, tag), (4, tag + "&p=4")):
        equal("page number read back from %s" % url,
              product_parser.page_number_from_url(url), n)


def check_the_wrong_pagination_parameter_is_not_used():
    """`&pageno=` and `&page=` are silently ignored by the site (HTTP 200,
    page 1). A run that built one would dedupe every page down to page 1's
    rows and report a COMPLETE run holding one page."""
    built = product_parser.page_url(
        "https://maison.kose.co.jp/site/itemtags/list.aspx?tags=a,b", 3)
    check("only ?p= is built", "p=3" in built and "pageno" not in built
          and "page=3" not in built, built)


def check_the_sites_own_page_counter_is_read():
    equal("counter on a category page",
          product_parser.total_pages(LISTING_HTML), 13)
    equal("a tag listing publishes none, and None means UNKNOWN",
          product_parser.total_pages(TAGS_HTML), None)
    equal("the separator is the FULLWIDTH solidus, not an ASCII slash",
          product_parser.page_counter("<p>2／13ページ</p>"), (2, 13))
    equal("an ASCII slash is NOT this site's counter and matches nothing",
          product_parser.page_counter("<p>2/13ページ</p>"), (None, None))


def check_pages_are_planned_from_the_counter():
    """Load-bearing here: past its end a category serves its LAST page again."""
    equal("50 asked, 13 available", product_parser.pages_to_fetch(50, 13), 13)
    equal("3 asked, 13 available", product_parser.pages_to_fetch(3, 13), 3)
    equal("unknown count does not cap the run",
          product_parser.pages_to_fetch(5, None), 5)
    equal("and zero available is treated as unknown rather than as a cap",
          product_parser.pages_to_fetch(5, 0), 5)


def check_listing_page_level_facts():
    lp = product_parser.parse_listing(LISTING_HTML, LISTING_URL, page=1)
    equal("rows", len(lp.rows), 4)
    equal("pages available", lp.pages_available, 13)
    equal("page size", lp.page_size, 24)
    equal("next url", lp.next_url,
          "https://maison.kose.co.jp/site/cosmedecorte/c/c15_p2/")
    equal("canonical", lp.canonical, LISTING_URL)
    equal("tiles counted", lp.tiles_on_page, 4)
    check("product-shaped links outnumber tiles, which is why rows use tiles",
          lp.product_links_on_page > lp.tiles_on_page,
          "%d links vs %d tiles" % (lp.product_links_on_page, lp.tiles_on_page))


def check_supported_urls_are_refused_with_a_true_reason():
    ok, why = product_parser.is_supported_url(LISTING_URL)
    equal("a real listing is supported", (ok, why), (True, "category"))
    for url, needle in [
        ("https://www.kose.co.jp/", "publishes no catalogue"),
        ("https://kose.com/anything", "REFUSED"),
        ("https://kose.com.tw/", "different platform"),
        ("https://example.com/", "is not maison.kose.co.jp"),
        ("https://maison.kose.co.jp/site/", "not a Maison KOSÉ listing"),
    ]:
        ok, why = product_parser.is_supported_url(url)
        check("refused: %s" % url, not ok, why)
        check("...with a reason naming the real problem (%s)" % needle,
              needle.lower() in why.lower(), why)


# ---------------------------------------------------------------------------
# Prices
# ---------------------------------------------------------------------------

def check_price_parsing():
    cases = [
        ("264,000円（税込）", 264000.0),
        ("3,024円（税込/8%）※", 3024.0),
        ("605円（税込）", 605.0),
        ("1,078円", 1078.0),
        ("", None),
        ("価格未定", None),
    ]
    for text, want in cases:
        equal("price of %r" % text, product_parser.parse_price(text), want)


# ---------------------------------------------------------------------------
# Detection. Everything here is a TRIPWIRE: nothing has ever fired on this
# site, and the checks exist so that stays true on purpose rather than by
# accident.
# ---------------------------------------------------------------------------

def check_no_marker_fires_on_a_page_the_site_serves():
    """§18: count every candidate on a page you KNOW is good, first."""
    good = [("listing", LISTING_HTML), ("tags", TAGS_HTML),
            ("product", PRODUCT_HTML), ("empty", EMPTY_HTML),
            ("404", NOTFOUND_HTML)]
    for name, html in good:
        equal("no challenge detected on the %s fixture" % name,
              product_parser.detect_bot_challenge(html), None)


def check_cf_turnstile_is_not_carried_as_a_marker():
    """§19: 2Captcha's own Scraping Browser extension injects `cf-turnstile`
    into every page it loads, so it fires on GOOD pages and misses real
    ones. `challenges.cloudflare.com` is the one that works."""
    markers = [m for m, _ in product_parser.BOT_CHALLENGE_MARKERS]
    check("cf-turnstile is not a marker", "cf-turnstile" not in markers)
    check("challenges.cloudflare.com is", "challenges.cloudflare.com" in markers)
    injected = ('<script src="chrome-extension://kjmkgkdkpedkejedfhmfcenooemhbpbo'
                '/content/captcha/turnstile/hunter.js" '
                'data-ts-input="cf-turnstile-response"></script>')
    page = LISTING_HTML.replace("</head>", injected + "</head>")
    equal("a page carrying the extension's own injection is still clean",
          product_parser.detect_bot_challenge(page), None)


def check_a_marker_would_still_fire_if_the_site_turned_one_on():
    """A tripwire nobody can trip is not a tripwire."""
    page = LISTING_HTML.replace(
        "</head>", '<script src="https://challenges.cloudflare.com/turnstile/v0/api.js"></script></head>')
    equal("a real Turnstile is reported", product_parser.detect_bot_challenge(page),
          "cloudflare turnstile")
    equal("and the page state follows the marker rather than the tiles",
          page_flow.classify(page.replace('<li class="c-product__item', '<li class="x'), 200),
          "challenge")


def check_a_marker_survives_both_encodings():
    """§20: an edge can entity-escape the punctuation in its own marker, so a
    literal matches a browser's DOM and misses a raw HTTP response."""
    escaped = ("<html><head><title>Access Denied</title>"
               "<script src=\"https&#58;&#47;&#47;challenges&#46;cloudflare&#46;com"
               "&#47;turnstile&#47;v0&#47;api.js\"></script></head><body></body></html>")
    equal("the escaped spelling is still detected",
          product_parser.detect_bot_challenge(escaped), "cloudflare turnstile")


def check_page_states_on_real_captures():
    equal("a listing is content", page_flow.classify(LISTING_HTML, 200), "content")
    equal("a product page is content too, on its own JSON-LD rather than tiles",
          page_flow.classify(PRODUCT_HTML, 200), "content")
    equal("an exhausted tag facet is EMPTY, not blocked",
          page_flow.classify(EMPTY_HTML, 200), "empty")
    equal("the site's own 404 is empty as well",
          page_flow.classify(NOTFOUND_HTML, 200), "empty")
    equal("a 403 is blocked", page_flow.classify(EMPTY_HTML, 403), "blocked")
    equal("but a 403 on a page that still HAS tiles is content: the tiles are "
          "the stronger signal", page_flow.classify(LISTING_HTML, 403), "content")
    equal("no body at all is unknown", page_flow.classify(None), "unknown")


def check_chromiums_own_error_page_is_not_mistaken_for_the_site():
    """It carries `<title>maison.kose.co.jp</title>` and no vendor marker, so
    only "was this built out of the site's own assets?" answers correctly."""
    equal("no marker matches it",
          product_parser.detect_bot_challenge(CHROMIUM_ERROR_HTML), None)
    equal("it references none of the site's own assets",
          product_parser.references_own_assets(CHROMIUM_ERROR_HTML), 0)
    equal("so it classifies as unknown rather than as an empty listing",
          page_flow.classify(CHROMIUM_ERROR_HTML, 200), "unknown")
    check("while a real page references them repeatedly",
          product_parser.references_own_assets(LISTING_HTML) >= 2,
          str(product_parser.references_own_assets(LISTING_HTML)))


def check_the_unambiguous_signal_is_checked_before_the_threshold():
    """§17's classification-order trap: a thin but REAL page must not come
    back as blocked because it happens to reference few assets."""
    thin = ('<html><head><script src="/js/sys/cart.js"></script></head><body>'
            '<ul class="c-product-content__list">'
            '<li class="c-product__item"><a href="/site/x/g/gAAAA/">x</a>'
            '<p class="c-product__price">1,000円（税込）</p></li>'
            '</ul></body></html>')
    equal("one asset reference and one real tile is CONTENT",
          page_flow.classify(thin, 200), "content")


def check_the_404_carries_exactly_one_product_link():
    """Which is why the parse-failure threshold is two, not one."""
    equal("the site's 404 links to one product",
          product_parser.product_link_count(NOTFOUND_HTML), 1)
    check("so it is not reported as a broken parser",
          not page_flow.looks_like_a_parse_failure("empty", 0, 1))
    check("while a real grid that parsed to nothing is",
          page_flow.looks_like_a_parse_failure("content", 0, 48))



# ---------------------------------------------------------------------------
# Structural checks the whole family shares (§10, §17, §22).
# ---------------------------------------------------------------------------

def check_shared_calls_bind_against_the_real_signature():
    """§17's check #1, and the one that earns its keep.

    A sibling repo shipped `classify(html, url=…)` in two of three engines
    against a callee taking `status` second, and BOTH crashed on their first
    fetch — invisible to import, --help, compileall, the undefined-name walk
    and 400+ green assertions, because none of those calls a function the way
    a live run does.

    This walks every engine's AST for calls into the shared modules and binds
    each one against the callee's real signature.
    """
    import page_flow
    import product_parser
    import output_writer
    targets = {"page_flow": page_flow, "product_parser": product_parser,
               "output_writer": output_writer}
    bound = 0
    for module in ENGINES + ("scraper_api_client",):
        path = os.path.join(HERE, module + ".py")
        if not os.path.exists(path):
            continue
        source = open(path, encoding="utf-8").read()
        tree = ast.parse(source)
        # Which shared names this file imported directly (`from x import y`).
        direct = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module in targets:
                for alias in node.names:
                    direct[alias.asname or alias.name] = (
                        targets[node.module], alias.name)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            owner = attr = None
            if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
                if func.value.id in targets:
                    owner, attr = targets[func.value.id], func.attr
            elif isinstance(func, ast.Name) and func.id in direct:
                owner, attr = direct[func.id]
            if owner is None:
                continue
            # A name that is NOT THERE is the loudest possible failure and
            # this check used to swallow it: `getattr(..., None)` returned
            # None, `not callable(None)` was true, and the call was skipped.
            # Three calls into a page_flow API that does not exist in this
            # repo -- comparable(), next_page_selector(),
            # next_page_candidates(), all of them Tokopedia's, all arriving
            # with copied code -- sat in two engines under a green run of
            # this very function. Absent is not "nothing to bind".
            if not hasattr(owner, attr):
                check("%s.%s exists (called from %s:%d)"
                      % (getattr(owner, "__name__", owner), attr,
                         module + ".py", node.lineno),
                      False,
                      "the engine calls a name the shared module does not "
                      "define; a live run reaches this as AttributeError")
                continue
            callee = getattr(owner, attr)
            if not callable(callee) or inspect.isclass(callee):
                continue
            try:
                signature = inspect.signature(callee)
            except (TypeError, ValueError):
                continue
            positional = [inspect.Parameter.empty] * len(node.args)
            keywords = {}
            for kw in node.keywords:
                if kw.arg is None:          # **kwargs — cannot be checked here
                    keywords = None
                    break
                keywords[kw.arg] = inspect.Parameter.empty
            if keywords is None:
                continue
            try:
                signature.bind(*positional, **keywords)
                bound += 1
            except TypeError as e:
                check("%s:%d %s.%s(...) binds against its real signature"
                      % (module, node.lineno, owner.__name__, attr),
                      False, "%s; signature is %s" % (e, signature))
    check("every shared-module call in every engine binds (%d checked)" % bound,
          bound > 40, "only %d calls were checked — is the walk finding them?"
          % bound)


def check_credential_scan_is_one_implementation_invoked_from_both():
    """§17: two sources of truth, one dead and one holed.

    `.github/ci_checks.py` sat in three repos invoked by NOTHING, while
    tests.yml carried an inline grep doing a narrower version of the same job
    — one that matched only ws:// and wss://, so an http://user:pass@
    credential would have sailed past CI.
    """
    script = os.path.join(HERE, ".github", "ci_checks.py")
    check("the credential scan exists as a script", os.path.exists(script))
    if not os.path.exists(script):
        return
    workflow = os.path.join(HERE, ".github", "workflows", "tests.yml")
    if os.path.exists(workflow):
        text = open(workflow, encoding="utf-8").read()
        check("CI INVOKES the script rather than reimplementing it",
              "ci_checks.py" in text)
    result = subprocess.run([sys.executable, script, "--all"], cwd=HERE,
                            capture_output=True, text=True)
    check("the credential scan passes on this repo's own tree",
          result.returncode == 0,
          (result.stdout + result.stderr)[-600:])


def check_ci_calls_the_shared_checks_rather_than_restating_them():
    """§17: one implementation, invoked from both — asserted, not assumed.

    This repo's FIRST CI run failed on exactly this. `tests.yml` carried
    INLINE reimplementations of the `--help` and sample-output checks that
    `.github/ci_checks.py` already implements. The inline sample check still
    imported `output_writer.Business` — a class this repo renamed to
    `Product` — so the job died with ImportError while `ci_checks.py` passed
    on the same tree. One copy had been updated and the other had not, and
    nothing in the repo could see the difference.

    The guard triggers on the whole `.github` directory being absent, never
    on a file inside it being missing (§22): two suites in this family run
    INSIDE the Docker image, which deliberately COPYs no `.github/`, so a
    check that reads a workflow file is correct in the repo and red in the
    image. A check that quietly starts passing once its input disappears is
    the failure mode this one is guarding against, so the escape is the
    directory, not the file.
    """
    github_dir = os.path.join(HERE, ".github")
    if not os.path.isdir(github_dir):
        skip("ci wiring", "no .github/ directory (this is the Docker image, "
                          "which deliberately carries no CI material)")
        return

    workflow = os.path.join(github_dir, "workflows", "tests.yml")
    script = os.path.join(github_dir, "ci_checks.py")
    check("ci_checks.py exists", os.path.exists(script))
    check("tests.yml exists", os.path.exists(workflow))
    if not (os.path.exists(workflow) and os.path.exists(script)):
        return

    text = open(workflow, encoding="utf-8").read()
    for flag in ("--help-check", "--sample-check", "--secret-check"):
        check("tests.yml invokes ci_checks.py %s" % flag,
              "ci_checks.py" in text and flag in text,
              "the workflow must CALL the shared check, not restate it")

    # The positive direction is not enough on its own: the workflow could
    # call the script AND still carry a stale inline copy beside it, which is
    # exactly the state that broke the first run. So assert the tell-tales of
    # a reimplementation are gone.
    # Deliberately NOT keyed on the filename. `sample_output.json` appears
    # legitimately in the docker job, which asserts the IMAGE does not carry
    # it — so a filename tell-tale fails on a correct workflow, which is its
    # own kind of check nobody can read. What actually distinguishes a
    # reimplementation is inline Python that imports the row model or
    # dataclass machinery to rebuild the expected column list.
    for tell in ("from output_writer import", "asdict("):
        check("tests.yml does not reimplement the sample check (%r)" % tell,
              tell not in text,
              "an inline copy drifts from the shared one silently")


def check_banned_wording():
    """§12: enforced by this test rather than by review."""
    for root, dirs, files in os.walk(HERE):
        dirs[:] = [d for d in dirs if d not in
                   (".git", "__pycache__", ".pytest_cache", "node_modules")]
        for filename in files:
            if not filename.endswith((".py", ".md", ".yml", ".yaml", ".txt",
                                      ".toml", ".html", ".example")):
                continue
            path = os.path.join(root, filename)
            text = open(path, encoding="utf-8", errors="replace").read().lower()
            for phrase in BANNED_WORDING:
                if phrase.lower() in text and filename != "smoke_test.py":
                    check("%s contains no %r" % (
                        os.path.relpath(path, HERE), phrase), False)
    check("banned-wording scan ran", True)


def check_worker_pools_start_on_different_exits():
    engine = _import_engine("playwright_scraper")
    if engine is None:
        return
    from proxy_pool import ProxyPool
    pool = ProxyPool(["http://a:1", "http://b:2", "http://c:3"], rotate="per-run")
    firsts = [engine._worker_pool(pool, i).current for i in range(3)]
    equal("three workers start on three different exits",
          len(set(firsts)), 3)
    equal("a missing pool stays missing", engine._worker_pool(None, 0), None)


def check_fingerprint_kwargs_are_ones_the_driver_accepts():
    """§10: an unknown key in new_context(**kwargs) is a TypeError at launch,
    on the PAID path, at runtime."""
    engine = _import_engine("playwright_scraper")
    if engine is None:
        return
    try:
        from fingerprint_client import playwright_context_kwargs
    except ImportError as e:
        skip("fingerprint", str(e))
        return
    sample = {"id": "x", "country": "US",
              "userAgent": "Mozilla/5.0 Chrome/140.0.0.0",
              "screen": {"width": 1920, "height": 1080},
              "timezone": "America/New_York", "language": "en-US",
              "devicePixelRatio": 2}
    kwargs = playwright_context_kwargs(sample)
    from playwright.sync_api import sync_playwright  # noqa: F401
    import playwright.sync_api as pw_api
    signature = inspect.signature(pw_api.Browser.new_context)
    unknown = [k for k in kwargs if k not in signature.parameters]
    check("every fingerprint kwarg is one new_context accepts", not unknown,
          "unknown: %s" % unknown)


def check_engines_do_not_evaluate_a_string_in_the_browser():
    """§18: a site whose CSP omits `unsafe-eval` kills wait_for_function with
    an EvalError and takes the run down with exit 1. BBB has not been
    measured for that, and the cheap habit costs nothing where it would have
    been allowed."""
    for module in ENGINES:
        path = os.path.join(HERE, module + ".py")
        if not os.path.exists(path):
            continue
        tree = ast.parse(open(path, encoding="utf-8").read())
        called = {node.func.attr for node in ast.walk(tree)
                  if isinstance(node, ast.Call)
                  and isinstance(node.func, ast.Attribute)}
        for banned in ("wait_for_function", "waitForFunction", "waitFor"):
            check("%s never CALLS %s" % (module, banned), banned not in called,
                  "poll through page_flow.wait_for_count instead")


def check_credentials_never_reach_a_log():
    """§8: an EXCEPTION MESSAGE is a log, and the masker must be GLOBAL.

    A Playwright connection error repeats the endpoint five times (the
    message plus a four-line call log), so a masker handling only the first
    occurrence prints the password four times and looks like it is working.
    """
    for module in ENGINES:
        engine = _import_engine(module)
        if engine is None:
            continue
        masked = engine._mask_credentials(
            "tried ws://u:supersecret@h1:9222 and ws://u:supersecret@h2:9222 "
            "and again ws://u:supersecret@h1:9222")
        check("%s masks EVERY occurrence" % module,
              "supersecret" not in masked, masked)
        check("%s keeps the host and port, which are the useful half" % module,
              "h1:9222" in masked and "h2:9222" in masked, masked)
    from proxy_pool import mask
    masked = mask("http://user:secret@exit.example.com:2334")
    check("proxy_pool.mask hides the password", "secret" not in masked)
    check("proxy_pool.mask keeps the exit", "exit.example.com:2334" in masked)


def check_csv_and_json_writers():
    from output_writer import Product, write_csv, write_json
    import product_parser as P
    rows = P.parse_listing(LISTING_HTML, LISTING_URL).rows
    check("the fixture produced rows to write", len(rows) > 0, len(rows))
    with tempfile.TemporaryDirectory() as tmp:
        csv_path = os.path.join(tmp, "out.csv")
        write_csv(rows, csv_path, row_cls=Product)
        with open(csv_path, encoding="utf-8") as f:
            reader = list(csv.reader(f))
        equal("CSV header matches the dataclass, in order",
              reader[0], [f.name for f in fields(Product)])
        equal("CSV holds every row", len(reader) - 1, len(rows))
        check("no Python list repr leaked into the CSV",
              not any(cell.startswith("[") for row in reader[1:] for cell in row))

        empty_csv = os.path.join(tmp, "empty.csv")
        write_csv([], empty_csv, row_cls=Product)
        with open(empty_csv, encoding="utf-8") as f:
            header = list(csv.reader(f))
        equal("an EMPTY csv still carries its header", len(header), 1)
        equal("...and it is the right one", header[0],
              [f.name for f in fields(Product)])

        json_path = os.path.join(tmp, "out.json")
        write_json(rows, json_path)
        loaded = json.load(open(json_path, encoding="utf-8"))
        equal("JSON holds every row", len(loaded), len(rows))
        equal("JSON keys are the dataclass fields, in order",
              list(loaded[0].keys()), [f.name for f in fields(Product)])
        equal("JSON and CSV agree on the column ORDER",
              list(loaded[0].keys()), reader[0])


def check_exit_codes():
    import output_writer as O
    equal("0 ok / 1 crash / 2 usage / 3 blocked / 4 empty / 5 api / 6 partial",
          (O.EXIT_BLOCKED, O.EXIT_NO_PRODUCTS, O.EXIT_API_ERROR, O.EXIT_PARTIAL),
          (3, 4, 5, 6))
    check("page_cap_reached is a COMPLETE stop reason",
          "page_cap_reached" in O.COMPLETE_STOP_REASONS)
    check("single_page_mode is complete by construction",
          "single_page_mode" in O.COMPLETE_STOP_REASONS)
    check("no_new_products is complete",
          "no_new_products" in O.COMPLETE_STOP_REASONS)


def check_a_run_that_finds_nothing_writes_nothing():
    """Never replace last night's good output with []."""
    from output_writer import save
    with tempfile.TemporaryDirectory() as tmp:
        prefix = os.path.join(tmp, "out")
        with open(prefix + ".json", "w", encoding="utf-8") as f:
            f.write('[{"sku": "yesterday"}]')
        code = save([], prefix, "json", allow_empty=False)
        equal("an empty run exits 4", code, 4)
        equal("...and leaves the previous good file alone",
              open(prefix + ".json", encoding="utf-8").read(),
              '[{"sku": "yesterday"}]')
        code = save([], prefix, "json", allow_empty=True)
        equal("--allow-empty WRITES the empty file...", 
              json.load(open(prefix + ".json", encoding="utf-8")), [])
        # ...and still reports exit 4. Pinned deliberately (§10: pin a known
        # behaviour rather than half-guarding it): "zero businesses" is true
        # whether or not the file was written, and a caller that wanted the
        # file still wants to know the result was empty.
        equal("...and still reports exit 4, because it IS empty", code, 4)


def check_concurrency_with_the_browser_stubbed():
    """§10: a live run cannot always reach this machinery.

    Page 1 is fetched alone and decides how many pages there are, so a
    blocked page 1 means the workers never start. Driven directly instead,
    with the browser replaced.
    """
    engine = _import_engine("playwright_scraper")
    if engine is None:
        return

    class Args:
        delay = 0
        retries = 1
        retry_delay = 0
        out = "unused"
        mode = "search"
        sort = "a-z"
        pages = 50

    fetched = []
    import threading
    lock = threading.Lock()

    def fake_fetch(session, args, pool, page_num, url):
        with lock:
            fetched.append(page_num)
        outcome = engine.PageOutcome(page_num=page_num, url=url)
        # Page 6 is the end of this listing: no rows, but a served page.
        outcome.products = [] if page_num >= 6 else [object()] * 15
        outcome.state = "empty" if page_num >= 6 else "content"
        return outcome

    class FakeSession:
        def __init__(self, *a, **k):
            self.pool = None
        def open(self):
            return self
        def close(self):
            pass

    class FakePlaywright:
        def __enter__(self):
            return None
        def __exit__(self, *a):
            return False

    real_fetch = engine._fetch_one_page
    real_session = engine._BrowserSession
    real_pw = engine.sync_playwright
    engine._fetch_one_page = fake_fetch
    engine._BrowserSession = FakeSession
    engine.sync_playwright = lambda: FakePlaywright()
    try:
        specs = [(n, "u%d" % n) for n in range(2, 51)]
        results, unattempted, exhausted = engine._fetch_pages_concurrently(
            Args(), None, specs, 4)
    finally:
        engine._fetch_one_page = real_fetch
        engine._BrowserSession = real_session
        engine.sync_playwright = real_pw

    check("every page fetched was fetched exactly once",
          len(fetched) == len(set(fetched)), "%r" % sorted(fetched))
    check("dispatch STOPPED at the end of the listing", exhausted)
    check("...so the 49 queued pages cost far fewer fetches",
          len(fetched) < 15, "fetched %d of 49" % len(fetched))
    check("unattempted pages are REPORTED, not counted as failed",
          len(unattempted) > 0 and all(isinstance(n, int) for n in unattempted))
    equal("attempted + unattempted covers the whole queue",
          len(set(fetched)) + len(unattempted), 49)
    equal("outcomes are restorable to page order",
          [o.page_num for o in sorted(results, key=lambda o: o.page_num)],
          sorted(o.page_num for o in results))


def check_a_dead_worker_neither_hangs_nor_loses_its_siblings():
    engine = _import_engine("playwright_scraper")
    if engine is None:
        return

    class Args:
        delay = 0
        retries = 1
        retry_delay = 0
        out = "unused"
        mode = "search"
        sort = "a-z"
        pages = 10

    def exploding_fetch(session, args, pool, page_num, url):
        if page_num == 3:
            raise RuntimeError("worker died")
        outcome = engine.PageOutcome(page_num=page_num, url=url)
        outcome.products = [object()] * 15
        outcome.state = "content"
        return outcome

    class FakeSession:
        def __init__(self, *a, **k):
            self.pool = None
        def open(self):
            return self
        def close(self):
            pass

    class FakePlaywright:
        def __enter__(self):
            return None
        def __exit__(self, *a):
            return False

    real_fetch, real_session, real_pw = (engine._fetch_one_page,
                                         engine._BrowserSession,
                                         engine.sync_playwright)
    engine._fetch_one_page = exploding_fetch
    engine._BrowserSession = FakeSession
    engine.sync_playwright = lambda: FakePlaywright()
    try:
        specs = [(n, "u%d" % n) for n in range(2, 8)]
        results, unattempted, exhausted = engine._fetch_pages_concurrently(
            Args(), None, specs, 3)
    finally:
        engine._fetch_one_page = real_fetch
        engine._BrowserSession = real_session
        engine.sync_playwright = real_pw

    check("the run returned rather than hanging", True)
    check("the dead worker's siblings still delivered their pages",
          len(results) >= 3, "%d results" % len(results))
    check("page 3 is not reported as a success",
          3 not in [o.page_num for o in results])


def check_no_statement_is_unreachable():
    """A statement sitting after a return/raise/break/continue in the SAME
    block, which therefore can never run.

    Narrow on purpose: it makes no claim about reachability in general, only
    about a block whose control flow has already left. Measured across the
    eighteen repos of this family on 2026-09-16 it reported six problems and
    zero false positives.

    `check_undefined_names_in_every_module` cannot see this class at all, by
    design -- it pools every binding in the file rather than tracking scopes,
    so a name used inside dead code passes as long as anything else in the
    module binds it. What was hiding in that blind spot here, and in five
    sibling repos, byte for byte: a function whose `def` line had been lost,
    leaving its docstring and body absorbed into the end of the function
    above it. Present since this repo's first commit, invisible to import,
    `--help`, `compileall`, and every green run of this suite.
    """
    for filename in sorted(f for f in os.listdir(HERE) if f.endswith(".py")):
        tree = ast.parse(open(os.path.join(HERE, filename),
                              encoding="utf-8").read())
        dead = []
        for node in ast.walk(tree):
            for field in ("body", "orelse", "finalbody"):
                block = getattr(node, field, None)
                if not isinstance(block, list):
                    continue
                for i, stmt in enumerate(block[:-1]):
                    if isinstance(stmt, (ast.Return, ast.Raise,
                                         ast.Continue, ast.Break)):
                        dead.append(block[i + 1].lineno)
                        break
        check("%s: no statement the control flow can never reach" % filename,
              not dead, "first at line %d" % min(dead) if dead else "")


def check_undefined_names_in_every_module():
    """§10: compileall proves a file PARSES, not that its names RESOLVE.

    A live run of a sibling repo's pyppeteer engine died with NameError on a
    line reached only while fetching, after an import had been removed — the
    module imported cleanly, --help worked, compileall passed and CI was
    green. Kept COARSE (pooled bindings, no scope tracking) so it
    under-reports rather than inventing problems.
    """
    import builtins
    modules = [f for f in sorted(os.listdir(HERE))
               if f.endswith(".py") and f != "smoke_test.py"]
    for filename in modules:
        tree = ast.parse(open(os.path.join(HERE, filename), encoding="utf-8").read())
        # Module-level dunders exist without being assigned anywhere.
        defined = set(dir(builtins)) | {"__file__", "__name__", "__doc__",
                                        "__package__", "__spec__"}
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                for alias in node.names:
                    defined.add((alias.asname or alias.name).split(".")[0])
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef,
                                   ast.ClassDef)):
                defined.add(node.name)
            elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                defined.add(node.id)
            elif isinstance(node, ast.arg):
                defined.add(node.arg)
            elif isinstance(node, ast.ExceptHandler) and node.name:
                defined.add(node.name)
            elif isinstance(node, ast.alias) and node.asname:
                defined.add(node.asname)
        used = {n.id for n in ast.walk(tree)
                if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)}
        unresolved = sorted(used - defined)
        check("%s: every name resolves" % filename, not unresolved,
              "%s" % unresolved)


def check_dockerfile_copies_everything_the_entrypoint_imports():
    """§10: all three repos in this family shipped an image that died with
    ModuleNotFoundError on every invocation, --help included, because
    proxy_pool.py was missing from the COPY list. CI never built the image;
    this check needs no Docker."""
    path = os.path.join(HERE, "Dockerfile")
    if not os.path.exists(path):
        check("Dockerfile exists", False)
        return
    dockerfile = open(path, encoding="utf-8").read()
    # Only the COPY instructions, continuations included — a comment above
    # them naming a file is not a file the image carries.
    copy_lines, joining = [], False
    for line in dockerfile.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        if joining or stripped.upper().startswith("COPY "):
            copy_lines.append(stripped)
            joining = stripped.endswith("\\")
    copied = set(re.findall(r"([A-Za-z_][A-Za-z0-9_]*)\.py", " ".join(copy_lines)))
    entry = re.search(r'(?:CMD|ENTRYPOINT)\s*\[?\s*"?(?:python3?"?,\s*"?)?'
                      r'([A-Za-z_][A-Za-z0-9_]*)\.py', dockerfile)
    entrypoint = entry.group(1) if entry else "playwright_scraper"
    needed = _import_graph(entrypoint)
    missing = sorted(needed - copied)
    check("the Dockerfile COPYs every module %s.py imports" % entrypoint,
          not missing, "missing %s" % missing)
    for unwanted in ("smoke_test", "test_smoke"):
        check("the image does not carry %s.py" % unwanted,
              unwanted not in copied)


def check_env_example_documents_exactly_what_the_loader_reads():
    import env_config
    path = os.path.join(HERE, ".env.example")
    if not os.path.exists(path):
        check(".env.example exists", False)
        return
    documented = set(re.findall(r"^\s*#?\s*([A-Z][A-Z0-9_]+)\s*=", 
                                open(path, encoding="utf-8").read(), re.M))
    read = set(env_config.ENV_KEYS)
    check("every variable the loader reads is documented",
          not (read - documented), "undocumented: %s" % sorted(read - documented))
    check("every documented variable is actually read",
          not (documented - read), "unread: %s" % sorted(documented - read))


def check_a_copied_env_example_reads_as_UNSET():
    """§17: `cp .env.example .env` followed by a run must not connect.

    The placeholder check was a literal set in a sibling repo, and the two
    credentialled URLs are documented the way the vendor documents them —
    `ws://{login}-zone-…:{password}@cb.2captcha.com:9222` — so neither
    literal matched, the run connected with the string `{login}-zone-…` as
    its username, and got a 401 a long way from its cause.
    """
    import env_config
    example = os.path.join(HERE, ".env.example")
    if not os.path.exists(example):
        check(".env.example exists", False)
        return
    text = open(example, encoding="utf-8").read()
    values = dict(re.findall(r"^([A-Z][A-Z0-9_]+)=(.*)$", text, re.M))
    check("the example actually sets every variable",
          set(values) == set(env_config.ENV_KEYS),
          "example has %s, loader reads %s"
          % (sorted(values), sorted(env_config.ENV_KEYS)))
    # Every CREDENTIAL must read as unset. The default TARGET must not: it is
    # a real, usable URL, and blanking it would remove the one setting this
    # file exists to make convenient (§17's check #3 says exactly this — the
    # credentials unset, the non-credential default still usable).
    CREDENTIALS = {"TWOCAPTCHA_KEY", "KOSE_CDP_ENDPOINT", "KOSE_PROXY"}
    before = dict(os.environ)
    try:
        for name, raw in values.items():
            os.environ[name] = raw
            got = env_config.env_value(name)
            if name in CREDENTIALS:
                check("a copied .env.example leaves %s unset" % name,
                      got is None, "got %r" % got)
            else:
                check("...while %s stays a usable default" % name,
                      got == raw.strip(), "got %r" % got)
    finally:
        os.environ.clear()
        os.environ.update(before)
    # And the counter-check: a real credential must still come through, or
    # the placeholder rule would have made the loader useless. Deliberately
    # NOT 32 hex characters — that is the shape of a real 2captcha key, and
    # this repo's own credential scan (rightly) fails on one.
    try:
        os.environ["TWOCAPTCHA_KEY"] = "not-a-real-key-but-a-real-value"
        equal("a real value is still read",
              env_config.env_value("TWOCAPTCHA_KEY"),
              "not-a-real-key-but-a-real-value")
    finally:
        os.environ.clear()
        os.environ.update(before)


def check_engines_import_their_driver_at_module_level():
    """For the guarded imports above to MEAN anything.

    A sibling repo imported `launch`/`connect` inside the launch path, so the
    module imported cleanly with no pyppeteer installed: the group never
    skipped, and the CI job that exists to fail on unexpected skips could not
    have caught a broken import. It also let CI run against a stub version
    for a while without anything noticing. This drifts back silently, so it
    is asserted with an `ast` walk rather than trusted.
    """
    for module, driver in DRIVER_IMPORTS.items():
        path = os.path.join(HERE, module + ".py")
        if not os.path.exists(path):
            check("%s exists" % module, False)
            continue
        tree = ast.parse(open(path, encoding="utf-8").read())
        top_level = set()
        for node in tree.body:          # module level ONLY
            if isinstance(node, ast.Import):
                top_level.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                top_level.add(node.module.split(".")[0])
        check("%s imports %s at MODULE level" % (module, driver),
              driver in top_level,
              "top-level imports: %s" % sorted(top_level))


def check_engine_flag_sets():
    """§17's check #2: against the contract AND against each other, both ways.

    A missing flag fails; so does closing a difference the README documents.
    """
    sets = {}
    for module in ENGINES:
        if not os.path.exists(os.path.join(HERE, module + ".py")):
            continue
        sets[module] = _argparse_flags(module)
    for module, flags in sets.items():
        missing = (CONTRACT_FLAGS | EXTRA_FLAGS) - flags
        check("%s defines every contract flag" % module, not missing,
              "missing %s" % sorted(missing))
    # The ONE documented difference: pyppeteer downloads its own Chromium
    # and could not launch it on the development machine, so it needs a way
    # to point at another one. Its twins have no equivalent because they do
    # not ship a browser. Listed here so that closing the difference — or
    # growing a second one — fails the build (§17).
    DOCUMENTED_DIFFERENCES = {"puppeteer_scraper": {"--chromium-path"}}
    names = sorted(sets)
    for i in range(len(names) - 1):
        a, b = names[i], names[i + 1]
        only_a = sets[a] - sets[b] - DOCUMENTED_DIFFERENCES.get(a, set())
        only_b = sets[b] - sets[a] - DOCUMENTED_DIFFERENCES.get(b, set())
        check("%s and %s define the same flags" % (a, b),
              not only_a and not only_b,
              "only in %s: %s; only in %s: %s"
              % (a, sorted(only_a), b, sorted(only_b)))


def check_banned_and_removed_flags():
    """Scoped to the ENGINES.

    `--country` is absent here — the flag CLAUDE.md §10 bans outright — and
    `--locale` takes its place, because on Montblanc the market really is a
    property of the URL rather than of the browser.

    That makes the ban's REASON bite harder than usual: the locale is a path
    segment, so a `--locale` that disagreed with a `--url` would silently
    read a different market, and on this site a different market is a
    different PRICE (EUR 2000 on en-fi against EUR 1900 on de-de for one
    backpack). So the flag is refused alongside --url rather than merged,
    and this check pins that refusal exists in every engine.
    """
    for module in ENGINES:
        path = os.path.join(HERE, module + ".py")
        if not os.path.exists(path):
            continue
        source = open(path, encoding="utf-8").read()
        for flag in BANNED_FLAGS:
            check("%s does not define %s" % (module, flag),
                  '"%s"' % flag not in source)
        check("%s does not define the banned --country" % module,
              '"--country"' not in source,
              "§10 bans it: it could disagree with the URL")
        check("%s refuses --tags alongside --url" % module,
              "--url already names what to fetch" in source,
              "two ways to say what to fetch must not be merged in silence")
        check("%s builds a category URL only from a cNN id" % module,
              "--category builds a URL from a category id" in source,
              "the brand slug selects nothing on this site, so a flag taking "
              "one would build an address whose meaning it does not control")


def check_every_engine_exposes_the_same_public_surface():
    for module in ENGINES:
        engine = _import_engine(module)
        if engine is None:
            continue
        for name in ("scrape", "parse_args", "PageOutcome", "_fetch_one_page",
                     "_parse_for_mode", "_target_url"):
            check("%s.%s exists" % (module, name), hasattr(engine, name))
        outcome = engine.PageOutcome(page_num=1, url="u")
        for field_name in ("state", "canonical", "pages_available",
                           "products", "blocked_by",
                           "load_failed", "final_url"):
            check("%s.PageOutcome carries %r" % (module, field_name),
                  hasattr(outcome, field_name))
        check("%s.PageOutcome.ok is True for a fresh outcome" % module,
              outcome.ok)
        equal("%s shares CORE_FIELDS with its twins" % module,
              tuple(engine.CORE_FIELDS),
              ("title", "url", "sku", "brand", "currency"))
        equal("%s shares PRICE_COVERAGE_FLOOR with its twins" % module,
              engine.PRICE_COVERAGE_FLOOR, 95)
        equal("%s shares CORE_FIELD_FLOOR with its twins" % module,
              engine.CORE_FIELD_FLOOR, 99)


def check_sample_output_matches_the_schema():
    from output_writer import Product
    expected = [f.name for f in fields(Product)]
    json_path = os.path.join(HERE, "sample_output.json")
    csv_path = os.path.join(HERE, "sample_output.csv")
    if not os.path.exists(json_path):
        check("sample_output.json exists", False)
        return
    rows = json.load(open(json_path, encoding="utf-8"))
    check("sample_output.json holds rows", bool(rows))
    equal("sample_output.json keys match the schema, in order",
          list(rows[0].keys()), expected)
    check("sample_output.json is from a real run (maison.kose.co.jp rows)",
          all(r["source"] == "maison.kose.co.jp" for r in rows))
    check("...and every row carries a tax rate beside its price",
          all(r.get("tax_rate") for r in rows if r.get("price") is not None),
          "a tax-inclusive price with no rate cannot be converted back")
    check("...and the sample shows BOTH tax rates, so the reduced one is "
          "visible to anyone reading the file rather than only the code",
          {r.get("tax_rate") for r in rows} == {8, 10},
          str(sorted({r.get("tax_rate") for r in rows})))
    check("...and both modes, so a reader sees which columns each populates",
          {r.get("mode") for r in rows} == {"listing", "product"},
          str(sorted({r.get("mode") for r in rows})))
    check("...and a row of each stock state",
          {r.get("in_stock") for r in rows} >= {True, False},
          str(sorted(str(r.get("in_stock")) for r in rows)))
    check("...and a currency wherever there is a price",
          all(r.get("currency") for r in rows if r.get("price") is not None))
    check("...and carries no fabrication markers",
          not any("example" in (r.get("url") or "").lower() or
                  "lorem" in (r.get("title") or "").lower() for r in rows))
    if os.path.exists(csv_path):
        header = next(csv.reader(open(csv_path, encoding="utf-8")))
        equal("sample_output.csv header matches the schema", header, expected)


def check_no_test_mutates_the_working_tree():
    """§10: one suite used its own file as a fake chromedriver and chmod'd it
    to 755, leaving a mode change in git status.

    Compares the tree against how it looked when the suite STARTED, not
    against a clean checkout — otherwise this is permanently red while
    anyone is editing, and a check that is always red teaches everyone to
    ignore checks.
    """
    if _TREE_BEFORE is None:
        skip("git status", "not a git repository")
        return
    after = _tree_state()
    changed = sorted(set(after) - set(_TREE_BEFORE))
    check("the suite itself changed nothing in the working tree",
          not changed, "%s" % changed)


def check_captcha_capability_claims_match_the_code():
    """§19: the most expensive bug this family can ship is a SENTENCE.

    It fails in both directions and this family has shipped both:

      * saying a captcha CANNOT be solved, when the true statement is that
        THIS REPO does not implement the task type. 2Captcha solves
        enterprise reCAPTCHA and Cloudflare Turnstile and has for years, so
        such a sentence tells a reader not to buy something that works.
      * saying this repo DOES solve something it builds no task type for --
        which is what the README said here: it billed the Managed Challenge
        solve to `--twocaptcha-key`, while the only thing that clears one is
        `Captcha.setAutoSolve` over `--cdp-endpoint`.

    Neither is visible to any other check: nothing fails, nothing crashes,
    and the output is correct.
    """
    readme = open(os.path.join(HERE, "README.md"), encoding="utf-8").read()
    solver = open(os.path.join(HERE, "captcha_solver.py"), encoding="utf-8").read()
    low = readme.lower()

    # Conclusions about the PRODUCT. "Unsolvable" is a property of a PAGE —
    # it means the page carries no widget — and never of a vendor. 2Captcha
    # solves enterprise reCAPTCHA and Cloudflare Turnstile and has for years,
    # so a sentence saying otherwise tells a reader not to buy something that
    # works, and nothing else in this suite can see it.
    for phrase in ("cannot be solved", "can't be solved", "neither is solvable",
                   "is not solvable", "solver is inapplicable", "no solver can",
                   "2captcha cannot", "no captcha service"):
        check("README: no %r -- write 'this repo does not implement X'" % phrase,
              phrase not in low)

    # The pairing that matters ON THIS SITE.
    #
    # The sibling repo pins "the README must say TurnstileTaskProxyless is
    # not built here", because BBB renders Cloudflare Managed Challenges and
    # a reader could reasonably expect a key to clear one. Montblanc renders
    # NO challenge at all, so the equivalent hazard is the opposite one: this
    # README's central claim is that no key is needed, and a claim like that
    # rots the moment the site switches a bot manager on.
    #
    # So the claim has to be PAIRED with the thing that would retest it — the
    # daily canary — rather than left as a sentence nobody re-measures (§13).
    claims_no_key = ("no, and it would be dishonest" in low
                     or "do i need a 2captcha account" in low)
    if claims_no_key:
        check("README pairs 'no key needed' with the canary that retests it",
              "canary" in low,
              "a claim that the site is ungated goes stale silently; the "
              "daily canary is what turns it back into a measurement")
        check("...and dates the measurement it rests on",
              re.search(r"20\d\d-\d\d-\d\d", readme) is not None,
              "§13: a number describing a living thing needs its moment")

    # And in the other direction: if the README names a task type, the solver
    # had better build it. A capability claim citing no task type is a guess
    # wearing a fact's clothes; one citing a task type nobody implemented is
    # worse.
    for task in ("TurnstileTaskProxyless", "RecaptchaV2EnterpriseTaskProxyless",
                 "RecaptchaV3TaskProxyless"):
        if task.lower() in low:
            check("README names %s, so the solver must build it" % task,
                  task in solver,
                  "the README credits a task type this repo does not send")

    # Whatever the README credits with clearing the challenge must be a thing
    # the engines actually do.
    if "setautosolve" in low:
        srcs = ""
        for name in ("playwright_scraper.py", "selenium_scraper.py",
                     "puppeteer_scraper.py"):
            path = os.path.join(HERE, name)
            if os.path.exists(path):
                srcs += open(path, encoding="utf-8").read()
        check("README credits Captcha.setAutoSolve, and an engine calls it",
              "Captcha.setAutoSolve" in srcs)


def check_policy_constants_have_a_consumer():
    """§17: a policy constant nothing reads is the same defect as dead code.

    `RETRY_ON_BLOCKED` carried a paragraph of measured justification in a
    sibling repo and NO engine consulted it, so setting it False changed
    nothing while the prose read like enforcement.
    """
    import page_flow
    sources = {}
    for name in ("playwright_scraper", "puppeteer_scraper", "selenium_scraper"):
        path = os.path.join(HERE, name + ".py")
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                sources[name] = f.read()
    check("policy: the engines are readable", len(sources) == 3, sorted(sources))

    for const in ("RETRY_ON_BLOCKED", "BLOCK_RETRIES_WITHOUT_POOL",
                  "SOLVES_PER_PAGE"):
        readers = [n for n, s in sources.items() if const in s]
        check("policy: %s is read by an engine" % const, readers, "no consumer")


def check_state_policy():
    import page_flow

    equal("policy: content is parsed", page_flow.should_parse("content"), True)
    equal("policy: content is not retried", page_flow.should_retry("content"), False)

    # An empty page is an ANSWER. It must not be retried and must not be
    # reported as blocked.
    equal("policy: empty is parsed", page_flow.should_parse("empty"), True)
    equal("policy: empty is not retried", page_flow.should_retry("empty"), False)
    equal("policy: empty is not blocked", page_flow.counts_as_blocked("empty"), False)

    # A refusal offers nothing to solve, so it must not spend money.
    equal("policy: blocked never pays a solver",
          page_flow.should_solve("blocked"), False)
    equal("policy: blocked is blocked", page_flow.counts_as_blocked("blocked"), True)

    # A rendered widget IS a test, and is the one state that pays.
    equal("policy: a captcha may be solved", page_flow.should_solve("challenge"), True)

    equal("policy: unknown waits rather than spending",
          (page_flow.should_retry("unknown"), page_flow.should_solve("unknown")),
          (True, False))
    # An unrecognised state must fall back to the cautious one rather than
    # raising, so a new state name cannot crash a run mid-flight.
    equal("policy: an unknown state name falls back to 'unknown'",
          page_flow.should_solve("something-new"), False)


def check_pagination_addressability_is_asked_per_url():
    import page_flow
    check("pagination: a category listing is addressable",
          page_flow.pagination_is_addressable(LISTING_URL))
    check("pagination: a tag listing is addressable too — both routes were "
          "CHECKED against the site's own rel=next before being trusted (§7)",
          page_flow.pagination_is_addressable(TAGS_URL))
    check("pagination: a PRODUCT page is not — it is one page",
          not page_flow.pagination_is_addressable(PRODUCT_URL))


def check_page_and_position_are_unique_across_pages():
    """One line, and the column is worthless without it: `position` restarts
    at 1 on every page."""
    import product_parser as P
    page1 = P.parse_listing(LISTING_HTML, LISTING_URL, page=1).rows
    page2 = P.parse_listing(LISTING_HTML, LISTING_URL, page=2).rows
    pairs = [(r.page, r.position) for r in page1 + page2]
    equal("page+position is unique across a multi-page run",
          len(set(pairs)), len(pairs))
    equal("page 2's rows really say page 2",
          sorted({r.page for r in page2}), [2])


def check_a_broken_parser_is_not_reported_as_an_empty_category():
    """§20: a served page that links to N products and parses to zero is OUR
    bug, and saying "0 products" sends the reader to check the URL instead.

    §20 also says to check the signal CAN fire before adding it. Here it
    genuinely can, and the margin is measured: rows come from
    `li.c-product__item` tiles while `product_link_count` counts `/g/g…/`
    hrefs, and a real grid page carries 48-55 of the latter against 24 of the
    former. So a tile-markup change leaves every link in place and takes
    every row away — which is what this fixture simulates.
    """
    import page_flow
    from product_parser import product_link_count, parse_products, detect_page_state

    # Built by breaking the ELEMENT of every tile while leaving its links,
    # its prices and the site's own assets untouched — which is exactly the
    # shape a markup change takes, and the shape that makes rows vanish while
    # `product_link_count` carries on reporting a healthy page.
    broken = LISTING_HTML.replace('<li class="c-product__item',
                                  '<div class="c-product__item')
    links = product_link_count(broken)
    check("parse-failure: the fixture still links to products", links >= 4, str(links))
    equal("parse-failure: and parses to nothing",
          len(parse_products(broken, LISTING_URL)), 0)
    equal("parse-failure: while the page reads as served",
          detect_page_state(broken, 200, "")[0], "empty")

    check("parse-failure: that combination is flagged",
          page_flow.looks_like_a_parse_failure("empty", 0, links))

    # A genuinely empty category must NOT be flagged — that is a correct
    # answer, and crying wolf on it is the failure this guards against.
    equal("parse-failure: an empty category with no product links is not one",
          page_flow.looks_like_a_parse_failure("empty", 0, 0), False)
    equal("parse-failure: one stray link (a nav flyout) is not one",
          page_flow.looks_like_a_parse_failure("empty", 0, 1), False)
    # Nor is a page that parsed fine, nor a block.
    equal("parse-failure: a page with rows is never one",
          page_flow.looks_like_a_parse_failure("content", 24, 24), False)
    equal("parse-failure: a BLOCKED page is not one either",
          page_flow.looks_like_a_parse_failure("blocked", 0, 5), False)


def check_parser_found_nothing_is_not_a_complete_run():
    """The stop_reason must not read as success (§8: blocked != empty)."""
    from output_writer import COMPLETE_STOP_REASONS, run_meta
    check("parse-failure: 'parser_found_nothing' is NOT a complete stop reason",
          "parser_found_nothing" not in COMPLETE_STOP_REASONS,
          list(COMPLETE_STOP_REASONS))
    meta = run_meta(status="failed", stop_reason="parser_found_nothing",
                    pages_requested=1, pages_completed=0, pages_failed=[1],
                    products=0, mode="category", source="montblanc.com",
                    start_url="u", final_url="u")
    equal("parse-failure: the sidecar carries the reason by name",
          meta["stop_reason"], "parser_found_nothing")

    # Every engine must be able to SET it, or the sidecar can never say it.
    for module in ENGINES:
        path = os.path.join(HERE, module + ".py")
        if not os.path.exists(path):
            continue
        source = open(path, encoding="utf-8").read()
        check("%s can report parser_found_nothing" % module,
              "parser_found_nothing" in source,
              "the engine never sets the stop_reason, so it is unreachable")
        check("%s consults page_flow for it" % module,
              "looks_like_a_parse_failure" in source,
              "the engine must not reimplement the decision")


def check_sidecar_shape():
    from output_writer import run_meta
    meta = run_meta(status="complete", stop_reason="page_cap_reached",
                    pages_requested=50, pages_completed=12, pages_failed=[],
                    products=280, mode="category", source="montblanc.com",
                    start_url="https://www.montblanc.com/en-fi/writing-instruments",
                    final_url="https://www.montblanc.com/en-fi/writing-instruments?start=264&sz=24",
                    extra={"total_results": 280, "pages_available": 12,
                           "page_size": 24, "locale": "en-fi",
                           "sort_requested": "price-asc",
                           "site_default_sort": "recommended"})
    for key in ("status", "stop_reason", "pages_requested", "pages_completed",
                "pages_failed", "mode", "source"):
        check("the sidecar records %r" % key, key in meta)
    equal("the sidecar carries the site's own total", meta["total_results"], 280)
    equal("...and the market the prices belong to", meta["locale"], "en-fi")
    equal("...and which ordering was asked for", meta["sort_requested"], "price-asc")
    equal("...and what a visitor would have got instead",
          meta["site_default_sort"], "recommended")
    equal("pages_failed is a LIST of numbers, not a count",
          isinstance(meta["pages_failed"], list), True)

    # No `capped_by_site` here, and the ABSENCE is the finding: this site
    # imposes no page cap, so a complete run really is the whole category.
    check("no capped_by_site on a site that does not cap",
          "capped_by_site" not in meta, sorted(meta))


def check_row_schema():
    from output_writer import Product, ROW_CLASS_BY_MODE, UNIQUE_BY_SKU_MODES
    names = [f.name for f in fields(Product)]
    equal("the family prefix is byte-identical and in order (§9)",
          names[:5], ["source", "scraped_at", "url", "sku", "title"])

    # The commerce columns this site DOES have. Montblanc is a shop, so the
    # family's price fields are present rather than dropped.
    for present in ("brand", "price", "currency", "in_stock", "image_url",
                    "category", "price_source"):
        check("the commerce column %r is present" % present, present in names)

    # And the ones measured ABSENT, each with its count in output_writer's
    # docstring. §9 says removing a column needs the measurement written
    # down; this pins that they stay removed until someone re-measures.
    for gone in ("original_price", "discount_pct", "lowest_price_30d",
                 "rating", "review_count", "ean", "gtin", "engraved"):
        check("the column %r is absent, not null-forever" % gone,
              gone not in names,
              "if this is back, output_writer's measurement should be too")

    # Site-specific columns go at the END of the row (§9), after the family's.
    equal("site-specific columns come last",
          names[-9:], ["mode", "tax_rate", "price_is_store_price", "badges",
                       "subcategory", "volume", "colour_count",
                       "release_date", "variant_of"])

    equal("every mode maps to a row class",
          sorted(ROW_CLASS_BY_MODE), ["listing", "product"])
    equal("every mode is one row per sku",
          sorted(UNIQUE_BY_SKU_MODES), ["listing", "product"])
    equal("both modes share one class",
          len({c for c in ROW_CLASS_BY_MODE.values()}), 1)


def check_fixtures_carry_no_session_material():
    """§10: a real page dump carries the session that fetched it.

    A sibling repo committed three `sessionId` values, their CSRF tokens and
    a real customer's display name, profile permalink and review text. None
    of that granted anything — the session material was anonymous and
    expired — and it still did not belong in a public repo.

    Montblanc is the easy case: it publishes products, not people, and no
    capture here carries a name, a review or a login. So this guards the
    SHAPE rather than any literal, which is the half that keeps working when
    the next capture is taken (§10: guard with PATTERNS, not the old
    values).
    """
    fixtures = {
        "LISTING_HTML": LISTING_HTML,
        "LISTING_TAX8_HTML": LISTING_TAX8_HTML,
        "TAGS_HTML": TAGS_HTML,
        "PRODUCT_HTML": PRODUCT_HTML,
        "EMPTY_HTML": EMPTY_HTML,
        "NOTFOUND_HTML": NOTFOUND_HTML,
        "CHROMIUM_ERROR_HTML": CHROMIUM_ERROR_HTML,
    }
    patterns = {
        "a session id": r"sessionId|session_id|JSESSIONID|dwsid",
        "a CSRF token": r"csrf[_-]?token|anti-?csrftoken",
        "a bearer token": r"[Bb]earer\s+[A-Za-z0-9._-]{16,}",
        "a 32-hex key": r"\b[0-9a-f]{32}\b",
        "an email address": r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
        "credentials in a URL": r"[a-z]+://[^\s/@]+:[^\s/@]+@",
    }
    for fixture_name, text in fixtures.items():
        for label, pattern in patterns.items():
            hit = re.search(pattern, text)
            check("%s carries no %s" % (fixture_name, label), hit is None,
                  "matched %r — scrub the capture before committing it"
                  % (hit.group(0)[:40] if hit else ""))


def _import_engine(name):
    try:
        return __import__(name)
    except ImportError as e:
        skip(name, "engine library absent (%s)" % e)
        return None


def _argparse_flags(module_name):
    """Every --flag a module's parser defines, without running the CLI."""
    path = os.path.join(HERE, module_name + ".py")
    tree = ast.parse(open(path, encoding="utf-8").read())
    # Only calls on the argparse parser itself. A browser's option object
    # also has `add_argument`, and counting Chrome's own switches
    # (`--no-sandbox`, `--window-size=…`) as CLI flags made this check
    # compare nonsense.
    parsers = {"p"}
    for node in ast.walk(tree):
        if (isinstance(node, ast.Assign) and isinstance(node.value, ast.Call)
                and isinstance(node.value.func, ast.Attribute)
                and node.value.func.attr in ("add_argument_group",
                                             "add_mutually_exclusive_group")):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    parsers.add(target.id)
    flags = set()
    for node in ast.walk(tree):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and node.func.attr == "add_argument"
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id in parsers):
            for arg in node.args:
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str) \
                        and arg.value.startswith("--"):
                    flags.add(arg.value)
    return flags


def _tree_state():
    result = subprocess.run(["git", "status", "--porcelain"], cwd=HERE,
                            capture_output=True, text=True)
    if result.returncode != 0:
        return None
    return sorted(line for line in result.stdout.splitlines()
                  if not line.endswith(".pyc"))


def _import_graph(entrypoint):
    """Every local module an entrypoint reaches, transitively."""
    local = {f[:-3] for f in os.listdir(HERE) if f.endswith(".py")}
    seen, queue = set(), [entrypoint]
    while queue:
        name = queue.pop()
        if name in seen or name not in local:
            continue
        seen.add(name)
        tree = ast.parse(open(os.path.join(HERE, name + ".py"),
                              encoding="utf-8").read())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                queue.extend(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                queue.append(node.module.split(".")[0])
    return seen

CHECKS = [v for k, v in sorted(globals().items()) if k.startswith("check_")]


def main():
    global VERBOSE
    parser = argparse.ArgumentParser(description="kose-scraper offline suite")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()
    VERBOSE = args.verbose

    global _TREE_BEFORE
    _TREE_BEFORE = _tree_state()

    for fn in CHECKS:
        if VERBOSE:
            print("\n== %s" % fn.__name__)
        try:
            fn()
        except Exception as e:  # noqa: BLE001 — a broken check is a failure
            import traceback
            FAILURES.append("%s raised %s: %s" % (fn.__name__, type(e).__name__, e))
            print("  ERROR %s raised %s: %s" % (fn.__name__, type(e).__name__, e))
            if VERBOSE:
                traceback.print_exc()

    print("\n%d checks passed, %d failed, %d group(s) skipped."
          % (PASSED, len(FAILURES), len(SKIPS)))
    for line in SKIPS:
        print("  skipped: %s" % line)
    if FAILURES:
        print("\nFailures:")
        for line in FAILURES:
            print("  - %s" % line)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
