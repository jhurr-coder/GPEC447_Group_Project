# GPEC447_Group_Project

"""
ArcGIS GeoEnrichment - Industrial Variable Explorer v2
Run this locally on your machine where the API returns 200.

Requires: requests, pandas
Install: pip install requests pandas
"""

import requests
import pandas as pd
import json

KEYWORDS = [
    "manufactur", "warehouse", "warehousing", "transport",
    "industrial", "freight", "logistics", "wholesale",
    "truck", "distribution", "naics", "trade"
]

PRIORITY_NAICS = ["31", "32", "33", "42", "48", "49"]

def fetch_collections(keyword):
    url = (
        f"https://geoenrich.arcgis.com/arcgis/rest/services/World/"
        f"GeoenrichmentServer/Geoenrichment/dataCollections"
        f"?f=json&keyword={keyword}"
    )
    try:
        resp = requests.get(url, timeout=15)
        print(f"  [{resp.status_code}] {keyword}")
        if resp.status_code == 200 and resp.text.strip():
            return resp.json()
    except Exception as e:
        print(f"  Error: {e}")
    return None


def flatten_collections(data):
    """
    Recursively extract all variable-like dicts from nested API response.
    Handles various ArcGIS response structures.
    """
    rows = []

    def recurse(obj, path=""):
        if isinstance(obj, dict):
            # If it looks like a variable record, capture it
            if any(k in obj for k in ["id", "alias", "description", "variableID"]):
                rows.append({
                    "id":          obj.get("id", obj.get("variableID", "")),
                    "alias":       obj.get("alias", obj.get("name", "")),
                    "description": obj.get("description", ""),
                    "category":    obj.get("category", obj.get("datasetID", path)),
                    "vintage":     obj.get("vintage", obj.get("year", "")),
                    "units":       obj.get("units", ""),
                })
            for k, v in obj.items():
                recurse(v, path=f"{path}.{k}")
        elif isinstance(obj, list):
            for item in obj:
                recurse(item, path)

    recurse(data)
    return rows


def is_relevant(row):
    text = " ".join(str(v) for v in row.values()).lower()
    return any(kw in text for kw in KEYWORDS)


def priority_score(row):
    text = " ".join(str(v) for v in row.values())
    for naics in PRIORITY_NAICS:
        if naics in text:
            return "HIGH"
    if any(kw in text.lower() for kw in ["manufactur", "warehouse", "freight", "wholesale"]):
        return "HIGH"
    if any(kw in text.lower() for kw in ["transport", "truck", "distribution", "logistics"]):
        return "MEDIUM"
    return "LOW"


def save_raw(data, keyword):
    """Save raw JSON response so you can inspect it manually."""
    with open(f"raw_{keyword}.json", "w") as f:
        json.dump(data, f, indent=2)
    print(f"  Saved raw response to raw_{keyword}.json")


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("GeoEnrichment Industrial Variable Explorer v2")
    print("=" * 60)

    all_rows = []
    search_terms = [
        "manufacturing", "warehousing", "transportation",
        "wholesale", "freight", "industrial", "logistics"
    ]

    for kw in search_terms:
        data = fetch_collections(kw)
        if data:
            save_raw(data, kw)

            # Show raw structure on first hit
            if not all_rows:
                print(f"\n  Raw keys from '{kw}' response: {list(data.keys()) if isinstance(data, dict) else type(data)}")
                if isinstance(data, dict):
                    for k, v in data.items():
                        if isinstance(v, list):
                            print(f"    '{k}': list of {len(v)}")
                            if v and isinstance(v[0], dict):
                                print(f"      First item keys: {list(v[0].keys())}")
                        else:
                            print(f"    '{k}': {str(v)[:100]}")

            rows = flatten_collections(data)
            relevant = [r for r in rows if is_relevant(r)]
            print(f"  Extracted {len(rows)} records, {len(relevant)} relevant")
            all_rows.extend(relevant)

    # ── Deduplicate and score ──────────────────────────────────────────────────
    if all_rows:
        df = pd.DataFrame(all_rows).drop_duplicates(subset=["id", "alias"])
        df["priority"] = df.apply(priority_score, axis=1)
        df = df.sort_values(["priority", "alias"])

        print("\n" + "=" * 60)
        print(f"RESULTS: {len(df)} unique relevant variables found")
        print("=" * 60)
        print(df[["id", "alias", "category", "vintage", "priority"]].to_string(index=False))

        df.to_csv("industrial_variables_geoenrichment.csv", index=False)
        print("\nSaved to: industrial_variables_geoenrichment.csv")

        # Summary by priority
        print("\n── Priority Summary ──")
        print(df["priority"].value_counts().to_string())

    else:
        print("\nNo variables extracted.")
        print("Check the raw_*.json files to inspect the API response structure.")
        print("\nFallback: manually export from the Data Browser UI using:")
        print("  1. Search each term in the browser")
        print("  2. Click 'Export as CSV' or 'Export as JSON'")
        print("  3. Share the file here for analysis")

    # ── Also try fetching all collections without keyword filter ──────────────
    print("\n── Trying full collections list (no keyword filter) ──")
    url_all = (
        "https://geoenrich.arcgis.com/arcgis/rest/services/World/"
        "GeoenrichmentServer/Geoenrichment/dataCollections?f=json&countryCode=US"
    )
    try:
        resp = requests.get(url_all, timeout=20)
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200 and resp.text.strip():
            data_all = resp.json()
            save_raw(data_all, "ALL_collections")
            rows_all = flatten_collections(data_all)
            relevant_all = [r for r in rows_all if is_relevant(r)]
            print(f"Total records: {len(rows_all)}, Relevant: {len(relevant_all)}")
            if relevant_all:
                df_all = pd.DataFrame(relevant_all).drop_duplicates()
                df_all["priority"] = df_all.apply(priority_score, axis=1)
                df_all.to_csv("industrial_variables_all_collections.csv", index=False)
                print("Saved to: industrial_variables_all_collections.csv")
                print(df_all[["id","alias","category","priority"]].to_string(index=False))
    except Exception as e:
        print(f"Error: {e}")


import sys
!{sys.executable} -m pip install requests pandas
