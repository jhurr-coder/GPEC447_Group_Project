# GPEC 447 - Otay Mesa Industrial-Logistics Project: Integration Reference

**Team:** Canyu Li, Christian Phouasalith, Joseph Hurr

This reference records the shared definitions and interfaces that let the three workstreams
combine without conflicting or duplicating logic. It documents what each part produces, the data
contract between parts, and the conventions for credentials, coordinate systems, and run order.

---

## 1. What each part produces

| Part | Owner | Input | Output |
|---|---|---|---|
| GeoEnrichment | Joseph | ArcGIS GeoEnrichment on SD tracts | per-tract business / employee **counts** (CSV) |
| Business points | Christian | City business-tax CSVs | geocoded industrial **businesses as points** (CSV, WGS84) |
| Standalone notebook + overlap measures | Canyu | public Census + SANDAG layers | indicators, statistics, maps, and **overlap measures** |

`Code_canyu.ipynb` is the analytical spine and runs end to end on public data alone. The other two
outputs attach to it as optional inputs (the notebook's Section 10 hooks) that add detail but are
never required for the notebook to complete.

**Canyu's core spatial task** (Plan of Analysis): *calculate overlap measures among relevant general
industrial zoning, industrial-plan land use, employment centers, and freight-related
infrastructure.* This is the polygon overlay and containment analysis in **Section 15** of the
notebook: intersection area, Jaccard index, containment ratios, a four-way coupling core, and
per-tract area shares.

### Why the three parts do not overlap functionally

"Employment" and "industrial business" appear in more than one part, but each part uses a different
representation, so they measure different things:

| Who | Represents | Data type |
|---|---|---|
| Canyu | employment **centers** and industrial land (do the layers coincide in space) | polygon geometry |
| Joseph | employment / business **counts** per tract (how much activity) | numeric attributes |
| Christian | individual **firms** (which specific businesses, and each firm's distance to freight) | points |

The notebook's Hook B (Section 10) consumes Christian's points only to **count establishments per
tract** and report their correlation with ACS industrial employment as a cross-check. It does not
recompute per-firm distances - that distance measure is Christian's output and is not duplicated in
the notebook.

---

## 2. Unit of analysis: census tract

All three parts describe the same census tracts and the same industrial universe.

The census tract is used rather than the industrial zone for measurable reasons:

- The City of San Diego contains only a handful of general-industrial zones - too few observations
  to support statistics or any model.
- Industrial zoning in a spatially constrained city often occupies land left available after other
  allocations, so a zone label is a weak proxy for freight orientation.
- Census tracts provide hundreds of observations and carry ACS industry-of-employment counts
  directly, so activity can be measured, not just designated.

Otay Mesa is the primary case; Kearny Mesa, Miramar, and Sorrento Valley are non-border comparison
areas measured with identical indicators.

---

## 3. Data contract between parts

**Geographic exchange format: WGS84 longitude/latitude (EPSG:4326).** Every file passed between
parts stores coordinates in WGS84. Each part may use a different projected CRS internally for
distance and area work - that choice is local and does not affect the interface:

| Part | Internal projected CRS | Exchanged as |
|---|---|---|
| Canyu notebook | EPSG:2230 (CA zone 6, US survey feet) | reads WGS84, reprojects on load |
| Christian | EPSG:3310 (CA Albers, meters) | converts back to WGS84 before writing CSV |
| Joseph | EPSG:4326 for enrichment | WGS84 |

Both projected systems yield correct planar distances and areas; results agree to within
projection-level differences that are negligible at this scale.

**Tract identifier: `GEOID` (11-digit string), `tract_geoid` on point files.** Christian's geocoded
output assigns each business its containing tract as `tract_geoid` via a spatial join. When that
column is present, Hook B groups on it directly; when it is absent, the notebook spatially joins the
points to its own tracts. Either path produces per-tract establishment counts keyed to the same
`GEOID`.

**Optional input files the notebook looks for** (place in `data_processed/`):

- `esri_enrichment_by_tract.csv` - Joseph's GeoEnrichment counts, joined on `GEOID` (Hook A).
- `industrial_businesses_core_geocoded.csv` - Christian's geocoded points with WGS84
  `longitude`/`latitude` (and optionally `tract_geoid`), counted per tract (Hook B).

**Shared industrial definition (NAICS).** The "broad" industrial set is NAICS 31-33 (manufacturing),
42 (wholesale), 48-49 (transportation and warehousing), and 8113 (industrial machinery repair). The
"core" set keeps freight-relevant subsectors and excludes non-freight wholesale and transit/postal
codes (425, 485, 486, 487). The notebook's ACS proxy (manufacturing + wholesale +
transportation/warehousing) aligns with the broad set at the tract level.

---

## 4. Credentials: entered once

All ArcGIS access reads the username from the `ARCGIS_USERNAME` environment variable, so the parts
authenticate through one consistent mechanism rather than hard-coded accounts.

In `Code_canyu.ipynb`, the Section 1 setup cell prompts once for the Census API key (required) and,
optionally, the ArcGIS username, and stores both in the process environment. Every later cell reads
from the environment, so **running the whole notebook requires entering credentials only once**, at
setup. Re-running the setup cell reuses values already in the environment without prompting again.

Christian's and Joseph's scripts read the same `ARCGIS_USERNAME` variable, so a single signed-in
account (the geocoding/enrichment service account, e.g. `gpec447sp26_14` or `gpec447sp26_23`) covers
all three parts; the specific account only needs entitlements for geocoding and GeoEnrichment.

---

## 5. Network robustness for tract loading

Some campus and proxied networks block direct access to `www2.census.gov` and SANDAG hosts. The
notebook handles the tract layer specifically:

- **Primary:** Census TIGER cartographic-boundary tracts (`cb_2023_06_tract_500k`).
- **Automatic fallback:** a GitHub-hosted Census mirror (`loganpowell/census-geojson`, 2020 500k
  tracts), fetched with `requests` to a local file and then read from disk. Fetching to disk avoids
  the SSL failure that GDAL's network reader hits behind some proxies.

Either source yields the 736 San Diego County tracts (filtered on `COUNTYFP == "073"`) with a
compatible `GEOID`. The county administrative boundary comes from the uploaded `gadm41_USA_2.json`
(GADM level 2); its southern edge coincides with the US-Mexico international border and is drawn on
the Otay Mesa maps for context. The SANDAG zoning, land-use, employment-center, and freight layers
in Sections 6 and 14 still require network access to those hosts; where a layer is unreachable the
notebook prints a notice and continues, and the tract-level analysis is unaffected.

---

## 6. Run order

The notebook is self-contained: Section 9 can generate the two optional CSVs itself (given the
business-tax inputs and an ArcGIS account), and Sections 10+ consume them. The same CSVs can instead
be produced outside the notebook and dropped in. Either path works:

**In-notebook (single submission):**
1. Place the City business-tax CSVs (`tr_active1.csv`, `tr_active2.csv`) beside the notebook.
2. Run `Code_canyu.ipynb` top to bottom; enter credentials once at Section 1. Section 9 geocodes
   the business points and runs GeoEnrichment, writing both CSVs into `data_processed/`; Section 10
   then attaches them.

**Pre-produced (files supplied separately):**
1. Generate `industrial_businesses_core_geocoded.csv` and `esri_enrichment_by_tract.csv`.
2. Drop them into `data_processed/`, set `GEN_BUSINESS_POINTS`/`GEN_ENRICHMENT` to `False` in
   Section 9 to skip regeneration, and run the notebook.

Without the business-tax inputs or an ArcGIS account, Section 9 skips cleanly and the notebook runs
on public data alone.

---

## 7. File map

| File | Role |
|---|---|
| `Code_canyu.ipynb` | self-contained notebook: upstream data products (Section 9), indicators, statistics, composite maps, and the overlap measures (Section 15) |
| `INTEGRATION_GUIDE.md` | this reference |

Christian's and Joseph's scripts are maintained in their own files in the group repository.
