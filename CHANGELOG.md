# Changelog

All notable changes to this project are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project follows [Semantic Versioning](https://semver.org/) as closely
as a CLI toolkit can. A **patch** release means fixes; it does not promise
that every flag and default is frozen. Where a patch changes behaviour an
existing user would notice, the release notes lead with it.

## [0.1.0] — 2026-09-18

First release. Reads **Maison KOSÉ** (`maison.kose.co.jp`), Kosé's own online
store.

> **The domain in this repo's name does not resolve.** `kose.com` is
> registered (GoDaddy, 1998, paid to 2029) and delegated to two nameservers
> that answer REFUSED for the zone, so every resolver returns SERVFAIL and no
> client anywhere gets an address. It is a broken delegation, not a bot
> manager. Kosé's storefront is `maison.kose.co.jp`, which is where
> `www.kose.co.jp` sends a visitor with its own meta refresh, and that is
> what this scraper reads.

### Added

- Two modes over three routes: `--mode listing` reads a category
  (`/site/{brand}/c/cNN/`) or a tag facet
  (`/site/itemtags/list.aspx?tags=…`), and `--mode product` reads one product
  page out of its own JSON-LD.
- Four engines: Playwright (primary), Selenium, pyppeteer, and the 2Captcha
  Scraper API. All four were run live on 2026-09-18; the three browser
  engines returned **48 of 48 identical rows** on the same two pages.
- 23 columns, including four this site needs that the family schema did not
  have: `tax_rate` (Japan charges 8% and 10% and the prices are
  tax-inclusive), `price_is_store_price`, `badges`, and `variant_of`.
- A canary that runs a real 3-page scrape **daily from a bare GitHub runner
  with no secrets**, because the README's central claim is that none are
  needed. A second job reads a product page; a third exercises the Scraping
  Browser API and skips with a `::notice::` when no secret is set.

### Measured, on 2026-09-18 from a datacentre address

- **No gating of any kind.** `curl`, `python-requests` and a request with **no
  `User-Agent` header at all** each returned the same 90,310-byte listing;
  twelve pages back to back were twelve HTTP 200s.
- **No captcha.** Zero markers of reCAPTCHA, hCaptcha, Turnstile, DataDome,
  PerimeterX, Incapsula, Kasada or AWS WAF across 13 captures, and no
  `data-sitekey` anywhere. The solver is wired and has never had anything to
  do. Nothing here claims a captcha on this site could not be solved.
- **216 rows across four live runs**, with `title`, `url`, `sku`, `brand`,
  `price`, `currency`, `in_stock`, `image_url` and `tax_rate` populated on
  216 of 216. Prices ran ¥495 to ¥264,000.
- One category, `/c/c15/`, states 13 pages and holds 12 × 24 + 16 = **304
  products**.

### Site traps this release handles

- **The brand segment in every URL is decorative.** `/site/xyz/c/c15/`
  returns byte-identical bytes to `/site/cosmedecorte/c/c15/`. Only `cNN` and
  `gSKU` address anything, so `brand` is read per tile — a tag listing mixed
  **11 brands across 72 rows**.
- **A category listing walked past its end serves its last page AGAIN**,
  byte-identical and HTTP 200, rather than 404ing or emptying. Runs plan
  against the site's own `N／Mページ` counter and still stop on "no new sku".
  A tag listing ends with a genuinely empty page and publishes no counter.
- **`&pageno=` and `&page=` are silently ignored** on a tag listing and
  return page 1 with HTTP 200; only `?p=` paginates it.
- **5 of 20 product pages canonicalise to a DIFFERENT sku** — `/g/gJQBA/` is
  the 60 g cream and points at the 20 g `/g/gJQGA/`. A row's URL is built
  from the page's own sku; the canonical is kept as `variant_of`.
- **A product page reuses the listing's tile class** on `<div>`s for
  staff-review cards, 15 on one measured page. The tile selector is
  element-qualified and sees zero of them.

### Known limitations

- `--cdp-endpoint` (the Scraping Browser API) is **not live-verified in this
  repo**: the profile available when this was built had expired (`401
  deny_no_user`), and those credentials live about a day. The code path is
  the family's and is exercised by sibling repos.
- Selenium cannot use an authenticated remote CDP endpoint or an
  authenticated proxy; both limits are the driver's and are documented in the
  README rather than left to be discovered.
- The site's own `/site/goods/search.aspx?keyword=…` route returns a page
  with no tiles on it, so there is no keyword-search mode. The tag facets are
  the route that crosses brands.

[0.1.0]: https://github.com/2scraper/kose-scraper/releases/tag/v0.1.0
