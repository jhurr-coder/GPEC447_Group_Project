# GPEC 447 — Project Notebook Template

---

## 1. Project Title

<!-- Replace with your project title -->
**Industrial–Logistics Coupling in the Otay Mesa Border Zone: A Spatial Analysis of Freight Infrastructure and Industrial Activity in San Diego**

---

## 2. Team Members

| Name | Student ID |
|------|------------|
| Christian Phouasalith | gpec447sp26_23 |
| Joseph Hurr | gpec447sp26_11 |
| Canyu Li | <!-- add ID --> |

---

## 3. Research Question & Importance

> **250–300 words**

### Question
Is industrial activity in the Otay Mesa border area more strongly associated with ports of entry (POEs) and major freight corridors than industrial activity in comparable non-border industrial areas of San Diego?

### Intended Audience
Regional planners, economic development agencies (SANDAG, City of San Diego), cross-border logistics operators, and policymakers considering infrastructure investments around the Otay Mesa East proposed port of entry.

### Business Case
San Diego's Otay Mesa district sits at one of the busiest commercial border crossings in the world. Understanding whether industrial clustering there is genuinely organized around port access — rather than simply reflecting leftover land use patterns — has direct implications for:
- Land use planning decisions near the proposed Otay Mesa East POE
- Infrastructure investment prioritization for freight corridors
- Economic development strategies targeting cross-border logistics

### Evolution from Proposal
<!-- If your question changed, explain here. Otherwise: -->
The core question remained consistent with the project proposal. The primary methodological evolution was a shift from industrial zone polygons as the unit of analysis to census tracts (Canyu's component) and geocoded business license records (Joseph's and Christian's components), following feedback from Prof. Zaslavsky that industrial zoning in San Diego reflects historical land allocation rather than deliberate freight-access decisions.

---

## 4. Background & Literature

> **200–400 words**

### References

1. **SANDAG FreightViewer** — Interactive visualization of San Diego's freight network, ports of entry, and major roads.
   [https://gis.sandag.org/FreightViewer/](https://gis.sandag.org/FreightViewer/)
   *Informed our selection of freight infrastructure layers and POE point locations.*

2. **US Census Bureau — American Community Survey (ACS) 5-Year Estimates, 2022**
   [https://www.census.gov/programs-surveys/acs](https://www.census.gov/programs-surveys/acs)
   *Provided tract-level industry-of-employment counts (DP03 variables) used in the census-tract component of the analysis.*

3. **LEHD Origin-Destination Employment Statistics (LODES)**
   [https://lehd.ces.census.gov/data/](https://lehd.ces.census.gov/data/)
   *Alternative tract-level jobs data by 2-digit NAICS; identified as a future direction for distinguishing where workers are employed (vs. where they reside).*

4. **City of San Diego — Zoning and Parcel Information Portal (ZAPP)**
   [https://www.arcgis.com/apps/instant/sidebar/index.html?appid=75f6a5d68aee481f8ff48240bcaa1239](https://www.arcgis.com/apps/instant/sidebar/index.html?appid=75f6a5d68aee481f8ff48240bcaa1239)
   *Revealed that San Diego's industrial zoning reflects "leftover land" allocation rather than freight-access optimization — the key limitation that motivated our shift to business-license records as the primary unit of analysis.*

5. **GADM — Global Administrative Areas, USA Level 2**
   [https://gadm.org/](https://gadm.org/)
   *Used for San Diego County boundary definition in the geocoding and spatial filtering pipeline.*

6. **US Census TIGER/Line Cartographic Boundary Files, 2023**
   [https://www2.census.gov/geo/tiger/GENZ2023/](https://www2.census.gov/geo/tiger/GENZ2023/)
   *Census tract geometries used as the spatial unit of analysis in the tract-level component.*

### How References Shaped the Analysis
The ZAPP zoning layer directly prompted a core methodological decision: abandoning industrial zone polygons in favor of geocoded business license records. The literature on border-zone industrial clustering (particularly maquiladora research) suggested that freight-oriented businesses self-select for port proximity — a hypothesis we tested statistically. SANDAG's freight network data provided the infrastructure reference layer used in both indicator calculations.

---

## 5. Python Packages

> **100–150 words**

```python
# Core spatial analysis
import geopandas as gpd      # Spatial dataframes, CRS transformations, spatial joins
import pandas as pd           # Tabular data manipulation
import numpy as np            # Numerical operations, array math

# Geometry
from shapely.geometry import Point, box  # Point and polygon construction

# Visualization
import matplotlib.pyplot as plt          # Static maps and charts
import matplotlib.patches as mpatches    # Legend patches for maps
from matplotlib.lines import Line2D      # Custom legend elements

# Statistical testing
from scipy.stats import mannwhitneyu, chi2_contingency, gaussian_kde

# Network requests
import requests               # Fetching GeoJSON layers from SANDAG and Census
from io import BytesIO        # In-memory file handling for remote GeoJSON

# ArcGIS (Christian's geocoding component only)
from arcgis.gis import GIS
from arcgis.geocoding import batch_geocode
```

**Evolution from proposal:** The proposal anticipated using `arcgis.geoenrichment` for tract-level enrichment. Following Prof. Zaslavsky's feedback, this was replaced with direct Census ACS API calls, removing the ESRI dependency for the tract-level component. `scipy.stats` was added to support statistical significance testing not anticipated in the proposal.

---

## 6. Data Sources

> **200–400 words**

| Source | URL | Description |
|--------|-----|-------------|
| SD Business License Records | Internal (City of San Diego) | Active business license records (`tr_active1.csv`, `tr_active2.csv`) filtered to industrial NAICS codes |
| Census TIGER Tracts 2023 | [Link](https://www2.census.gov/geo/tiger/GENZ2023/shp/cb_2023_06_tract_500k.zip) | San Diego County census tract geometries (736 tracts) |
| ACS 5-Year 2022 (DP03) | [Link](https://api.census.gov/data/2022/acs/acs5/profile) | Tract-level civilian employment by industry |
| SANDAG POE Points | [Link](https://gis.sandag.org/FreightViewer/data/poe_points_update.json) | Port of entry point locations (10 features) |
| SANDAG Major Roads | [Link](https://gis.sandag.org/FreightViewer/data/MajorRoads_20171002.json) | Major freight road network (45 features) |
| SD Community Planning Districts | [Link](https://geo.sandag.org/server/rest/directories/downloads/) | Official city planning area boundaries (61 features, `Community_Plan_SD.geojson`) |
| SD Zoning Base | [Link](https://geo.sandag.org/server/rest/directories/downloads/Zoning_Base_SD.geojson) | All city base zone polygons (3,706 features) |
| GADM USA Level 2 | [Link](https://gadm.org/) | County-level administrative boundaries |

### Evolution from Proposal
The proposal relied on industrial zone polygons as the primary study unit. These were replaced by geocoded business license records following the realization that San Diego's industrial zoning reflects historical land allocation rather than freight-access optimization. The ACS API replaced planned ESRI GeoEnrichment calls for tract-level employment data.

### Data Quality Concerns
- **Geocoding validity:** Geocode scores (80–100) indicate address-matching confidence, not whether the registered address corresponds to an operational freight facility. A business registered at a downtown office may conduct freight operations elsewhere. A sample validation against known operational locations would be needed to confirm co-location.
- **ACS employment data:** DP03_0038E bundles utilities with transportation/warehousing. Separating these requires the detail table C24030.
- **SANDAG roads:** The major roads layer dates to 2017 and may not reflect recent network changes.
- **Desired but unavailable:** Tijuana-side industrial data; parcel-level operational land use (vs. registered land use); drive-time network distances to POEs.

---

## 7. Data Cleaning

> **~100 words**

### Business License Records (Christian)
```python
# Standardize column names
businesses.columns = (
    businesses.columns.str.strip().str.lower()
    .str.replace(" ", "_").str.replace("#", "num")
)

# Clean NAICS codes (remove float artifacts)
businesses["naics"] = (
    businesses["naics"].astype(str).str.strip()
    .str.replace(".0", "", regex=False)
)

# Filter to industrial NAICS — Core definition
industrial_core = industrial_broad[
    industrial_broad["naics"].str.startswith(core_keep_prefixes, na=False)
    & ~industrial_broad["naics"].str.startswith(core_exclude_prefixes, na=False)
].copy()
```

Key cleaning decisions:
- Removed 175 businesses geocoded outside San Diego County boundaries
- Excluded NAICS prefixes 425 (electronic markets), 485 (transit), 486 (pipelines), 487 (scenic transport) as non-freight-relevant
- Retained only geocode status "M" (matched) records

### GeoJSON Layers
All SANDAG and Census layers loaded directly from live URLs with CRS validation on import. No cleaning required beyond reprojection to the working CRS (EPSG:3310).

---

## 8. Descriptive Statistics

> *(Combination of markdown and documented code cells)*

### Business Point Distribution

```python
# Summary by subarea and industry group
businesses.groupby(["subarea", "industry_group"]).size().unstack(fill_value=0)
```

| Subarea | Manufacturing | Wholesale Trade | Transportation & Warehousing |
|---------|--------------|-----------------|------------------------------|
| Otay Mesa | — | — | — |
| Kearny Mesa | — | — | — |
| Miramar | — | — | — |
| Sorrento Valley | — | — | — |
| Other | — | — | — |

> *Fill in after running v10*

### Spatial Distribution
- **Mean center:** computed from business point coordinates
- **Standard distance:** measures dispersion around the mean center
- **Spatial autocorrelation:** Not formally tested at the point level; KDE heatmaps used to visualize clustering intensity

### Distance Summary

```python
businesses.groupby("subarea")["dist_nearest_poe_mi"].agg(
    ["count", "mean", "median", "std", "min", "max"]
).round(3)
```

> *Output populated after running v10*

---

## 9. Analysis

> **500–1000 words**

### Workflow Overview

```
Christian's geocoded CSV (industrial_businesses_core_geocoded.csv)
         │
         ▼
[joseph_indicators_v10.ipynb]
  ├── Clip to SD planning districts
  ├── Assign subareas via spatial join (Community_Plan_SD.geojson)
  ├── Indicator 1: dist_nearest_poe_mi  (gpd.sjoin_nearest → POE layer)
  ├── Indicator 1b: dist_to_freight_road_mi (gpd.sjoin_nearest → roads)
  └── Indicator 2: buffer_quarter/half/one_mi (binary inside/outside)
         │
         ▼
[joseph_indicators_output.geojson]
         │
         ▼
[joseph_visualizations_v8.ipynb]
  ├── Map 1: Overview dot map (four subareas)
  ├── Map 2: POE distance graduated color + planning district outlines
  ├── Map 3: Otay Mesa zoom — buffer rings
  ├── Map 4: KDE heatmap 2×2 grid
  ├── Chart: Buffer overlap bar chart (four areas)
  ├── Chart: POE distance box plot (four areas)
  └── Stats: Pairwise Mann-Whitney U + Chi-square
```

### Step-by-Step

**Step 1 — CRS selection**
All spatial operations use EPSG:3310 (California Albers, meters), matching Christian's pipeline exactly. Distances computed in meters, converted to miles for reporting.

**Step 2 — Subarea assignment**
Businesses are assigned to study areas via `gpd.sjoin` on official City of San Diego Community Planning District boundaries (`Community_Plan_SD.geojson`), matching Christian's `planning_area` approach. The four study areas map to planning districts as follows:

- Otay Mesa → `OTAY MESA` + `OTAY MESA-NESTOR`
- Kearny Mesa → `KEARNY MESA`
- Miramar → `MIRAMAR RANCH NORTH` + `SCRIPPS MIRAMAR RANCH`
- Sorrento Valley → `MIRA MESA` *(no official Sorrento Valley district)*

**Step 3 — Indicator 1: POE Distance**
Distance from each business point to the nearest POE is computed using `geometry.distance()` against the union of all SANDAG POE points. Separate distances to San Ysidro and Otay Mesa POEs are also retained. Summarized by subarea.

**Step 4 — Indicator 1b: Freight Road Distance**
`gpd.sjoin_nearest()` against the SANDAG major roads layer assigns each business its distance to the nearest road segment. Distance categories match Christian's bins: 0–0.25, 0.25–0.5, 0.5–1, 1–2, 2+ miles.

**Step 5 — Indicator 2: Buffer Flags**
The dissolved road network is buffered at 402m (0.25 mi), 805m (0.50 mi), and 1,609m (1.00 mi). Each business receives a binary flag per buffer distance.

**Step 6 — Statistical Testing**
Pairwise comparisons for each of the three comparison areas vs. Otay Mesa:
- **Mann-Whitney U** on `dist_nearest_poe_mi` — non-parametric, appropriate for right-skewed distance distributions
- **Chi-square + Cramér's V** on each buffer flag — proportion test for binary outcomes
- **95% bootstrap CIs** on all effect sizes (2,000 iterations)

**Evolution from Proposal**
The proposal anticipated using industrial zone polygons and ESRI GeoEnrichment. Both were replaced: polygons by geocoded business records (following the leftover-land critique), GeoEnrichment by direct Census ACS API calls. Statistical significance testing was not in the original proposal and was added based on the need to distinguish the Otay Mesa difference from sampling variation.

---

## 10. Summary of Results

> **200–400 words**

### Key Findings

**Indicator 1 — POE Distance:**
- Otay Mesa businesses: median **1.06 miles** from nearest POE (n = 466)
- Non-border comparison: median **20.07 miles** (n = 2,426)
- Mann-Whitney U: rank-biserial r = **0.972**, p < 0.0001
- A randomly selected Otay Mesa business is closer to a POE than a non-border business **97.2% of the time**

**Indicator 2 — Freight Corridor Buffer:**

| Buffer | Otay Mesa | Kearny Mesa | Miramar | Sorrento Valley |
|--------|-----------|-------------|---------|-----------------|
| 0.25 mi | 45.9% | — | — | — |
| 0.50 mi | 84.5% | — | — | — |
| 1.00 mi | 96.4% | — | — | — |

> *Fill in comparison area values after running v10*

**Core finding:** POE proximity is the dominant spatial signal distinguishing Otay Mesa's industrial activity. Corridor access (freight road proximity) is real but modest in effect size, reflecting that major freight roads serve industrial areas throughout San Diego County — not exclusively near the border.

---

## 11. Discussion

> **200+ words**

### Findings in Context of Literature
The strong POE-proximity clustering documented here is consistent with research on border-zone industrial development showing that freight-oriented businesses self-select for locations minimizing cross-border transport costs. The near-complete separation (r = 0.972) is stronger than typical distance-decay effects found in urban industrial location literature, suggesting that the border crossing itself — not just road access — is the organizing principle of Otay Mesa's industrial geography.

### Trade-offs and Decision Points

**Buffer distance:** The choice of 0.25, 0.50, and 1.00 mile buffer thresholds is researcher-defined. Zaslavsky's feedback noted that findings should not depend on one arbitrary distance — our three-threshold approach partially addresses this by showing consistency across distances.

**CRS selection:** EPSG:3310 (California Albers) was chosen to match Christian's pipeline and uses meters as the distance unit, appropriate for the scale of analysis.

**Subarea definition:** Planning district boundaries replace the researcher-defined bounding box and 3-mile circles used in earlier versions, grounding subarea definitions in official city geography.

**Geocoding validity:** Geocode scores reflect address-matching confidence, not operational location accuracy. This is the most significant unresolved methodological concern.

**Sorrento Valley:** No official Sorrento Valley planning district exists. MIRA MESA was used as the closest available match, which may not fully represent the intended comparison area.

---

## 12. Conclusions & Future Work

> **200+ words**

### Did We Answer the Research Question?
Yes, with important caveats. The spatial association between Otay Mesa's industrial activity and port of entry proximity is statistically significant and extremely strong. However, the analysis documents where businesses are *registered*, not necessarily where their freight operations occur.

### Future Work

1. **Border-logistics indicator businesses:** Identify NAICS subcategories unique to Otay Mesa (customs brokers 541614, freight forwarders 488510, cold storage 493120) to construct a "border-economy index" as suggested by Prof. Zaslavsky.

2. **Operational location validation:** Validate a sample of geocoded businesses against known operational addresses (company websites, satellite imagery) to assess how often registered and operational addresses diverge.

3. **Tijuana-side analysis:** Extend to the Mexican side of the border — maquiladora zones directly across from Otay Mesa are the other half of the cross-border production system.

4. **Drive-time distance:** Replace straight-line POE distance with network/drive-time distance accounting for road geometry and border wait times.

5. **Otay Mesa East POE:** Model the expected spatial shift in industrial clustering if the proposed new crossing opens, using the distance-decay relationship documented here.

6. **LODES employment data:** Use Census LODES to distinguish where workers are *employed* (vs. where they *reside*) at the tract level, separating production workers from commuters.

### Expected Use
Results are most immediately relevant to SANDAG regional planners and City of San Diego economic development staff considering land use decisions near the proposed Otay Mesa East crossing. The spatial framework developed here could be extended to other US–Mexico border crossings in California and Texas.

---

*Notebook prepared for GPEC 447, UC San Diego, Spring 2026.*
