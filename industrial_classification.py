"""
industrial_classification.py
GPEC 447 — Otay Mesa Industrial-Logistics project
Shared, single source of truth for "what counts as industrial / logistics".

Every teammate imports from this file so the definition is identical everywhere:
    from industrial_classification import (
        classify_industry, is_broad, is_core,
        INDUSTRIAL_NAICS_GROUPS, BROAD_PREFIXES, CORE_KEEP, CORE_EXCLUDE,
    )

Definition (agreed with the project design + Prof. Zaslavsky's freight-dependence note):
  Manufacturing                 NAICS 31-33   -> high freight dependence
  Wholesale trade               NAICS 42      -> distribution / logistics
  Transportation & warehousing  NAICS 48-49   -> direct freight indicator
  Industrial machinery repair   NAICS 8113    -> industrial ecosystem (broad only)

This mirrors the ACS industry groups used in Canyu's standalone notebook
(manufacturing + wholesale + transportation/warehousing), so the business-point
work (Christian), the GeoEnrichment work (Joseph) and the tract work (Canyu)
all describe the SAME industrial universe.
"""

from __future__ import annotations

# --- group labels -----------------------------------------------------------
INDUSTRIAL_NAICS_GROUPS = {
    "Manufacturing":                  ("31", "32", "33"),
    "Wholesale Trade":                ("42",),
    "Transportation and Warehousing": ("48", "49"),
    "Industrial Machinery Repair":    ("8113",),
}

# --- broad vs core membership (kept identical to the original team code) -----
# Broad = whole industrial ecosystem.
BROAD_PREFIXES = ("31", "32", "33", "42", "48", "49", "8113")

# Core = freight-relevant only; drops brokers, passenger, pipeline, sightseeing.
CORE_KEEP = (
    "31", "32", "33",                         # manufacturing
    "421", "422", "423", "424",               # wholesale / distribution
    "481", "483", "484", "488",               # air/water/truck freight + support
    "491", "492", "493",                      # postal, couriers, warehousing
    "8113",                                   # industrial machinery repair
)
CORE_EXCLUDE = (
    "425",   # wholesale brokers / electronic markets (no physical goods handling)
    "485",   # passenger ground transportation
    "486",   # pipeline transportation
    "487",   # scenic / sightseeing transportation
)


def normalize_naics(naics) -> str:
    """Return a clean NAICS string: digits only, trailing '.0' removed, no spaces."""
    s = str(naics).strip()
    if s.endswith(".0"):
        s = s[:-2]
    # keep digits only (handles '3361 ', '3361.0', '3361/2' etc. -> '3361')
    out = []
    for ch in s:
        if ch.isdigit():
            out.append(ch)
        else:
            break
    return "".join(out)


def classify_industry(naics) -> str:
    """Map a NAICS code to one of the industrial group labels, else 'Other'."""
    code = normalize_naics(naics)
    if code.startswith(("31", "32", "33")):
        return "Manufacturing"
    if code.startswith("8113"):
        return "Industrial Machinery Repair"
    if code.startswith("42"):
        return "Wholesale Trade"
    if code.startswith(("48", "49")):
        return "Transportation and Warehousing"
    return "Other"


def is_broad(naics) -> bool:
    """True if the code is in the broad industrial ecosystem."""
    return normalize_naics(naics).startswith(BROAD_PREFIXES)


def is_core(naics) -> bool:
    """True if the code is freight-relevant core (keep-set minus exclude-set)."""
    code = normalize_naics(naics)
    return code.startswith(CORE_KEEP) and not code.startswith(CORE_EXCLUDE)


def add_classification(df, naics_col: str = "naics"):
    """
    Convenience for pandas: returns a copy of df with a normalized 'naics',
    plus 'industry_group', 'is_broad', 'is_core' columns.
    """
    out = df.copy()
    out[naics_col] = out[naics_col].map(normalize_naics)
    out["industry_group"] = out[naics_col].map(classify_industry)
    out["is_broad"] = out[naics_col].map(is_broad)
    out["is_core"] = out[naics_col].map(is_core)
    return out


if __name__ == "__main__":
    # quick self-test
    samples = ["3361", "3361.0", "4231", "4251", "4841", "4851", "8113", "5221", "23"]
    for s in samples:
        print(f"{s:>8} -> group={classify_industry(s):28s} "
              f"broad={is_broad(s)!s:5} core={is_core(s)!s}")
