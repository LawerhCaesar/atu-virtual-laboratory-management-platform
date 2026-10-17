"""Public learning excerpts: fixed upstream URLs, bounded I/O and shared caching."""
import json
import secrets
from urllib.error import URLError
from urllib.parse import quote
from urllib.request import HTTPRedirectHandler, Request, build_opener

from django.core.cache import cache
from django.utils.html import strip_tags

TOPICS = (
    "Regenerative braking", "Four-stroke engine", "Internal combustion engine",
    "Fuel injection", "Engine control unit", "Ignition timing", "Air–fuel ratio",
    "Turbocharger", "Variable valve timing", "Engine cooling", "Thermostat",
    "Electric vehicle", "Battery electric vehicle", "Electric motor",
    "Lithium-ion battery", "Battery management system", "Charging station",
    "Hybrid electric vehicle", "Plug-in hybrid", "Fuel cell vehicle", "Fuel cell",
    "Hydrogen vehicle", "Vehicle dynamics", "Anti-lock braking system",
    "Electronic stability control", "Traction control system", "Differential (mechanical device)",
    "Automotive aerodynamics", "Suspension (vehicle)", "Tire", "Torque",
    "Power (physics)", "Sensor", "Crankshaft", "Piston", "Camshaft",
    "Oxygen sensor", "Throttle", "On-board diagnostics", "Continuously variable transmission",
)
LICENSE_URL = "https://creativecommons.org/licenses/by-sa/4.0/"
POOL_KEY = "homepage-learning:online:v1"
REFRESH_KEY = "homepage-learning:refresh:v1"
AFDC = "https://afdc.energy.gov/vehicles/"
BACKUP_FACTS = (
    {"id": "backup-hybrid-braking", "title": "Braking can recover energy",
     "text": "Hybrid vehicles can use their electric motor as a generator during braking, storing some of the recovered energy in the battery.",
     "source_url": AFDC + "electric-basics-hev"},
    {"id": "backup-hybrid-power", "title": "A hybrid combines two power sources",
     "text": "A hybrid electric vehicle combines an internal combustion engine with an electric motor and a battery. Its battery can be charged through regenerative braking.",
     "source_url": AFDC + "electric-basics-hev"},
    {"id": "backup-hydrogen-power", "title": "Hydrogen can power an electric drive",
     "text": "A fuel cell electric vehicle converts energy stored in hydrogen into electricity that powers an electric motor.",
     "source_url": AFDC + "fuel-cell"},
    {"id": "backup-fuel-cell-battery", "title": "Fuel-cell vehicles can have batteries too",
     "text": "A fuel cell vehicle's battery can store energy recovered during braking and supplement the power supplied by its fuel cell.",
     "source_url": AFDC + "how-do-fuel-cell-electric-cars-work"},
    {"id": "backup-converter", "title": "One vehicle can use different voltages",
     "text": "A DC/DC converter can reduce the traction battery's high voltage to the lower voltage used by vehicle accessories and the auxiliary battery.",
     "source_url": AFDC + "how-do-fuel-cell-electric-cars-work"},
)


class NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def backup_fact(excluded=()):
    candidates = [fact for fact in BACKUP_FACTS if fact["id"] not in excluded]
    # If the small offline pool is exhausted, still avoid the current fact.
    candidates = candidates or [fact for fact in BACKUP_FACTS if not excluded or fact["id"] != excluded[-1]]
    return {**secrets.choice(candidates), "source_name": "U.S. Department of Energy · AFDC",
            "mode": "backup", "credit": "Source-checked backup fact", "license_url": ""}


def fetch_excerpt(topic):
    request = Request(
        "https://en.wikipedia.org/api/rest_v1/page/summary/" + quote(topic.replace(" ", "_"), safe=""),
        headers={"User-Agent": "ATUVirtualLaboratory/1.0 (https://atu-virtual-laboratory-staging.onrender.com/)",
                 "Accept": "application/json"},
    )
    with build_opener(NoRedirects()).open(request, timeout=2) as response:
        raw = response.read(65537)
    if len(raw) > 65536:
        raise ValueError("Upstream excerpt exceeds limit")
    data = json.loads(raw)
    if not isinstance(data, dict) or data.get("type") != "standard" or not isinstance(data.get("extract"), str):
        raise ValueError("Not an educational article summary")
    text = " ".join(strip_tags(data["extract"]).split())
    if len(text) < 50:
        raise ValueError("Article excerpt is too short")
    shortened = len(text) > 420
    if shortened:
        text = text[:417].rsplit(" ", 1)[0] + "…"
    return {"id": topic, "title": topic, "text": text, "source_name": "Wikipedia contributors",
            "source_url": "https://en.wikipedia.org/wiki/" + quote(topic.replace(" ", "_"), safe=""),
            "mode": "online", "credit": "Wikipedia excerpt" + (" (shortened)" if shortened else ""),
            "license_url": LICENSE_URL}


def random_fact(excluded=()):
    pool = cache.get(POOL_KEY, {})
    # One upstream request per minute per cache, independent of visitor count.
    # Both a timeout and cooldown apply when the provider is unavailable.
    if cache.add(REFRESH_KEY, True, timeout=60):
        unseen = [topic for topic in TOPICS if topic not in pool and topic not in excluded]
        choices = unseen or [topic for topic in TOPICS if topic not in excluded]
        try:
            fact = fetch_excerpt(secrets.choice(choices or TOPICS))
            pool[fact["id"]] = fact
            cache.set(POOL_KEY, pool, timeout=86400)
        except (URLError, OSError, ValueError, TypeError):
            pass
    candidates = [fact for key, fact in pool.items() if key not in excluded]
    if candidates:
        fact = dict(secrets.choice(candidates))
        fact["credit"] += " · cached online source"
        return fact
    return backup_fact(excluded)
