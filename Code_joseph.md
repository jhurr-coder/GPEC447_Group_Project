# GPEC447_Group_Project

from arcgis.gis import GIS
from arcgis.geoenrichment import Country
import pandas as pd

gis = GIS(username="gpec447sp26_11")
usa = Country.get('US', gis=gis)
all_vars = usa.enrich_variables
print(f"Total: {len(all_vars)} | Columns: {all_vars.columns.tolist()}")

PATTERN = (
    "manufactur|warehouse|transport|wholesale|"
    "naics 31|naics 32|naics 33|naics 42|naics 48|naics 49|"
    "industrial|freight|logistics|truck|distribution"
)

mask = all_vars.apply(
    lambda col: col.astype(str).str.lower().str.contains(PATTERN, na=False)
).any(axis=1)

relevant = all_vars[mask].copy()
print(f"Relevant variables: {len(relevant)}")
relevant.to_csv("relevant_industrial_vars.csv", index=False)

pd.set_option("display.max_colwidth", 50)
pd.set_option("display.max_rows", 80)
print(relevant.head(80).to_string())
------------------------------------------------------------------------------------

"""
Final recommended variables for Otay Mesa Industrial-Logistics Project
Based on the 387 variables found in GeoEnrichment.
Run this in Jupyter to enrich your study areas with these variables.
"""

import pandas as pd

# ── RECOMMENDED VARIABLES ─────────────────────────────────────────────────────

recommended = [
    # PRIMARY — Business counts (NAICS, most current/precise)
    {"variable_id": "businesses.N06_BUS",  "alias": "2025 Manufacturing (NAICS31-33) Businesses",        "priority": "HIGH", "why": "Core industrial business identifier"},
    {"variable_id": "businesses.N07_BUS",  "alias": "2025 Wholesale Trade (NAICS42) Businesses",         "priority": "HIGH", "why": "Wholesale = logistics/distribution activity"},
    {"variable_id": "businesses.N21_BUS",  "alias": "2025 Transportation/Warehouse (NAICS48-49) Businesses", "priority": "HIGH", "why": "Direct freight/logistics indicator"},
    {"variable_id": "businesses.N21A_BUS", "alias": "2025 Truck Transportation (NAICS484) Businesses",   "priority": "HIGH", "why": "Most specific trucking/freight indicator"},

    # PRIMARY — Employee counts (NAICS)
    {"variable_id": "employees.N06_EMP",   "alias": "2025 Manufacturing (NAICS31-33) Employees",         "priority": "HIGH", "why": "Employment concentration measure"},
    {"variable_id": "employees.N07_EMP",   "alias": "2025 Wholesale Trade (NAICS42) Employees",          "priority": "HIGH", "why": "Wholesale employment density"},
    {"variable_id": "employees.N21_EMP",   "alias": "2025 Transportation/Warehouse (NAICS48-49) Employees", "priority": "HIGH", "why": "Transport/warehouse employment"},
    {"variable_id": "employees.N21A_EMP",  "alias": "2025 Truck Transportation (NAICS484) Employees",    "priority": "HIGH", "why": "Trucking-specific employment"},

    # SECONDARY — Wholesale subcategories (useful for depth)
    {"variable_id": "businesses.N07A_BUS", "alias": "2025 Wholesale Durable Goods (NAICS423) Businesses","priority": "MEDIUM", "why": "Durable goods = industrial inputs"},
    {"variable_id": "employees.N07A_EMP",  "alias": "2025 Wholesale Durable Goods (NAICS423) Employees", "priority": "MEDIUM", "why": "Durable goods employment"},

    # CROSS-CHECK — SIC versions (older system, good for validation)
    {"variable_id": "businesses.S04_BUS",  "alias": "2025 Manufacturing (SIC20-39) Businesses",          "priority": "MEDIUM", "why": "Cross-check against NAICS manufacturing"},
    {"variable_id": "businesses.S05_BUS",  "alias": "2025 Transportation (SIC40-47) Businesses",         "priority": "MEDIUM", "why": "Cross-check against NAICS transport"},
    {"variable_id": "businesses.S08_BUS",  "alias": "2025 Wholesale Trade (SIC50-51) Businesses",        "priority": "MEDIUM", "why": "Cross-check against NAICS wholesale"},
    {"variable_id": "employees.S04_EMP",   "alias": "2025 Manufacturing (SIC20-39) Employees",           "priority": "MEDIUM", "why": "Cross-check employment"},
    {"variable_id": "employees.S05_EMP",   "alias": "2025 Transportation (SIC40-47) Employees",          "priority": "MEDIUM", "why": "Cross-check employment"},
    {"variable_id": "employees.S08_EMP",   "alias": "2025 Wholesale Trade (SIC50-51) Employees",         "priority": "MEDIUM", "why": "Cross-check employment"},

    # SKIP — these matched keyword but are NOT relevant
    # AutomobilesAutomotiveProducts.* — household vehicle ownership, not industrial
    # financial.X14028* — car loan data, not relevant
    # commute.ACSPUBTRAN — commuter transit, not relevant
]

df = pd.DataFrame(recommended)
pd.set_option("display.max_colwidth", 60)
pd.set_option("display.width", 130)
print("=" * 80)
print("RECOMMENDED VARIABLES FOR OTAY MESA PROJECT")
print("=" * 80)
print(df[["priority","variable_id","alias","why"]].to_string(index=False))
df.to_csv("otay_mesa_recommended_variables.csv", index=False)
print("\nSaved: otay_mesa_recommended_variables.csv")

# ── HOW TO ENRICH YOUR STUDY AREAS ───────────────────────────────────────────
print("""
── Next Step: Enrich your study areas ──────────────────────────────────────

from arcgis.gis import GIS
from arcgis.geoenrichment import enrich
import pandas as pd

gis = GIS(username="gpec447sp26_11")

# Define your study areas (Otay Mesa + comparison areas)
study_areas = [
    {"name": "Otay Mesa",    "address": "Otay Mesa, San Diego, CA"},
    {"name": "Kearny Mesa",  "address": "Kearny Mesa, San Diego, CA"},
    {"name": "Miramar",      "address": "Miramar, San Diego, CA"},
    {"name": "Sorrento Valley", "address": "Sorrento Valley, San Diego, CA"},
]

# Variables to enrich with (use enrich_name from the table above)
analysis_variables = [
    "businesses.N06_BUS",   # Manufacturing businesses
    "businesses.N07_BUS",   # Wholesale businesses
    "businesses.N21_BUS",   # Transport/warehouse businesses
    "businesses.N21A_BUS",  # Truck transportation businesses
    "employees.N06_EMP",    # Manufacturing employees
    "employees.N07_EMP",    # Wholesale employees
    "employees.N21_EMP",    # Transport/warehouse employees
    "employees.N21A_EMP",   # Truck transportation employees
]

results = enrich(
    study_areas=study_areas,
    analysis_variables=analysis_variables,
    gis=gis
)

print(results)
results.to_csv("enriched_study_areas.csv", index=False)
""")
--------------------------------------------------------------------------------------
