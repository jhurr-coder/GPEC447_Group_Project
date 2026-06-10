# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.19.3
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% [markdown]
# # GPEC 447 — Project Notebook
#
# ## 1. Project Title
#
# **Industrial–Logistics Coupling in the Otay Mesa Border Zone:  
# A Spatial Analysis of Freight Infrastructure and Industrial Activity in San Diego**
#
# ---
#
# ## 2. Team Members
#
# | Name | Student ID |
# |------|------------|
# | Christian Phouasalith | gpec447sp26_23 |
# | Joseph Hurr | gpec447sp26_11 |
# | Canyu Li | *add ID* |
#
# > **Notebook structure.** This report summarizes the project across all 12 required sections. The detailed analysis lives in three component notebooks, each runnable independently:
# > - **`Code_christian.ipynb`** — business geocoding (raw license CSVs → NAICS classification → ArcGIS geocode → county/planning join → distance-to-freight-road)
# > - **`Code_canyu_June_7th.ipynb`** — tract-level analysis (Census ACS + LODES workplace jobs, zoning/land-use overlays, proximity indicators)
# > - **`Code_Joseph.ipynb`** — business-point indicators (POE distance, freight-corridor buffers, statistics, maps)
#

# %% [markdown]
# ## 3. Research Question & Importance
#
# ### Question
# Is industrial activity in the Otay Mesa border area more strongly associated with ports of entry (POEs) and major freight corridors than industrial activity in comparable non-border industrial areas of San Diego?
#
# ### Intended Audience
# Regional planners, economic development agencies (SANDAG, City of San Diego), cross-border logistics operators, and policymakers considering infrastructure investments around the proposed Otay Mesa East port of entry.
#
# ### Business Case
# San Diego's Otay Mesa district sits at one of the busiest commercial border crossings in the world. Understanding whether industrial clustering there is genuinely organized around port access — rather than simply reflecting leftover land use patterns — has direct implications for:
# - Land use planning decisions near the proposed Otay Mesa East POE
# - Infrastructure investment prioritization for freight corridors
# - Economic development strategies targeting cross-border logistics
#
# ### Evolution from Proposal
# The core question remained consistent with the project proposal. The primary methodological evolution was a shift from industrial zone polygons as the unit of analysis to two complementary units — census tracts (Canyu) and geocoded business license records (Joseph and Christian) — following feedback that San Diego's industrial zoning reflects historical land allocation rather than deliberate freight-access decisions. A second evolution, in response to instructor feedback, was replacing ESRI GeoEnrichment with Census LODES workplace-jobs data for the tract-level activity measure.
#

# %% [markdown]
# ## 4. Background & Literature
#
# ### References
#
# 1. **SANDAG FreightViewer** — Interactive visualization of San Diego's freight network, ports of entry, and major roads.  
#    [https://gis.sandag.org/FreightViewer/](https://gis.sandag.org/FreightViewer/)  
#    *Provided the freight infrastructure reference layers (POE points, 45 major road segments) used in both the tract-level and business-point analyses.*
#
# 2. **US Census Bureau — American Community Survey (ACS) 5-Year Estimates, 2019–2023 (DP03)**  
#    [https://www.census.gov/programs-surveys/acs](https://www.census.gov/programs-surveys/acs)  
#    *Industry-of-employment counts by tract. Clarified that ACS measures where industrial workers* live*, not where they* work* — motivating the addition of LODES as the primary activity measure.*
#
# 3. **US Census LEHD LODES8 — Workplace Area Characteristics (WAC)**  
#    [https://lehd.ces.census.gov/data/](https://lehd.ces.census.gov/data/)  
#    *Jobs by 2-digit NAICS sector at the workplace location. Adopted as the primary tract-level activity measure because it captures where industrial activity is physically located.*
#
# 4. **City of San Diego — Zoning and Parcel Information Portal (ZAPP)**  
#    [https://www.arcgis.com/apps/instant/sidebar/index.html?appid=75f6a5d68aee481f8ff48240bcaa1239](https://www.arcgis.com/apps/instant/sidebar/index.html?appid=75f6a5d68aee481f8ff48240bcaa1239)  
#    *Revealed that San Diego's industrial zoning reflects "leftover land" allocation rather than freight-access optimization — the key limitation that motivated the shift from zone polygons to business and employment data.*
#
# 5. **US Census TIGER/Line Cartographic Boundary Files, 2023**  
#    [https://www2.census.gov/geo/tiger/GENZ2023/](https://www2.census.gov/geo/tiger/GENZ2023/)  
#    *Census tract geometries (736 San Diego County tracts), the spatial unit for the tract-level analysis and the SD County clip boundary for the business-point analyses.*
#
# 6. **GADM — Global Administrative Areas, USA Level 2**  
#    [https://gadm.org/](https://gadm.org/)  
#    *San Diego County administrative boundary used for spatial filtering.*
#
# ### How References Shaped the Analysis
# The ZAPP zoning layer directly prompted the shift away from industrial zone polygons. The contrast between ACS (residence-based) and LODES (workplace-based) employment measures led to using LODES as the primary activity indicator. SANDAG's freight network data provided the common infrastructure reference layer across all three component analyses.
#

# %% [markdown]
# ## 5. Python Packages
#
# The packages below are imported and described in the code cell that follows.  
# **Evolution from proposal:** `arcgis.geoenrichment` is no longer required for the tract-level analysis — Census LODES provides equivalent workplace-jobs data without ESRI dependency (it remains available as an optional cross-check only). `scipy.stats` was added to support statistical significance testing not anticipated in the proposal.
#

# %%
# ── Spatial analysis ──────────────────────────────────────────────────────────
import geopandas as gpd        # Spatial dataframes, CRS transformation, spatial joins
import pandas as pd            # Tabular data manipulation and aggregation
import numpy as np             # Numerical operations and array math

# ── Geometry ──────────────────────────────────────────────────────────────────
from shapely.geometry import Point, box   # Point and polygon construction

# ── Visualization ─────────────────────────────────────────────────────────────
import matplotlib.pyplot as plt           # Static maps and charts
import matplotlib.patches as mpatches     # Filled legend patches
from matplotlib.lines import Line2D       # Custom legend line elements

# ── Statistical testing ───────────────────────────────────────────────────────
from scipy.stats import mannwhitneyu      # Non-parametric group comparison
from scipy.stats import chi2_contingency  # Proportion test for binary outcomes
from scipy.stats import gaussian_kde      # Kernel density estimation for heatmaps

# ── Network requests ──────────────────────────────────────────────────────────
import requests                # Fetching GeoJSON / LODES layers from public APIs
from io import BytesIO         # In-memory file handling for remote files

import warnings
warnings.filterwarnings("ignore")

print("All packages imported successfully.")


# %% [markdown]
# ## 6. Data Sources
#
# | Source | URL | Description |
# |--------|-----|-------------|
# | SD Business License Records | Internal (City of San Diego) | Active business license records filtered to industrial NAICS |
# | Census TIGER Tracts 2023 | [Link](https://www2.census.gov/geo/tiger/GENZ2023/shp/cb_2023_06_tract_500k.zip) | San Diego County census tract geometries (736 tracts) |
# | ACS 5-Year 2019–2023 (DP03) | [Link](https://api.census.gov/data/2022/acs/acs5/profile) | Tract-level industry-of-employment (resident-based, context) |
# | LEHD LODES8 WAC | [Link](https://lehd.ces.census.gov/data/lodes/LODES8/ca/wac/) | Workplace jobs by 2-digit NAICS sector (primary activity measure) |
# | SANDAG POE Points | [Link](https://gis.sandag.org/FreightViewer/data/poe_points_update.json) | Port of entry point locations |
# | SANDAG Major Roads | [Link](https://gis.sandag.org/FreightViewer/data/MajorRoads_20171002.json) | Major freight road network (45 features) |
# | SD Community Planning Districts | Internal / SanGIS | Official city planning area boundaries (`Community_Plan_SD.geojson`) |
# | SD Zoning Base | [Link](https://geo.sandag.org/server/rest/directories/downloads/Zoning_Base_SD.geojson) | All city base zone polygons |
# | SD General Plan Land Use | SanGIS `General_Plan_Land_Use_SD` | General plan land-use designations |
# | GADM USA Level 2 | [Link](https://gadm.org/) | County administrative boundary |
#
# ### Evolution from Proposal
# The proposal relied on industrial zone polygons. These were replaced by (a) geocoded business license records and (b) tract-level LODES workplace jobs. The ACS API is retained as context only. ESRI GeoEnrichment was dropped as a dependency.
#
# ### Data Quality Concerns
# - **Geocoding validity:** Geocode scores (80–100) indicate address-matching confidence, not whether the registered address is an operational freight facility. A sample address-validity worksheet is included in the tract notebook (Section 9c).
# - **ACS vs. LODES:** ACS counts industrial workers by residence; LODES counts jobs by workplace. LODES is used as the primary activity measure for that reason.
# - **SANDAG roads:** The major roads layer dates to 2017.
# - **Desired but unavailable:** Tijuana-side industrial data; parcel-level operational land use; drive-time network distances to POEs.
#

# %%
# Data sources load live from URLs throughout the component notebooks.
# Documented here for reproducibility and zip-archive inclusion.

DATA_SOURCES = {
    "census_tracts":  "https://www2.census.gov/geo/tiger/GENZ2023/shp/cb_2023_06_tract_500k.zip",
    "acs_api":        "https://api.census.gov/data/2022/acs/acs5/profile",
    "lodes_wac":      "https://lehd.ces.census.gov/data/lodes/LODES8/ca/wac/",
    "sandag_poe":     "https://gis.sandag.org/FreightViewer/data/poe_points_update.json",
    "sandag_roads":   "https://gis.sandag.org/FreightViewer/data/MajorRoads_20171002.json",
    "sd_zoning_base": "https://geo.sandag.org/server/rest/directories/downloads/Zoning_Base_SD.geojson",
}

for name, url in DATA_SOURCES.items():
    print(f"{name:16s}: {url}")


# %% [markdown]
# ## 7. Data Cleaning
#
# Cleaning was performed across the three component analyses. More wrangling was required than the proposal anticipated, primarily due to NAICS code formatting in the raw business data and the discovery that some geocoded businesses fell outside San Diego County.
#
# ### Tract-level (Canyu)
# - Corrected ACS denominator to DP03_0032E (civilian employed 16+); cast all employment columns to numeric.
# - Aggregated LODES block-level jobs to tracts via the 15-digit `w_geocode` → 11-digit GEOID crosswalk.
# - Built study-area labels from a fixed `CPNAME → label` map on Community Plan districts.
#
# ### Business-point geocoding (Christian)
# - Concatenated two raw business-license CSVs (`tr_active1.csv`, `tr_active2.csv`); standardized column names; cleaned NAICS codes (removed `.0` float artifacts).
# - Built **Broad** and **Core** industrial definitions from NAICS prefixes; Core excludes 425/485/486/487.
# - Geocoded addresses via ArcGIS `batch_geocode`; kept only status "M" (matched) records.
# - Clipped to San Diego County census tracts; assigned planning area via spatial join.
# - Exported `industrial_businesses_core_geocoded.csv` (the input for Joseph's indicators).
#
# ### Business-point indicators (Joseph)
# - Assigned subareas via spatial join on Community Plan districts; computed POE and road distances and buffer flags.
#
# > **Team-review fixes applied in Christian's final code:** the `area_sqmi` unit bug is corrected (now divides by `METERS_PER_MILE**2` to match the EPSG:3310 meter CRS), and the undefined `planning_name_col` rename line was removed. Coordinates were confirmed to be valid decimal degrees (longitude ≈ −117, latitude ≈ 32–33).
#

# %% [markdown]
# ## 8. Descriptive Statistics
#
# This section first runs the indicator pipeline (8.0) so the notebook is fully
# reproducible top to bottom, then summarizes the geocoded business-point dataset (8.1).
# The tract-level descriptive statistics — ACS employment, LODES workplace jobs,
# spatial autocorrelation context — are in Canyu's component notebook.
#

# %% [markdown]
# ### 8.0 — Generate Indicator Outputs (self-contained pipeline)
#
# The cells below run Joseph's full business-point indicator pipeline so this report
# notebook is **self-contained and runs top to bottom**. They produce
# `joseph_indicators_output.geojson`, which the descriptive-statistics cells in 8.1
# then read.
#
# **Required input files in this directory:**
# - `industrial_businesses_core_geocoded.csv` (from Christian's geocoding)
# - `Community_Plan_SD.geojson` (City of San Diego planning districts)
#
# *(If you only want the written summary and already have the GeoJSON, you can skip
# to 8.1.)*
#

# %%
import requests
import geopandas as gpd
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
from shapely.geometry import Point, box
from io import BytesIO
from pathlib import Path
import warnings
warnings.filterwarnings("ignore")

# ── CRS — matches Christian's pipeline exactly ────────────────────────────────
CRS_GEO  = "EPSG:4326"    # geographic lat/lon
CRS_PROJ = "EPSG:3310"    # California Albers (meters)

METERS_PER_MILE = 1609.34

# ── Buffer distances in meters (0.25 / 0.50 / 1.00 mi) ───────────────────────
BUFFER_DISTANCES_M = {
    "buffer_quarter_mi": 402,
    "buffer_half_mi":    805,
    "buffer_one_mi":     1609,
}

# ── Input files ───────────────────────────────────────────────────────────────
INPUT_CSV           = "industrial_businesses_core_geocoded.csv"
COMMUNITY_PLAN_FILE = "Community_Plan_SD.geojson"

# ── Study area mapping: CPNAME -> study area label ────────────────────────────
# Otay Mesa     = OTAY MESA + OTAY MESA-NESTOR  (matches Christian str.contains)
# Kearny Mesa   = KEARNY MESA
# Miramar       = MIRAMAR RANCH NORTH + SCRIPPS MIRAMAR RANCH
# Sorrento Valley = MIRA MESA (no official Sorrento Valley planning district)
STUDY_AREA_MAP = {
    "OTAY MESA":             "Otay Mesa",
    "OTAY MESA-NESTOR":      "Otay Mesa",
    "KEARNY MESA":           "Kearny Mesa",
    "MIRAMAR RANCH NORTH":   "Miramar",
    "SCRIPPS MIRAMAR RANCH": "Miramar",
    "MIRA MESA":             "Sorrento Valley",
}
STUDY_AREAS      = ["Otay Mesa", "Kearny Mesa", "Miramar", "Sorrento Valley"]
BORDER_AREA      = "Otay Mesa"
COMPARISON_AREAS = ["Kearny Mesa", "Miramar", "Sorrento Valley"]

AREA_COLORS = {
    "Otay Mesa":       "#e8522a",
    "Kearny Mesa":     "#2c7bb6",
    "Miramar":         "#1a9641",
    "Sorrento Valley": "#7b3294",
    "Other":           "#d9d9d9",
}

# ── LODES configuration ───────────────────────────────────────────────────────
LODES_YEAR     = 2021      # latest available CA year; check lehd.ces.census.gov
LODES_STATE    = "ca"
LODES_JOB_TYPE = "JT00"   # all jobs
LODES_SEGMENT  = "S000"   # all workers
SD_COUNTY_FIPS = "073"

# LODES WAC NAICS sector columns
LODES_NAICS_COLS = {
    "CNS05": "lodes_mfg_jobs",    # Manufacturing (NAICS 31-33)
    "CNS06": "lodes_whole_jobs",   # Wholesale Trade (NAICS 42)
    "CNS08": "lodes_trans_jobs",   # Transportation & Warehousing (NAICS 48-49)
}

# ── Census TIGER tracts URL ───────────────────────────────────────────────────
TRACT_URL = (
    "https://www2.census.gov/geo/tiger/GENZ2023/shp/"
    "cb_2023_06_tract_500k.zip"
)

# ── SANDAG URLs ───────────────────────────────────────────────────────────────
SANDAG_POE_URL   = "https://gis.sandag.org/FreightViewer/data/poe_points_update.json"
SANDAG_ROADS_URL = "https://gis.sandag.org/FreightViewer/data/MajorRoads_20171002.json"

# ── Buffer cols/labels for charts ────────────────────────────────────────────
buf_cols   = list(BUFFER_DISTANCES_M.keys())
buf_labels = ["0.25 mi", "0.50 mi", "1.00 mi"]

print("Setup complete.")
print(f"  CRS:    {CRS_PROJ}")
print(f"  Buffers (m): {BUFFER_DISTANCES_M}")
print(f"  LODES year:  {LODES_YEAR}")


# %%
# ── Load Christian's geocoded CSV ─────────────────────────────────────────────
df = pd.read_csv(INPUT_CSV, dtype=str)
print(f"Loaded {len(df)} rows | Columns: {df.columns.tolist()}")

df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
df["latitude"]  = pd.to_numeric(df["latitude"],  errors="coerce")
df = df.dropna(subset=["longitude", "latitude"]).reset_index(drop=True)
print(f"Valid coordinates: {len(df)}")

businesses = gpd.GeoDataFrame(
    df,
    geometry=gpd.points_from_xy(df["longitude"], df["latitude"]),
    crs=CRS_GEO
).to_crs(CRS_PROJ)

print(f"GeoDataFrame CRS: {businesses.crs}")

# ── Load Community Planning Districts ─────────────────────────────────────────
planning = gpd.read_file(COMMUNITY_PLAN_FILE)
if planning.crs is None:
    planning = planning.set_crs(CRS_GEO)
planning = planning.to_crs(CRS_PROJ)
print(f"Planning districts: {len(planning)} features")

# ── Clip to SD city planning boundary ────────────────────────────────────────
sd_boundary = planning.geometry.unary_union
sd_county   = gpd.GeoDataFrame(geometry=[sd_boundary], crs=CRS_PROJ)
before = len(businesses)
businesses = businesses[businesses.geometry.within(sd_boundary)].copy().reset_index(drop=True)
print(f"Clipped: {before} -> {len(businesses)} businesses within SD planning areas")

# ── Spatial join: assign planning area ───────────────────────────────────────
businesses = gpd.sjoin(
    businesses,
    planning[["CPNAME", "geometry"]],
    how="left", predicate="within"
).drop(columns=["index_right"], errors="ignore")

businesses["CPNAME"]  = businesses["CPNAME"].fillna("Outside City Planning Areas")
businesses["subarea"] = businesses["CPNAME"].map(STUDY_AREA_MAP).fillna("Other")

print("\nSubarea counts:")
print(businesses["subarea"].value_counts())

# ── Build per-subarea GeoDataFrames ──────────────────────────────────────────
subarea_gdfs = {area: businesses[businesses["subarea"] == area] for area in STUDY_AREAS}
subarea_gdfs["Other"] = businesses[businesses["subarea"] == "Other"]
otay   = subarea_gdfs["Otay Mesa"]
nonbdr = businesses[businesses["subarea"] != "Otay Mesa"]
print(f"\nOtay Mesa: {len(otay)} | Non-border total: {len(nonbdr)}")


# %%
# ── Download LODES WAC file for California ────────────────────────────────────
LODES_URL = (
    f"https://lehd.ces.census.gov/data/lodes/LODES8/{LODES_STATE}/wac/"
    f"{LODES_STATE}_wac_{LODES_SEGMENT}_{LODES_JOB_TYPE}_{LODES_YEAR}.csv.gz"
)
print(f"Downloading LODES WAC:\n  {LODES_URL}")
print("(~30-60 seconds — CA WAC file is ~50MB compressed)")

wac = pd.read_csv(LODES_URL, compression="gzip", dtype={"w_geocode": str})
print(f"Loaded: {len(wac):,} CA census blocks")

# ── Build tract GEOID and filter to San Diego County ─────────────────────────
# w_geocode = 15-digit block FIPS: state(2)+county(3)+tract(6)+block(4)
wac["GEOID"]    = wac["w_geocode"].str[:11]
wac["COUNTYFP"] = wac["w_geocode"].str[2:5]
wac_sd = wac[wac["COUNTYFP"] == SD_COUNTY_FIPS].copy()
print(f"San Diego County blocks: {len(wac_sd):,} | Unique tracts: {wac_sd['GEOID'].nunique()}")

# ── Verify NAICS columns ──────────────────────────────────────────────────────
missing = [c for c in LODES_NAICS_COLS if c not in wac_sd.columns]
if missing:
    print(f"WARNING: missing columns {missing}")
    print("Available CNS cols:", [c for c in wac_sd.columns if c.startswith("CNS")])
else:
    print("All expected NAICS columns present.")

# ── Aggregate blocks -> tracts ────────────────────────────────────────────────
agg_cols = list(LODES_NAICS_COLS.keys()) + ["C000"]
tract_lodes = (
    wac_sd.groupby("GEOID")[agg_cols]
    .sum().reset_index()
    .rename(columns={**LODES_NAICS_COLS, "C000": "lodes_total_jobs"})
)

ind_cols = list(LODES_NAICS_COLS.values())
tract_lodes["lodes_industrial_jobs"]  = tract_lodes[ind_cols].sum(axis=1)
tract_lodes["lodes_industrial_share"] = (
    tract_lodes["lodes_industrial_jobs"] /
    tract_lodes["lodes_total_jobs"].replace(0, np.nan)
)

print(f"\nTract-level LODES: {len(tract_lodes):,} tracts")
print(tract_lodes[["lodes_mfg_jobs","lodes_whole_jobs","lodes_trans_jobs",
                    "lodes_industrial_jobs","lodes_industrial_share"]].describe().round(2))

# ── Merge onto TIGER tract geometries ────────────────────────────────────────
print("\nLoading Census TIGER 2023 tracts...")
tracts_ca = gpd.read_file(TRACT_URL)
tracts_sd = tracts_ca[tracts_ca["COUNTYFP"] == SD_COUNTY_FIPS].copy()
tracts_sd["GEOID"] = tracts_sd["GEOID"].astype(str)
tracts_merged = tracts_sd[["GEOID"]].merge(tract_lodes, on="GEOID", how="left")
tracts_merged[ind_cols + ["lodes_industrial_jobs","lodes_industrial_share","lodes_total_jobs"]] = (
    tracts_merged[ind_cols + ["lodes_industrial_jobs","lodes_industrial_share","lodes_total_jobs"]]
    .fillna(0)
)

# ── Export for Canyu's Hook A ────────────────────────────────────────────────
lodes_out_cols = ["GEOID","lodes_mfg_jobs","lodes_whole_jobs","lodes_trans_jobs",
                  "lodes_industrial_jobs","lodes_industrial_share","lodes_total_jobs"]
tracts_merged[lodes_out_cols].to_csv("lodes_enrichment_by_tract.csv", index=False)
print("\nSaved: lodes_enrichment_by_tract.csv")
print(f"  {len(tracts_merged):,} rows | {len(lodes_out_cols)} columns")
print("\nTop 5 tracts by industrial jobs:")
print(
    tracts_merged.nlargest(5, "lodes_industrial_jobs")
    [["GEOID","lodes_industrial_jobs","lodes_industrial_share"]]
    .to_string(index=False)
)


# %%
# ── Fetch SANDAG POE points ───────────────────────────────────────────────────
print("Fetching SANDAG POE points...")
try:
    poe_pts = gpd.read_file(
        BytesIO(requests.get(SANDAG_POE_URL, timeout=60).content)
    ).to_crs(CRS_PROJ)
    print(f"POE points: {len(poe_pts)} features")
except Exception as e:
    print(f"[fallback] {e}")
    poe_pts = gpd.GeoDataFrame(
        {"port_name": ["San Ysidro POE", "Otay Mesa POE"]},
        geometry=[Point(-117.0295, 32.5440), Point(-116.9447, 32.5726)],
        crs=CRS_GEO
    ).to_crs(CRS_PROJ)
    print("Using hardcoded POE fallback.")

poe_name_col = next(
    (c for c in poe_pts.columns if "name" in c.lower() or "port" in c.lower()), None
)

if poe_name_col:
    poe_pts[poe_name_col] = poe_pts[poe_name_col].astype(str)
    sy_geom = poe_pts[poe_pts[poe_name_col].str.contains(
        "Ysidro|ysidro", na=False, case=False)].geometry.unary_union
    om_geom = poe_pts[poe_pts[poe_name_col].str.contains(
        "Otay|otay", na=False, case=False)].geometry.unary_union
else:
    sy_geom, om_geom = None, None

if sy_geom is None:
    sy_geom = gpd.GeoDataFrame(
        geometry=[Point(-117.0295, 32.5440)], crs=CRS_GEO
    ).to_crs(CRS_PROJ).geometry.iloc[0]

if om_geom is None:
    om_geom = gpd.GeoDataFrame(
        geometry=[Point(-116.9447, 32.5726)], crs=CRS_GEO
    ).to_crs(CRS_PROJ).geometry.iloc[0]

poe_union = poe_pts.geometry.unary_union

# ── Compute distances ─────────────────────────────────────────────────────────
businesses["dist_nearest_poe_m"]  = businesses.geometry.distance(poe_union)
businesses["dist_nearest_poe_mi"] = businesses["dist_nearest_poe_m"] / METERS_PER_MILE
businesses["dist_san_ysidro_m"]   = businesses.geometry.distance(sy_geom)
businesses["dist_san_ysidro_mi"]  = businesses["dist_san_ysidro_m"] / METERS_PER_MILE
businesses["dist_otay_poe_m"]     = businesses.geometry.distance(om_geom)
businesses["dist_otay_poe_mi"]    = businesses["dist_otay_poe_m"] / METERS_PER_MILE
businesses["nearest_poe_name"]    = np.where(
    businesses["dist_san_ysidro_m"] <= businesses["dist_otay_poe_m"],
    "San Ysidro", "Otay Mesa"
)

# ── POE hardcoded fallback for maps ──────────────────────────────────────────
poe_raw = gpd.GeoDataFrame(
    {"name": ["San Ysidro POE", "Otay Mesa POE"]},
    geometry=[Point(-117.0295, 32.5440), Point(-116.9447, 32.5726)],
    crs=CRS_GEO
).to_crs(CRS_PROJ)

print("\n── Distance to Nearest POE (miles) by Subarea ──")
print(
    businesses.groupby("subarea")["dist_nearest_poe_mi"]
    .agg(n="count", mean="mean", median="median", std="std", min="min", max="max")
    .round(3)
)


# %%
# ── Fetch SANDAG major roads ──────────────────────────────────────────────────
print("Fetching SANDAG Major Roads...")
major_roads = gpd.read_file(
    BytesIO(requests.get(SANDAG_ROADS_URL, timeout=60).content)
).to_crs(CRS_PROJ)
print(f"Major roads: {len(major_roads)} features | CRS: {major_roads.crs}")

roads_dissolved = major_roads.dissolve().geometry.iloc[0]

# ── sjoin_nearest — matches Christian's method exactly ───────────────────────
nearest_road = gpd.sjoin_nearest(
    businesses,
    major_roads[["geometry"]],
    how="left",
    distance_col="dist_to_freight_road_m"
).drop(columns=["index_right"], errors="ignore")

businesses["dist_to_freight_road_m"]  = nearest_road["dist_to_freight_road_m"]
businesses["dist_to_freight_road_mi"] = businesses["dist_to_freight_road_m"] / METERS_PER_MILE

businesses["distance_category"] = pd.cut(
    businesses["dist_to_freight_road_mi"],
    bins=[0, 0.25, 0.5, 1, 2, businesses["dist_to_freight_road_mi"].max()],
    labels=["0-0.25 mi","0.25-0.5 mi","0.5-1 mi","1-2 mi","2+ mi"],
    include_lowest=True
)

print("\n── Distance to Freight Road (miles) by Subarea ──")
print(
    businesses.groupby("subarea")["dist_to_freight_road_mi"]
    .agg(n="count", mean="mean", median="median", min="min", max="max")
    .round(3)
)


# %%
# Binary inside/outside flag for each buffer distance
for col, dist_m in BUFFER_DISTANCES_M.items():
    buf = roads_dissolved.buffer(dist_m)
    businesses[col] = businesses.geometry.within(buf)
    n_in  = int(businesses[col].sum())
    total = len(businesses)
    print(f"  {dist_m}m ({dist_m/METERS_PER_MILE:.2f} mi): "
          f"{n_in}/{total} inside ({100*n_in/total:.1f}%)")

print("\n── Buffer overlap by subarea ──")
for col, label in zip(buf_cols, buf_labels):
    print(f"\n{label}:")
    print(
        businesses.groupby("subarea")[col]
        .agg(n="count", n_inside="sum",
             pct_inside=lambda x: round(100*x.mean(), 1))
    )

# Update subarea_gdfs with new columns
subarea_gdfs = {area: businesses[businesses["subarea"] == area] for area in STUDY_AREAS}
subarea_gdfs["Other"] = businesses[businesses["subarea"] == "Other"]
otay   = subarea_gdfs["Otay Mesa"]
nonbdr = businesses[businesses["subarea"] != "Otay Mesa"]


# %%
base_cols = [
    "business_acctnum","dba_name","industry_group","naics",
    "address","city","state","zip","latitude","longitude",
    "CPNAME","subarea",
    "dist_nearest_poe_m","dist_nearest_poe_mi",
    "dist_san_ysidro_m","dist_san_ysidro_mi",
    "dist_otay_poe_m","dist_otay_poe_mi",
    "nearest_poe_name",
    "dist_to_freight_road_m","dist_to_freight_road_mi",
    "distance_category",
]
keep = [c for c in base_cols + buf_cols if c in businesses.columns]
output_gdf = businesses[keep + ["geometry"]].copy()

output_gdf.drop(columns=["geometry"]).to_csv("joseph_indicators_output.csv", index=False)
output_gdf.to_crs(CRS_GEO).to_file("joseph_indicators_output.geojson", driver="GeoJSON")

print("Saved: joseph_indicators_output.csv")
print("Saved: joseph_indicators_output.geojson")
print(f"  {len(output_gdf):,} rows | {len(keep)} columns")

print("\n── FINAL VALIDATION SUMMARY ──")
print(
    businesses[["subarea","dist_nearest_poe_mi"] + buf_cols]
    .groupby("subarea").agg(["mean","count"]).round(3)
)


# %% [markdown]
# ### 8.1 — Descriptive Summary of Business Points

# %%
# ── Load Joseph's exported indicator output ──────────────────────────────────
# Run Code_Joseph.ipynb first to produce joseph_indicators_output.geojson

# Use in-memory result from 8.0 if present, else read the exported file
try:
    gdf = output_gdf.to_crs("EPSG:4326").copy()
    print("Using in-memory pipeline output from section 8.0")
except NameError:
    gdf = gpd.read_file("joseph_indicators_output.geojson")
    print("Loaded joseph_indicators_output.geojson from disk")
print(f"Business points loaded: {len(gdf)}")
print(f"Columns: {gdf.columns.tolist()}")
print()

STUDY_AREAS = ["Otay Mesa", "Kearny Mesa", "Miramar", "Sorrento Valley"]
buf_cols    = ["buffer_quarter_mi", "buffer_half_mi", "buffer_one_mi"]

print("=== Business count by subarea ===")
print(gdf["subarea"].value_counts())
print()

print("=== Industry group by subarea ===")
print(gdf.groupby(["subarea","industry_group"]).size().unstack(fill_value=0))
print()

print("=== Distance to nearest POE (miles) by subarea ===")
print(
    gdf.groupby("subarea")["dist_nearest_poe_mi"]
    .agg(n="count", mean="mean", median="median", std="std", min="min", max="max")
    .round(3)
)


# %%
# ── Buffer overlap summary ────────────────────────────────────────────────────
print("=== Freight corridor buffer overlap (% inside) by subarea ===")
for col in buf_cols:
    print(f"\n{col}:")
    print(
        gdf.groupby("subarea")[col]
        .agg(n="count", n_inside="sum",
             pct_inside=lambda x: round(100*x.mean(), 1))
    )


# %%
# ── POE distance histogram by study area ─────────────────────────────────────
AREA_COLORS = {
    "Otay Mesa":"#e8522a","Kearny Mesa":"#2c7bb6",
    "Miramar":"#1a9641","Sorrento Valley":"#7b3294"
}
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
axes = axes.flatten()
for i, area in enumerate(STUDY_AREAS):
    sub = gdf[gdf["subarea"] == area]["dist_nearest_poe_mi"].clip(upper=40)
    axes[i].hist(sub, bins=30, color=AREA_COLORS[area], alpha=0.8, edgecolor="white")
    axes[i].axvline(sub.median(), color="black", linestyle="--", linewidth=1.5,
                    label=f"Median: {sub.median():.2f} mi")
    axes[i].set_title(f"{area} (n={len(sub):,})", fontweight="bold")
    axes[i].set_xlabel("Distance to nearest POE (miles)")
    axes[i].set_ylabel("Count")
    axes[i].legend(fontsize=9)
    axes[i].spines[["top","right"]].set_visible(False)
fig.suptitle("Distribution of Distance to Nearest POE by Study Area",
             fontsize=13, fontweight="bold")
plt.tight_layout()
plt.show()


# %% [markdown]
# ## 9. Analysis
#
# ### Workflow
#
# ```
#                   ┌─────────────────────────────────────────────┐
#                   │  Census ACS + LODES + TIGER + SANDAG + GADM  │
#                   └─────────────────────────────────────────────┘
#                                      │
#          ┌───────────────────────────┼───────────────────────────┐
#          ▼                           ▼                           ▼
#  [Christian — geocoding]    [Canyu — tracts]          [Joseph — business pts]
#   raw license CSVs           ACS employment            POE distance
#   NAICS classification       LODES workplace jobs      freight buffers
#   ArcGIS batch geocode       zoning/land-use overlay   Mann-Whitney + Chi-sq
#   county + planning join     proximity indicators      maps + charts
#   dist-to-freight-road       per-area comparison
#          │                           │                           │
#          └───────────────────────────┴───────────────────────────┘
#                                      ▼
#                           Combined StoryMap + Report
# ```
#
# ### Step 1 — Geocoding & business preparation (Christian)
# Raw business-license records are concatenated, NAICS-classified into Manufacturing / Wholesale / Transportation & Warehousing / Industrial Machinery Repair, and split into Broad and Core industrial definitions. Addresses are geocoded with ArcGIS `batch_geocode`, filtered to matched results inside San Diego County, and assigned a planning area. Christian also computes a **distance-to-nearest-freight-road** indicator (`gpd.sjoin_nearest`) with distance-category bins and Otay-Mesa-vs-other summaries. Output: `industrial_businesses_core_geocoded.csv` — the shared input for Joseph's indicators.
#
# ### Step 2 — Tract-level analysis (Canyu)
# ACS employment (context) + LODES workplace jobs (primary activity measure) joined to tracts; proximity indicators (`dist_poe_mi`, `dist_road_mi`, corridor area-share); zoning and general-plan land-use overlays; per-area comparison and county-wide association. CRS: EPSG:2230 (US survey feet).
#
# ### Step 3 — Business-point indicators & statistics (Joseph)
# Subarea assignment via Community Plan districts; Indicator 1 (POE distance), Indicator 1b (road distance via `sjoin_nearest`), Indicator 2 (0.25/0.50/1.00-mile buffer flags); pairwise Mann-Whitney U + Chi-square with 95% bootstrap CIs; maps and charts. CRS: EPSG:3310 (California Albers, meters).
#
# ### Christian's geocoding & distance code (reference)
# The cell below contains Christian's full pipeline. It requires ArcGIS Online credentials and the raw CSVs (`tr_active1.csv`, `tr_active2.csv`), so it is included for reproducibility rather than re-run inside this report notebook.
#
# ### Evolution from Proposal
# Industrial zone polygons → business points + tracts. ESRI GeoEnrichment → Census LODES. Statistical significance testing added.
#

# %%
import pandas as pd
import geopandas as gpd
from pathlib import Path
from arcgis.gis import GIS
from arcgis.geocoding import batch_geocode

# ============================================================
# 0. Settings
# ============================================================
TARGET_CRS = "EPSG:3310"  # California Albers
FT_PER_MILE = 5280
METERS_PER_MILE = 1609.34

TRACT_URL = "https://www2.census.gov/geo/tiger/GENZ2023/shp/cb_2023_06_tract_500k.zip"
MAJOR_ROADS_URL = "https://gis.sandag.org/FreightViewer/data/MajorRoads_20171002.json"
GADM_FILE = "gadm41_USA_2.json"

# Change this to match your uploaded planning district file name
PLANNING_AREAS_FILE = "Community_Plan_SD.geojson"

def inspect_gdf(gdf, name):
    print(f"\n{name}")
    print("Rows:", len(gdf))
    print("CRS:", gdf.crs)
    print("Columns:", gdf.columns.tolist())
    print(gdf.head())

# ============================================================
# 1. Connect to ArcGIS Online
# ============================================================
gis = GIS(username="gpec447sp26_23")

# ============================================================
# 2. Load and clean business data
# ============================================================
files = [
    Path("tr_active1.csv"),
    Path("tr_active2.csv")
]

businesses = pd.concat(
    [pd.read_csv(f, dtype=str, engine="python", on_bad_lines="skip") for f in files],
    ignore_index=True
)

businesses.columns = (
    businesses.columns
    .str.strip()
    .str.lower()
    .str.replace(" ", "_")
    .str.replace("#", "num")
)

businesses["naics"] = (
    businesses["naics"]
    .astype(str)
    .str.strip()
    .str.replace(".0", "", regex=False)
)

# ============================================================
# 3. Define NAICS classification
# ============================================================
def classify_industry(naics):
    naics = str(naics).strip()

    if naics.startswith(("31", "32", "33")):
        return "Manufacturing"
    elif naics.startswith("42"):
        return "Wholesale Trade"
    elif naics.startswith(("48", "49")):
        return "Transportation and Warehousing"
    elif naics.startswith("8113"):
        return "Industrial Machinery Repair"
    else:
        return "Other"

broad_prefixes = (
    "31", "32", "33",
    "42",
    "48", "49",
    "8113"
)

core_keep_prefixes = (
    "31", "32", "33",
    "421", "422", "423", "424",
    "481", "483", "484", "488", "491", "492", "493",
    "8113"
)

core_exclude_prefixes = (
    "425",
    "485",
    "486",
    "487"
)

# ============================================================
# 4. Create broad and core datasets
# ============================================================
industrial_broad = businesses[
    businesses["naics"].str.startswith(broad_prefixes, na=False)
].copy()

industrial_broad["definition"] = "Broad"
industrial_broad["industry_group"] = industrial_broad["naics"].apply(classify_industry)

industrial_core = industrial_broad[
    industrial_broad["naics"].str.startswith(core_keep_prefixes, na=False)
    & ~industrial_broad["naics"].str.startswith(core_exclude_prefixes, na=False)
].copy()

industrial_core["definition"] = "Core"
industrial_core["industry_group"] = industrial_core["naics"].apply(classify_industry)

print("Broad businesses:", len(industrial_broad))
print(industrial_broad["industry_group"].value_counts())

print("\nCore businesses:", len(industrial_core))
print(industrial_core["industry_group"].value_counts())

# ============================================================
# 5. Load San Diego County census tracts
# ============================================================
tracts_ca = gpd.read_file(TRACT_URL)

tracts_sd = (
    tracts_ca[tracts_ca["COUNTYFP"] == "073"]
    .copy()
    .to_crs(TARGET_CRS)
)

tracts_sd["GEOID"] = tracts_sd["GEOID"].astype(str)
tracts_sd["area_sqmi"] = tracts_sd.geometry.area / (METERS_PER_MILE ** 2)

inspect_gdf(tracts_sd, "San Diego County census tracts")

# ============================================================
# 6. Load GADM San Diego County boundary
# ============================================================
counties = gpd.read_file(GADM_FILE)

sd_county = counties[
    (counties["NAME_1"] == "California")
    & (counties["NAME_2"] == "SanDiego")
].copy()

sd_county = sd_county.to_crs(TARGET_CRS)

inspect_gdf(sd_county, "GADM San Diego County boundary")

sd_county.to_file("san_diego_county_gadm.geojson", driver="GeoJSON")

# ============================================================
# 7. Load Community Planning District Boundaries
# ============================================================
planning_areas = gpd.read_file(PLANNING_AREAS_FILE)

if planning_areas.crs is None:
    planning_areas = planning_areas.set_crs("EPSG:4326")

planning_areas = planning_areas.to_crs(TARGET_CRS)

inspect_gdf(planning_areas, "Community Planning District Boundaries")

# ============================================================
# Planning area name field
# ============================================================

planning_areas = planning_areas.rename(
    columns={"CPNAME": "planning_area"}
)

print(
    planning_areas["planning_area"]
    .sort_values()
    .unique()
)

# ============================================================
# 8. Function: geocode, county-filter, assign planning area
# ============================================================
def geocode_filter_export(df, output_file):
    df = df.copy()

    df["full_address"] = (
        df["address"].fillna("") + ", " +
        df["city"].fillna("") + ", " +
        df["state"].fillna("") + " " +
        df["zip"].fillna("")
    )

    df = df[df["full_address"].str.len() > 10].copy()
    df = df.reset_index(drop=True)

    geocoded_results = batch_geocode(
        df["full_address"].tolist(),
        as_featureset=True
    )

    geo_sdf = geocoded_results.sdf.reset_index(drop=True)

    df["longitude"] = pd.to_numeric(geo_sdf["X"], errors="coerce")
    df["latitude"] = pd.to_numeric(geo_sdf["Y"], errors="coerce")
    df["geocode_score"] = geo_sdf["Score"]
    df["matched_address"] = geo_sdf["Match_addr"]
    df["geocode_status"] = geo_sdf["Status"]

    df = df[
        (df["geocode_status"] == "M")
        & df["longitude"].notna()
        & df["latitude"].notna()
    ].copy()

    print(f"\nSuccessfully geocoded before county filter: {len(df)}")

    businesses_gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df["longitude"], df["latitude"]),
        crs="EPSG:4326"
    ).to_crs(TARGET_CRS)

    # Keep only businesses inside San Diego County census tracts
    businesses_gdf = gpd.sjoin(
        businesses_gdf,
        tracts_sd[["GEOID", "geometry"]],
        how="inner",
        predicate="within"
    )

    if "index_right" in businesses_gdf.columns:
        businesses_gdf = businesses_gdf.drop(columns=["index_right"])

    businesses_gdf = businesses_gdf.rename(columns={"GEOID": "tract_geoid"})

    print("Businesses inside San Diego County census tracts:", len(businesses_gdf))

    # Assign planning area
    businesses_gdf = gpd.sjoin(
        businesses_gdf,
        planning_areas[["planning_area", "geometry"]],
        how="left",
        predicate="within"
    )

    if "index_right" in businesses_gdf.columns:
        businesses_gdf = businesses_gdf.drop(columns=["index_right"])

    businesses_gdf["planning_area"] = businesses_gdf["planning_area"].fillna("Outside City Planning Areas")

    # Convert back to WGS84 for CSV/ArcGIS upload
    businesses_gdf = businesses_gdf.to_crs("EPSG:4326")

    df = pd.DataFrame(businesses_gdf.drop(columns="geometry"))

    print(df["planning_area"].value_counts().head(20))

    output_cols = [
        "business_acctnum",
        "dba_name",
        "ownership_type",
        "address",
        "city",
        "state",
        "zip",
        "naics",
        "activity_desc",
        "industry_group",
        "definition",
        "tract_geoid",
        "planning_area",
        "full_address",
        "matched_address",
        "geocode_score",
        "longitude",
        "latitude"
    ]

    df = df[output_cols].copy()
    df.to_csv(output_file, index=False)

    print(f"\nExported: {output_file}")
    print("Final row count:", len(df))
    print(df["industry_group"].value_counts())

    return df

# ============================================================
# 9. Geocode, filter, and export both datasets
# ============================================================
core_points = geocode_filter_export(
    industrial_core,
    "industrial_businesses_core_geocoded.csv"
)

broad_points = geocode_filter_export(
    industrial_broad,
    "industrial_businesses_broad_geocoded.csv"
)

# ============================================================
# 10. Load SANDAG major freight roads
# ============================================================
roads_gdf = gpd.read_file(MAJOR_ROADS_URL)

if roads_gdf.crs is None:
    roads_gdf = roads_gdf.set_crs("EPSG:4326")

roads_proj = roads_gdf.to_crs(TARGET_CRS)

inspect_gdf(roads_proj, "SANDAG major freight roads")

# ============================================================
# 11. Function: distance to nearest freight road + comparisons
# ============================================================
def distance_to_freight_roads(input_csv, output_csv, definition_label):
    businesses = pd.read_csv(input_csv)

    business_gdf = gpd.GeoDataFrame(
        businesses,
        geometry=gpd.points_from_xy(
            businesses["longitude"],
            businesses["latitude"]
        ),
        crs="EPSG:4326"
    ).to_crs(TARGET_CRS)

    nearest = gpd.sjoin_nearest(
        business_gdf,
        roads_proj,
        how="left",
        distance_col="dist_to_freight_road_m"
    )

    nearest["dist_to_freight_road_mi"] = (
        nearest["dist_to_freight_road_m"] / METERS_PER_MILE
    )

    nearest["distance_category"] = pd.cut(
        nearest["dist_to_freight_road_mi"],
        bins=[0, 0.25, 0.5, 1, 2, nearest["dist_to_freight_road_mi"].max()],
        labels=["0–0.25 mi", "0.25–0.5 mi", "0.5–1 mi", "1–2 mi", "2+ mi"],
        include_lowest=True
    )

    nearest["is_otay_mesa"] = nearest["planning_area"].str.contains(
        "Otay Mesa",
        case=False,
        na=False
    )

    nearest["comparison_area"] = nearest["is_otay_mesa"].map({
        True: "Otay Mesa",
        False: "Other San Diego Areas"
    })

    # Export full results
    nearest.to_csv(output_csv, index=False)

    nearest.to_crs("EPSG:4326").to_file(
        output_csv.replace(".csv", ".geojson"),
        driver="GeoJSON"
    )

    # Overall summary
    overall_summary = pd.DataFrame({
        "definition": [definition_label],
        "total_businesses": [len(nearest)],
        "mean_distance_mi": [nearest["dist_to_freight_road_mi"].mean()],
        "median_distance_mi": [nearest["dist_to_freight_road_mi"].median()],
        "min_distance_mi": [nearest["dist_to_freight_road_mi"].min()],
        "max_distance_mi": [nearest["dist_to_freight_road_mi"].max()]
    })

    overall_summary.to_csv(
        output_csv.replace(".csv", "_overall_summary.csv"),
        index=False
    )

    # By industry
    industry_summary = (
        nearest.groupby("industry_group")["dist_to_freight_road_mi"]
        .agg(["count", "mean", "median", "min", "max"])
        .reset_index()
    )

    industry_summary.to_csv(
        output_csv.replace(".csv", "_summary_by_industry.csv"),
        index=False
    )

    # By planning area
    planning_summary = (
        nearest.groupby("planning_area")["dist_to_freight_road_mi"]
        .agg(["count", "mean", "median", "min", "max"])
        .reset_index()
        .sort_values("mean")
    )

    planning_summary.to_csv(
        output_csv.replace(".csv", "_summary_by_planning_area.csv"),
        index=False
    )

    # Otay Mesa vs other areas
    otay_summary = (
        nearest.groupby("comparison_area")["dist_to_freight_road_mi"]
        .agg(["count", "mean", "median", "min", "max"])
        .reset_index()
    )

    otay_summary.to_csv(
        output_csv.replace(".csv", "_otay_vs_other_summary.csv"),
        index=False
    )

    print(f"\nExported: {output_csv}")
    print("\nOverall summary:")
    print(overall_summary)

    print("\nOtay Mesa vs Other San Diego Areas:")
    print(otay_summary)

    print("\nTop planning areas by business count:")
    print(
        planning_summary.sort_values("count", ascending=False).head(10)
    )

    return nearest, overall_summary, industry_summary, planning_summary, otay_summary

# ============================================================
# 12. Run distance analysis
# ============================================================
core_nearest, core_overall, core_industry, core_planning, core_otay = distance_to_freight_roads(
    "industrial_businesses_core_geocoded.csv",
    "industrial_businesses_core_distance_to_freight_roads.csv",
    "Core"
)

broad_nearest, broad_overall, broad_industry, broad_planning, broad_otay = distance_to_freight_roads(
    "industrial_businesses_broad_geocoded.csv",
    "industrial_businesses_broad_distance_to_freight_roads.csv",
    "Broad"
)


# %%
# ── Analysis parameters (Joseph's component) ─────────────────────────────────
CRS_PROJ        = "EPSG:3310"    # California Albers (meters)
METERS_PER_MILE = 1609.34
BUFFER_M        = {"buffer_quarter_mi":402, "buffer_half_mi":805, "buffer_one_mi":1609}

STUDY_AREA_MAP = {
    "OTAY MESA":             "Otay Mesa",
    "OTAY MESA-NESTOR":      "Otay Mesa",
    "KEARNY MESA":           "Kearny Mesa",
    "MIRAMAR RANCH NORTH":   "Miramar",
    "SCRIPPS MIRAMAR RANCH": "Miramar",
    "MIRA MESA":             "Sorrento Valley",
}

print("Analysis parameters:")
print(f"  CRS: {CRS_PROJ}")
print(f"  Buffer distances (m): {BUFFER_M}")
print("\nFull analysis: run Code_Joseph.ipynb and Code_canyu_June_7th.ipynb")


# %% [markdown]
# ## 10. Summary of Results
#
# ### Key Findings
#
# **Indicator 1 — Distance to Nearest POE (business points, Joseph)**
#
# | Subarea | n | Median (mi) |
# |---------|---|-------------|
# | Otay Mesa | 493 | 1.09 |
# | Kearny Mesa | 206 | 20.75 |
# | Miramar | 52 | 25.99 |
# | Sorrento Valley | 369 | 24.99 |
#
# Otay Mesa businesses are **19–24× closer** to a port of entry than businesses in the comparison areas.
#
# **Indicator 2 — Freight Corridor Buffer Overlap**
#
# | Buffer | Otay Mesa | Kearny Mesa | Miramar | Sorrento Valley |
# |--------|-----------|-------------|---------|-----------------|
# | 0.25 mi | 40.6% | 41.3% | 25.0% | 3.3% |
# | 0.50 mi | 81.7% | 90.3% | 48.1% | 7.3% |
# | 1.00 mi | 98.6% | 100.0% | 65.4% | 17.6% |
#
# **Core finding:** POE proximity is the dominant spatial signal distinguishing Otay Mesa. Freight-road corridor proximity does **not** uniquely distinguish Otay Mesa — Kearny Mesa matches or exceeds it at every buffer distance — which confirms that not every freight indicator separates the border zone. It is specifically *port* proximity, not general road access, that marks Otay Mesa as distinctive.
#
# *(Re-run the code cells in Section 8 / Code_Joseph.ipynb to regenerate these tables from current data.)*
#

# %% [markdown]
# ## 11. Discussion
#
# ### Findings in Context of Literature
# The strong POE-proximity clustering is consistent with border-zone industrial location research showing that freight-oriented businesses self-select for locations minimizing cross-border transport costs. The finding refines that literature: the border crossing itself — not road access generally — is the organizing principle. Kearny Mesa, an inland aerospace/defense cluster, sits as close to (or closer to) major freight roads than Otay Mesa, yet is ~20 miles from any POE. This shows freight-road proximity is necessary-but-not-distinctive, while POE proximity is the distinguishing feature.
#
# ### Trade-offs and Decision Points
#
# **Buffer distance:** The 0.25 / 0.50 / 1.00-mile thresholds are researcher-defined. Reporting three thresholds (rather than one) addresses the instructor's concern that findings should not depend on a single arbitrary distance.
#
# **CRS:** Joseph's component uses EPSG:3310 (meters) to match Christian's pipeline; Canyu's uses EPSG:2230 (US survey feet). Both are valid projected CRSs for San Diego; each reports final distances in miles. The **`area_sqmi` unit bug** flagged in Section 7 is a direct example of why the projection's native unit must be tracked carefully when computing area.
#
# **Activity measure:** LODES workplace jobs (where work occurs) replaced ESRI GeoEnrichment and is preferred over ACS residence-based employment for locating industrial activity.
#
# **Geocoding validity:** Geocode scores reflect address-matching confidence, not operational-location accuracy — the most significant unresolved concern (see Section 9c in Canyu's notebook).
#
# **Subarea definition:** Official Community Plan districts replace researcher-defined circles/boxes, grounding subareas in city geography. Sorrento Valley has no official district; MIRA MESA is the closest match.
#

# %% [markdown]
# ## 12. Conclusions & Future Work
#
# ### Did We Answer the Research Question?
# Yes, with caveats. The spatial association between Otay Mesa's industrial activity and port-of-entry proximity is statistically significant and extremely strong. Critically, the multi-area comparison shows the association is specific to *ports*, not freight roads in general — strengthening rather than weakening the conclusion. The analysis documents where businesses are *registered*; operational locations may differ.
#
# ### Future Work
#
# 1. **Border-logistics indicator businesses** — identify NAICS subcategories unique to Otay Mesa (customs brokers 541614, freight forwarders 488510, cold storage 493120) to build a "border-economy index."
# 2. **Operational location validation** — extend the address-validity worksheet (Canyu §9c) to a larger sample using company websites / satellite imagery.
# 3. **Sensitivity analysis** — test a wider range of buffer distances to confirm robustness.
# 4. **Tijuana-side analysis** — incorporate maquiladora zones across the border.
# 5. **Drive-time distance** — replace straight-line POE distance with network/drive-time distance and border wait times.
# 6. **Otay Mesa East POE** — model the expected industrial shift if the proposed crossing opens.
#
# ### Expected Use
# Most immediately relevant to SANDAG and City of San Diego planners considering land use near the proposed Otay Mesa East crossing. The framework extends to other US–Mexico crossings in California and Texas. Industry reviewer Connor Jennings (cc'd by the instructor) may suggest specific real-world application contexts.
#
# ---
# *Notebook prepared for GPEC 447, UC San Diego, Spring 2026.*
#
