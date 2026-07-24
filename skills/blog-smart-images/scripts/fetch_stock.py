#!/usr/bin/env python3
"""fetch_stock.py — multi-provider stock photo fetcher with quota-aware failover.

Providers (activated only if their env key exists):
  pexels    PEXELS_API_KEY        free tier ~200 req/hour  (default cap 190/h)
  unsplash  UNSPLASH_ACCESS_KEY   free demo  ~50 req/hour  (default cap 45/h)

Failover logic (per request):
  try providers in --order; skip a provider when (a) no key, (b) its rolling
  1-hour request count >= its cap, or (c) the API answered 429/403 in this run
  or reported X-Ratelimit-Remaining <= reserve (2). First healthy provider wins;
  the switch is logged. Usage persists in .stock-usage.json next to --out.

Usage:
  python3 fetch_stock.py --query "bison crossing road yellowstone" \
      --n 3 --out candidates/ [--order pexels,unsplash] [--portrait]
  python3 fetch_stock.py --selftest        # offline check of the failover logic

Env overrides: PEXELS_HOURLY_CAP, UNSPLASH_HOURLY_CAP.
Every downloaded image gets a sidecar .json with source, photographer, page URL
and license note — the report and (for Unsplash) the caption credit need them.
Unsplash API guidelines are honored: the download_location trigger is called and
photos should be credited "Photo by <name> on Unsplash" in the caption.
"""
import argparse, json, os, sys, time, urllib.request, urllib.parse, urllib.error
from pathlib import Path

RESERVE = 2  # leave this many requests unused when the API reports remaining

# Pexels sits behind a CDN that answers 403 to the default urllib UA.
UA = "blog-smart-images/0.1 (+https://github.com/Waybox-AI)"

CAPS = {
    "pexels": int(os.environ.get("PEXELS_HOURLY_CAP", "190")),
    "unsplash": int(os.environ.get("UNSPLASH_HOURLY_CAP", "45")),
}
KEYS = {
    "pexels": os.environ.get("PEXELS_API_KEY"),
    "unsplash": os.environ.get("UNSPLASH_ACCESS_KEY"),
}

class Quota:
    """Rolling 1-hour request log per provider, persisted to JSON."""
    def __init__(self, path):
        self.path = Path(path); self.data = {}
        if self.path.exists():
            try: self.data = json.loads(self.path.read_text())
            except Exception: self.data = {}
    def _prune(self, prov):
        cut = time.time() - 3600
        self.data[prov] = [t for t in self.data.get(prov, []) if t > cut]
    def used(self, prov):
        self._prune(prov); return len(self.data.get(prov, []))
    def ok(self, prov, cap=None):
        return self.used(prov) < (cap if cap is not None else CAPS[prov])
    def hit(self, prov, n=1):
        self._prune(prov); self.data.setdefault(prov, []).extend([time.time()] * n)
        self.path.write_text(json.dumps(self.data))

def _get(url, headers):
    req = urllib.request.Request(url, headers={"User-Agent": UA, **headers})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode()), dict(r.headers)

def _download(url, dest, headers=None):
    req = urllib.request.Request(url, headers={"User-Agent": UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=60) as r, open(dest, "wb") as f:
        f.write(r.read())

def search_pexels(query, n, portrait, quota, out):
    key = KEYS["pexels"]
    q = urllib.parse.urlencode({"query": query, "per_page": n,
                                "orientation": "portrait" if portrait else "landscape"})
    data, hdr = _get(f"https://api.pexels.com/v1/search?{q}", {"Authorization": key})
    quota.hit("pexels")
    rem = hdr.get("X-Ratelimit-Remaining")
    if rem is not None and int(rem) <= RESERVE:
        raise RuntimeError("pexels remaining quota at reserve")
    got = []
    for ph in data.get("photos", [])[:n]:
        fn = out / f"pexels-{ph['id']}.jpg"
        _download(ph["src"].get("large2x") or ph["src"]["original"], fn)
        quota.hit("pexels")
        meta = {"source": "pexels", "id": ph["id"], "photographer": ph.get("photographer"),
                "page": ph.get("url"), "alt": ph.get("alt"),
                "license": "Pexels License (free commercial use; attribution appreciated, not required)",
                "credit_caption_required": False}
        fn.with_suffix(".json").write_text(json.dumps(meta, ensure_ascii=False, indent=2))
        got.append(str(fn))
    return got

def search_unsplash(query, n, portrait, quota, out):
    key = KEYS["unsplash"]
    q = urllib.parse.urlencode({"query": query, "per_page": n,
                                "orientation": "portrait" if portrait else "landscape"})
    auth = {"Authorization": f"Client-ID {key}", "Accept-Version": "v1"}
    data, hdr = _get(f"https://api.unsplash.com/search/photos?{q}", auth)
    quota.hit("unsplash")
    rem = hdr.get("X-Ratelimit-Remaining")
    if rem is not None and int(rem) <= RESERVE:
        raise RuntimeError("unsplash remaining quota at reserve")
    got = []
    for ph in data.get("results", [])[:n]:
        # API guideline: trigger the download endpoint before using the file
        try:
            _get(ph["links"]["download_location"], auth); quota.hit("unsplash")
        except Exception:
            pass
        fn = out / f"unsplash-{ph['id']}.jpg"
        _download(ph["urls"].get("full", ph["urls"]["regular"]) + "&w=2400", fn)
        meta = {"source": "unsplash", "id": ph["id"],
                "photographer": (ph.get("user") or {}).get("name"),
                "page": (ph.get("links") or {}).get("html"),
                "alt": ph.get("alt_description"),
                "license": "Unsplash License (free commercial use)",
                "credit_caption_required": True,
                "credit_caption": f"Photo by {(ph.get('user') or {}).get('name','?')} on Unsplash"}
        fn.with_suffix(".json").write_text(json.dumps(meta, ensure_ascii=False, indent=2))
        got.append(str(fn))
    return got

SEARCHERS = {"pexels": search_pexels, "unsplash": search_unsplash}

def fetch(query, n, out, order, portrait=False, quota=None, searchers=SEARCHERS):
    out = Path(out); out.mkdir(parents=True, exist_ok=True)
    quota = quota or Quota(out / ".stock-usage.json")
    dead = set()
    for prov in order:
        if prov not in searchers: continue
        if not KEYS.get(prov):
            print(f"[skip] {prov}: no key"); continue
        if prov in dead: continue
        if not quota.ok(prov):
            print(f"[switch] {prov} hourly cap reached ({quota.used(prov)}/{CAPS[prov]}) → next provider")
            continue
        try:
            files = searchers[prov](query, n, portrait, quota, out)
            if files:
                print(f"[ok] {prov}: {len(files)} candidate(s) for {query!r} "
                      f"(used {quota.used(prov)}/{CAPS[prov]} this hour)")
                return files
            print(f"[miss] {prov}: 0 results → next provider")
        except urllib.error.HTTPError as e:
            if e.code in (403, 429):
                print(f"[switch] {prov} rate-limited (HTTP {e.code}) → next provider"); dead.add(prov)
            else:
                print(f"[warn] {prov} HTTP {e.code} → next provider")
        except Exception as e:
            print(f"[warn] {prov}: {e} → next provider")
    print(f"[none] no provider could serve {query!r} (all keyless/capped/empty)")
    return []

def selftest():
    """Offline: verify cap gating, 429 failover, and no-key skip."""
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        q = Quota(Path(td) / "u.json")
        KEYS.update({"pexels": "x", "unsplash": "x"})
        # 1) unsplash at cap → pexels chosen
        q.hit("unsplash", CAPS["unsplash"])
        calls = []
        fake = {"pexels": lambda *a, **k: calls.append("pexels") or ["p.jpg"],
                "unsplash": lambda *a, **k: calls.append("unsplash") or ["u.jpg"]}
        r = fetch("t", 1, td, ["unsplash", "pexels"], quota=q, searchers=fake)
        assert r == ["p.jpg"] and calls == ["pexels"], (r, calls)
        # 2) first provider throws 429 → second used
        def boom(*a, **k): raise urllib.error.HTTPError("u", 429, "rl", {}, None)
        calls.clear()
        r = fetch("t", 1, td, ["pexels", "unsplash"],
                  quota=Quota(Path(td) / "u2.json"),
                  searchers={"pexels": boom, "unsplash": fake["unsplash"]})
        assert r == ["u.jpg"] and calls == ["unsplash"], (r, calls)
        # 3) no keys at all → empty
        KEYS.update({"pexels": None, "unsplash": None})
        assert fetch("t", 1, td, ["pexels", "unsplash"], quota=Quota(Path(td) / "u3.json")) == []
        KEYS.update({"pexels": "x", "unsplash": "x"})
    print("selftest OK: cap-gate, 429-failover, no-key skip")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--query"); ap.add_argument("--n", type=int, default=3)
    ap.add_argument("--out", default="candidates")
    ap.add_argument("--order", default=os.environ.get("STOCK_PROVIDER_ORDER", "pexels,unsplash"))
    ap.add_argument("--portrait", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest: selftest(); sys.exit(0)
    if not a.query: ap.error("--query required (or --selftest)")
    fetch(a.query, a.n, a.out, [p.strip() for p in a.order.split(",") if p.strip()])
