"""
page_flow.py
------------
The retry / solve / blocked decision, as DATA rather than as three copies of
an if-chain (CLAUDE.md §1).

Maison KOSÉ answers a request four ways, and three of them want a different
response:

    a listing or product page with its content on it   -> parse
    a page it served with no products on it            -> parse, it is an answer
    a refusal or a challenge                           -> rotate, or solve
    something that is not a Maison KOSÉ page at all    -> wait, then retry

Three copies of that triage across three engines would drift, and the drift
would be silent — one engine reporting exit 3 where its twin reports exit 0
on the same response.

The honest headline: nothing here has ever fired
-------------------------------------------------
Measured 2026-09-18 from a datacentre address (netcup, Nuremberg), against
maison.kose.co.jp:

    python-requests/2.31.0   HTTP 200, 90,310 bytes
    curl/8.5.0               HTTP 200, 90,310 bytes  (identical)
    a Chrome UA              HTTP 200, 90,310 bytes  (identical)
    no User-Agent header     HTTP 200, 90,310 bytes  (identical)

    12 consecutive page fetches, no delay between them -> 12 × HTTP 200

    zero captcha markers of any vendor across 13 captures (§18's count, in
    product_parser.BOT_CHALLENGE_MARKERS)

So on this site the block path is a TRIPWIRE, not a description of anything
observed. It is carried in full anyway, because the alternative to a tripwire
is a run that reports an empty catalogue on the day Kosé turns something on —
and because CLAUDE.md §19's most expensive bug in this family was a SENTENCE
claiming a captcha could not be met.

Nothing here claims a captcha is unsolvable on this site. There is no widget
to solve today; if one appears, `captcha_solver.py` is wired and the run pays
for it under the usual `--solve-captcha when-blocked` rule.

Two site shapes this module exists to get right
------------------------------------------------
**A category listing walked past its end returns its LAST PAGE AGAIN.**
`/c/c15_p13/` is the last page; `/c/c15_p14/` and `/c/c15_p15/` each return
the same 71,199 bytes, HTTP 200, with 16 real tiles on them. So "keep
fetching until a page comes back empty" never terminates on this route, and
`pages_to_plan` bounds a run by the site's own `N／Mページ` counter rather
than by walking off the end. A tag listing DOES end with an empty page, so
both routes still need the data-based stop (§7 layer 3).

**No JavaScript crosses this boundary.** `wait_for_count` takes a callback
each engine implements with its own `querySelectorAll`, never a string for
the browser to evaluate: a site whose CSP omits `unsafe-eval` kills
`wait_for_function` with an `EvalError` and takes the run down with exit 1
(CLAUDE.md §18). maison.kose.co.jp's CSP does allow `unsafe-eval` — it is in
the header, checked — so this costs nothing here and keeps the habit.
"""

import re
import time
from typing import Callable, Optional

import product_parser


# How many tiles mean "the grid has painted". Must be > 1: waiting for one
# match can resolve on something unrelated long before a grid is there (§5).
#
# Two rather than four, and the number is measured rather than inherited. The
# anchor below is a real product TILE, not a link, so it cannot resolve on a
# nav item — and listing pages here are legitimately short: 16 tiles on the
# last page of a category, 11 on a single-page brand, 6 on the last page of a
# tag facet. A minimum of 4 would have spent the full readiness budget on a
# perfectly good three-product category before parsing it correctly anyway.
MIN_CARD_MATCHES = 2

# A listing page's readiness anchor.
#
# Element-qualified on purpose. The bare class `.c-product__item` is reused
# on a PRODUCT page as a `<div>` for staff-review cards — 15 of them on one
# measured page — so a class-only anchor would report a listing as ready on a
# product page. Measured across 14 captures: `li.c-product__item` counts
# 11-24 on every listing and **0 on every product page**, which is the clean
# separation Montblanc's `.product-tile` did not have.
READY_SELECTOR_LISTING = "li.c-product__item"

# A product page's readiness anchor: 1 on every product capture, 0 on every
# listing. `.c-product-content__list` was the obvious alternative and was
# rejected by the same measurement — it is 1 on listings AND 1 on two of four
# product pages, because the detail page carries an `awoo` recommendation
# list built out of the same container.
READY_SELECTOR_PRODUCT = ".p-product-detail__item__price"

# This site server-renders both page kinds: the grid is in the first
# response's bytes, so readiness is a formality rather than a wait. The
# budget is generous anyway because it costs nothing when it is not needed —
# it is a ceiling, not a delay.
CONTENT_TIMEOUT_MS = 30_000
CONTENT_TIMEOUT_MS_PRODUCT = 20_000


def ready_selector(mode: str) -> str:
    return READY_SELECTOR_PRODUCT if mode == "product" else READY_SELECTOR_LISTING


def min_matches(mode: str) -> int:
    return 1 if mode == "product" else MIN_CARD_MATCHES


def content_timeout_ms(mode: str) -> int:
    return CONTENT_TIMEOUT_MS_PRODUCT if mode == "product" else CONTENT_TIMEOUT_MS


READY_POLL_MS = 500


def wait_for_count(count: Callable[[str], int], selector: str, minimum: int,
                   timeout_ms: int, sleep_ms: Callable[[int], None]) -> int:
    """Poll `count(selector)` until it reaches `minimum` or the budget runs out.

    Returns the last count seen, so a caller can report "13 of 24 painted"
    rather than a bare timeout. The OPERATION is named and the driver's own
    primitive is passed in, so no JavaScript dialect crosses this boundary
    (CLAUDE.md §1): Selenium's `execute_script` wants a function body with an
    explicit `return` while Playwright and pyppeteer want `() => expr`, and a
    shared module that spelled either would quietly acquire one driver's
    accent.
    """
    deadline = time.monotonic() + timeout_ms / 1000.0
    seen = 0
    while True:
        try:
            seen = count(selector)
        except Exception:
            seen = 0
        if seen >= minimum:
            return seen
        if time.monotonic() >= deadline:
            return seen
        sleep_ms(READY_POLL_MS)


def classify(html: Optional[str], status: Optional[int] = None,
             url: str = "") -> str:
    """The page's state, as one word.

    `status` is positional and second, which matters: this signature is bound
    against every call site by the suite, because a sibling repo shipped two
    engines calling `classify(html, url=…)` against a `classify(html, status,
    url)` and both crashed on their FIRST fetch — invisible to import,
    `--help` and `compileall` (CLAUDE.md §17).
    """
    return classify_with_reason(html, status, url)[0]


def classify_with_reason(html: Optional[str], status: Optional[int] = None,
                         url: str = ""):
    """`(state, detail)`. The detail is for a log line and may be None."""
    if html is None:
        return ("unknown", "no response body")
    return product_parser.detect_page_state(html, status, url)


# A transport-level failure, which never reaches `classify` because no
# response arrived. Chromium reports a dead proxy as a generic error rather
# than as a timeout, and the two want OPPOSITE responses: a timeout deserves
# another try at the same exit, a dead proxy a different one (CLAUDE.md §8).
_PROXY_FAILURE_RE = re.compile(
    r"ERR_PROXY_CONNECTION_FAILED|ERR_TUNNEL_CONNECTION_FAILED"
    r"|ERR_PROXY_AUTH_UNSUPPORTED|ERR_UNEXPECTED_PROXY_AUTH"
    r"|ERR_PROXY_CERTIFICATE_INVALID|ProxyError|407\b", re.I)

_TRANSPORT_REFUSAL_RE = re.compile(
    r"ERR_CONNECTION_CLOSED|ERR_CONNECTION_RESET|ERR_EMPTY_RESPONSE"
    r"|ERR_HTTP2_PROTOCOL_ERROR|not closed cleanly|INTERNAL_ERROR", re.I)


def classify_transport_error(exc: BaseException) -> str:
    """`proxy` · `refused` · `timeout` · `other` for an exception with no response.

    Unlike montblanc-scraper, `refused` is NOT this site's normal way of
    declining — maison.kose.co.jp has never been observed refusing anything,
    including to a bare `python-requests` UA. It is kept because a dropped
    connection is a real network event on any site and because calling it a
    timeout would send a run into a retry that cannot work.
    """
    text = f"{type(exc).__name__}: {exc}"
    if _PROXY_FAILURE_RE.search(text):
        return "proxy"
    if "timeout" in text.lower() or "timed out" in text.lower():
        return "timeout"
    if _TRANSPORT_REFUSAL_RE.search(text):
        return "refused"
    return "other"


# Product-shaped links below which "served but parsed to nothing" is not
# worth calling a parser failure.
#
# Two rather than one: a single stray `/g/g…/` link appears in the site's own
# 404 page (measured: exactly 1), so a threshold of one would report the 404
# as a broken parser. A real grid links to 22-55.
PARSE_FAILURE_MIN_LINKS = 2


def looks_like_a_parse_failure(state: str, rows: int, link_count: int) -> bool:
    """True when the page was SERVED, links to products, and parsed to zero.

    That combination is this repo's bug, not the site's, and it deserves to
    say so by name — "0 products" sends the reader to check the URL when the
    thing to check is the parser (CLAUDE.md §20).

    It CAN fire here, which §20 says to check before adding the signal: rows
    come from `li.c-product__item` tiles while the link count comes from
    `/g/g…/` hrefs, and a grid page carries 48-55 of those against 24 tiles.
    A tile-markup change therefore leaves the links untouched and the rows at
    zero — exactly the case this names. It is deliberately NOT a new exit
    code: the catalogue question really was answered, so it stays
    EXIT_NO_PRODUCTS and only the `stop_reason` differs.
    """
    if rows:
        return False
    if state not in ("content", "empty"):
        return False
    return link_count >= PARSE_FAILURE_MIN_LINKS


STATE_POLICY = {
    # Product tiles rendered. The unambiguous positive.
    "content":   {"retry": False, "solve": False, "blocked": False, "parse": True},
    # A page Maison KOSÉ served with no tiles on it: a tag facet walked past
    # its end, a bogus goods code, or the site's own 404. The site answered
    # exactly what was asked, so this is an answer and not a failure.
    # EXIT_NO_PRODUCTS rather than EXIT_BLOCKED — reporting it as blocked
    # sends a user hunting for a proxy problem that is not there.
    "empty":     {"retry": False, "solve": False, "blocked": False, "parse": True},
    # A refusal with no challenge on it. There is nothing to solve — an edge
    # that declines is not offering a test — so the only move is a different
    # exit. `solve` is False on a state whose name says blocked, and that is
    # the point: §8's "detected ≠ blocking ≠ paying".
    "blocked":   {"retry": True,  "solve": False, "blocked": True,  "parse": False},
    # A challenge widget. This one IS a test and is the state that pays for a
    # solver. A fresh browser from a different exit clears some challenges
    # too, which is why `retry` is also True. Never observed on this site.
    "challenge": {"retry": True,  "solve": True,  "blocked": True,  "parse": False},
    # Not recognisably a Maison KOSÉ page: an interstitial, a proxy's error
    # page, or Chromium's own — which carries the site's hostname in its
    # <title> and would fool a title check (§18). A wait, not a spend.
    "unknown":   {"retry": True,  "solve": False, "blocked": False, "parse": False},
}


def should_retry(state: str) -> bool:
    return STATE_POLICY.get(state, STATE_POLICY["unknown"])["retry"]


def should_solve(state: str) -> bool:
    return STATE_POLICY.get(state, STATE_POLICY["unknown"])["solve"]


def counts_as_blocked(state: str) -> bool:
    return STATE_POLICY.get(state, STATE_POLICY["unknown"])["blocked"]


def should_parse(state: str) -> bool:
    return STATE_POLICY.get(state, STATE_POLICY["unknown"])["parse"]


# Whether a blocked page is worth re-fetching at all. CONSULTED by the
# engines rather than merely documented — setting it False really does stop
# the retry loop. (A sibling repo carried this constant with a paragraph of
# justification and no reader, which is the same defect as dead code that
# looks load-bearing: §17.)
RETRY_ON_BLOCKED = True

# How many times to re-fetch a blocked page when there is no pool to rotate
# through. One: without a different exit, a re-fetch from the same address is
# the same request, and a second identical request is not evidence.
BLOCK_RETRIES_WITHOUT_POOL = 1

# One solve per page. A second solve on the same page is a second bill for
# the same answer.
SOLVES_PER_PAGE = 1


def pagination_is_addressable(url: str) -> bool:
    """Can page N of this listing be fetched without fetching page N-1?

    Yes on both of this site's listing routes, and it was CHECKED rather than
    assumed (CLAUDE.md §7): page 1's own `rel=next` agrees with what the
    convention builds, on both. That is what lets `--concurrency` above 1
    mean anything here.

    A product URL is not a listing and has no page 2, so it is False — and
    the engines refuse concurrency on it with that reason rather than
    silently fetching page 1 N times.
    """
    return product_parser.is_listing_url(url)


def pages_to_plan(pages_requested: int, pages_avail: Optional[int]) -> int:
    """How many pages to actually fetch.

    Bounded by the site's own counter where it published one. On this site
    that is not merely thrift: a category listing fetched past its last page
    returns THAT LAST PAGE AGAIN, byte-identical and HTTP 200, so a run that
    asked for 50 pages of a 13-page category would fetch page 13 thirty-seven
    times and hand the deduper 888 rows to throw away.

    `pages_avail` of None means the site published no counter — which a TAG
    listing never does — and means unknown, never zero. Capping a tag run at
    zero pages would turn a working route into an empty file.
    """
    return product_parser.pages_to_fetch(pages_requested, pages_avail)


def plan_from_total(pages_requested: int, total: Optional[int]) -> int:
    """`pages_to_plan`, named for the call site that has the site's counter."""
    return pages_to_plan(pages_requested, total)


def concurrency_limit(cdp_endpoint: Optional[str]) -> Optional[int]:
    """1 over a remote CDP profile, else no limit imposed here.

    The Scraping Browser API allows ONE live connection per profile, so
    workers sharing an endpoint collide with `profile_locked`. Several `pid`s
    and one run each is the way to parallelise that path (CLAUDE.md §7).
    """
    return 1 if cdp_endpoint else None
