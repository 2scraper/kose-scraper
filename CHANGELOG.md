# Changelog

All notable changes to this project are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project follows [Semantic Versioning](https://semver.org/) as closely
as a CLI toolkit can. A **patch** release means fixes; it does not promise
that every flag and default is frozen. Where a patch changes behaviour an
existing user would notice, the release notes lead with it.

## [Unreleased]

### Fixed

Leftovers from the sibling repos this one was bootstrapped from
(montblanc-scraper, bbb-scraper, etsy-scraper), which described those sites
as if they were this one.

- **User-visible strings.** `--pages` help named a `--mode category` and
  `--mode search` this repo does not have and said a category past its end is
  "a served, empty grid" (here it re-serves its last page). The Playwright
  blocked-page error said this site's edge "refuses `curl`, `python-requests`
  and friends outright", the opposite of what the README measured; it now
  matches the other two engines. The parse-failure error pointed at a JSON-LD
  `ItemList` a listing here does not carry; the image-coverage log line
  described that same `ItemList`; `--mode product` logs and `--help` spoke of
  variants and a `ProductGroup`; `--retries` help spoke of hub pages;
  `--dump-html` help pointed at a `TROUBLESHOOTING.md` that does not exist.
- **Engines agree on the refusal reason.** pyppeteer and Selenium recorded a
  refusal as `blocked_cloudflare (hard block)`, a vendor never observed here,
  while Playwright recorded `blocked_edge refusal`. All three now say
  `edge refusal`.
- **`diff_runs.py` tracked Montblanc's columns** (`collection`,
  `sub_collection`, `color`, `size`, `special_edition`, `base_sku`), none of
  which exist in this row model. It now tracks this site's own `tax_rate` and
  `subcategory`, and treats `subcategory` / `variant_of` as product-mode-only.
- **Issue templates** were Etsy's (DataDome, `shop_rating`, an etsy.com
  example URL). Rewritten from this repo's README.
- **Donor prose in core modules and comments:** the BBB Turnstile paragraphs
  in `captcha_solver.py`, Montblanc URLs and counts in the engines, BBB's
  `find_country` in two locale comments, and an unnamed tokopedia hub
  anecdote now credited to tokopedia-scraper.
- **Test data:** `smoke_test.py` built its sidecar fixtures from a
  montblanc.com run; they now use this site's measured `/c/c15/` run (13
  pages, 304 products, `mode="listing"`) and assert the sidecar fields this
  engine actually writes.
- **`.dockerignore`** listed `bbb_businesses.*`; it now lists this repo's
  `kose_products.*`. The Dockerfile example wrote to `writing-instruments`.

- `SECURITY.md` said this project has no releases or version tags; it has
  both. "Supported versions" now names the latest release and `main`.
- `captcha_solver.py`'s docstring pointed at a "No DataDome solver" section
  that does not exist in this repo (it came with the copied core). Removed.

## [0.1.1] — 2026-09-18

A pass back over CLAUDE.md before calling the repo finished. Everything here
was found by checking a claim rather than by reading the code.

### Fixed

- **An HTTP 404 was retried instead of being believed.** The engines
  discarded what `goto()` returned, so every page reached the classifier with
  `status=None` — and this site answers a missing path with a bare
  1,040-byte page carrying *no site chrome at all*, which without a status
  reads as "not recognisably this site" and RETRIES. Playwright and pyppeteer
  now thread the real status; Selenium cannot (WebDriver exposes none), so
  the parser reads the status the site states in its own `<title>404- …`,
  which is what makes all three engines agree rather than two of them being
  better informed than the third.

  A new terminal `not_found` state does not retry, does not count as blocked
  — exit 3 would send the reader after a proxy problem — and stops the run
  with its own `stop_reason`. Verified end to end: the bare tag-facet URL
  (`/site/itemtags/list.aspx` with no `tags=`) is an address this scraper
  ACCEPTS and really does answer 404, so the branch is reachable rather than
  decorative.

- **A run pointed at page 10 quietly returned page 1.** `_target_url`
  normalised a listing URL back to page 1, so `--url .../c15_p10/ --pages 2`
  fetched pages 1 and 2 and reported success. The start page is now honoured:
  that run reads 10 and 11.

- **The credential scan failed on a clean clone.** It skipped virtualenvs by
  DIRECTORY NAME, so following this repo's own README with the environment
  called anything but `.venv` walked into it and failed on the 32-hex string
  inside pip's vendored `packaging/_elffile.py`. A venv is now recognised by
  a `pyvenv.cfg` above the file or `site-packages` in its path. Measured
  across the family: 21 of 26 sibling repos still have the name-based
  version.

- **Two planning implementations became one.** `page_flow.pages_to_plan` now
  returns the absolute page numbers a run should fetch and is the only place
  that arithmetic lives; `plan_from_total` (a wrapper nothing called) and
  `product_parser.pages_to_fetch` (used only by its own test) are gone. Found
  by grepping every public name for a consumer outside its own module.

- **A fabricated fixture was replaced with a real capture.** `NOTFOUND_HTML`
  had been written by hand with a `404-` title on it, and was wrong about the
  one thing it existed to show: this site answers a bogus goods code with
  HTTP **200** and its full chrome. Every fixture in the suite is now cut
  from a real response.

### Verified

- `--concurrency 3` over five pages: 120 rows, 120 distinct skus, merged in
  PAGE order although the pages arrived 4-3-2-5, and `page`+`position` unique
  across the run. Refused over `--cdp-endpoint`, with the reason.
- The published repo description, topics, homepage and release notes carry
  none of the banned wording — the surfaces a file scan cannot see.
- 459 offline checks, and every new check was CONTROLLED: the fix reverted,
  the expected failures confirmed by name, the fix restored. One control
  caught a check of mine that was passing for the wrong reason.

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

[0.1.1]: https://github.com/2scraper/kose-scraper/releases/tag/v0.1.1
[0.1.0]: https://github.com/2scraper/kose-scraper/releases/tag/v0.1.0
