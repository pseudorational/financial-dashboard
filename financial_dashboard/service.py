"""Bounded, partitioned endpoint cache and session-independent orchestration."""
from collections import OrderedDict, deque
from dataclasses import dataclass
from threading import Lock
import copy
import logging
import random
import time
import uuid
from .models import Dashboard, Region, SCHEMA, MAPPING, utcnow
from .providers import ProviderError, validate_symbol

logger = logging.getLogger("financial_dashboard")
TTL = {"resolve":86400, "quote":60, "history":900, "annual":21600}
MAX_AGE = {"resolve":86400, "quote":86400, "history":86400, "annual":604800}

@dataclass
class Entry:
    value: object
    created: float
    retrieved: str

class EndpointCache:
    def __init__(self, clock=time.monotonic, sleep=time.sleep, capacity=128):
        self.clock, self.sleep, self.capacity = clock, sleep, capacity
        self.entries, self.locks, self.last_force = OrderedDict(), OrderedDict(), OrderedDict()
        self.lock_users = {}
        self.guard = Lock()
        self.budget = {}

    def _key_lock(self, key):
        with self.guard:
            if key not in self.locks:
                if len(self.locks) >= self.capacity:
                    removable = next((k for k in self.locks if self.lock_users[k] == 0), None)
                    if removable is None:
                        raise ProviderError("rate_limit", "Too many requests; retry later.")
                    del self.locks[removable]
                    del self.lock_users[removable]
                self.locks[key] = Lock()
                self.lock_users[key] = 0
            self.locks.move_to_end(key)
            self.lock_users[key] += 1
            return self.locks[key]

    def fetch(self, provider, symbol, endpoint, request, callback, deadline, force=False):
        key = (provider, symbol, endpoint, request, SCHEMA, MAPPING, "local-research" if provider.startswith("yahoo") else "synthetic")
        lock = self._key_lock(key)
        if not lock.acquire(timeout=max(0, min(10, deadline-self.clock()))):
            with self.guard:
                self.lock_users[key] -= 1
            raise ProviderError("timeout", "Request is still in progress; retry later.")
        try:
            now = self.clock()
            with self.guard:
                old = self.entries.get(key)
                if old:
                    self.entries.move_to_end(key)
                allowed_force = force and now-self.last_force.get(key, -100000) >= 15
                if old and now-old.created < TTL[endpoint] and not allowed_force:
                    return Region(copy.deepcopy(old.value), old.retrieved, "cached", cache_hit=True)
                if allowed_force:
                    self.last_force[key] = now
                    self.last_force.move_to_end(key)
                    while len(self.last_force) > self.capacity:
                        self.last_force.popitem(last=False)
            error = None
            for attempt in range(3):
                # Yahoo worker's 9-second hard timeout must fit inside the total budget.
                if deadline-self.clock() < (9.2 if provider.startswith("yahoo") else .01):
                    error = ProviderError("timeout", "Snapshot load deadline reached; refresh later.")
                    break
                with self.guard:
                    budget = self.budget.setdefault(provider, deque())
                    while budget and now-budget[0] >= 60:
                        budget.popleft()
                    if len(budget) >= 60:
                        raise ProviderError("rate_limit", "Shared provider request budget reached; retry in a minute.")
                    budget.append(now)
                try:
                    value = callback()
                    stamp = utcnow()
                    with self.guard:
                        self.entries[key] = Entry(copy.deepcopy(value), self.clock(), stamp)
                        while len(self.entries) > self.capacity:
                            self.entries.popitem(last=False)
                    logger.info("provider=%s endpoint=%s symbol=%s attempts=%d outcome=fresh", provider, endpoint, symbol, attempt+1)
                    return Region(copy.deepcopy(value), stamp, "fresh")
                except ProviderError as exc:
                    error = exc
                    if exc.category not in {"timeout", "rate_limit", "transient", "outage"} or attempt == 2:
                        break
                    delay = exc.retry_after if exc.retry_after is not None else (.5, 1.5)[attempt] + random.uniform(0,.1)
                    if delay < 0 or delay + (9.2 if provider.startswith("yahoo") else .01) > deadline-self.clock():
                        break
                    self.sleep(delay)
                    now = self.clock()
            # Fixture-only stale fallback. Yahoo retention/display permissions are unreviewed.
            if old and provider.startswith("fixture") and self.clock()-old.created <= MAX_AGE[endpoint]:
                return Region(copy.deepcopy(old.value), old.retrieved, "stale", f"Stale snapshot: {error.public_message}")
            raise error or ProviderError("outage", "Provider unavailable")
        finally:
            lock.release()
            with self.guard:
                self.lock_users[key] -= 1

class DashboardService:
    def __init__(self, provider, cache=None):
        self.provider = provider
        self.cache = cache or EndpointCache()

    def load(self, symbol, range_key="1Y", force=False):
        d = Dashboard(symbol.strip().upper(), correlation_id=uuid.uuid4().hex[:8])
        deadline = self.cache.clock() + 30
        try:
            symbol = validate_symbol(symbol)
            p = self.provider
            resolved = self.cache.fetch(p.provider_id, symbol, "resolve", "metadata", lambda:p.resolve_instrument(symbol), deadline, force)
            d.instrument = resolved.data
        except ProviderError as exc:
            d.error = exc.public_message
            return d
        i = d.instrument
        for region, endpoint, request, callback in [
            ("quote", "quote", "regular-market", lambda:p.get_quote(i)),
            ("history", "history", f"{range_key}:daily:auto-adjust=True", lambda:p.get_price_history(i, range_key)),
            ("financials", "annual", "annual:minimum=4", lambda:p.get_annual_financials(i, 4)),
        ]:
            try:
                setattr(d, region, self.cache.fetch(p.provider_id, f"{i.symbol}@{i.exchange}", endpoint, request, callback, deadline, force))
            except ProviderError as exc:
                setattr(d, region, Region(message=exc.public_message))
                logger.info("provider=%s endpoint=%s symbol=%s category=%s correlation=%s", p.provider_id, endpoint, i.symbol, exc.category, d.correlation_id)
        return d
