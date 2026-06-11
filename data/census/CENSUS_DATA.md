# Census / NHGIS data inventory (`data/census`)

This folder holds a single **IPUMS NHGIS** extract (`nhgis0008`) used to support geographic summaries for the Maryland crash-cost project. The extract is **nationwide** (all U.S. states and equivalent areas). For this project, restrict analysis to **Maryland** using geography fields in the CSVs (see [Maryland subset](#maryland-subset-for-this-project)).

---

## What is in the folder

| File | Approx. size | Contents |
|------|--------------|----------|
| `nhgis0008_csv.zip` | ~26 MB | ACS 5-year **tabular** extracts (CSV) plus **codebooks** (`.txt`) |
| `nhgis0008_shape.zip` | ~788 MB | **TIGER/Line 2024** shapefile archives (nested ZIPs) for tracts, counties, and places |

Unzip these archives when you need to read data in GIS or pandas/geopandas. Paths below are **inside** the archives after the outer unzip.

---

## Tabular data (`nhgis0008_csv.zip`)

All CSVs share NHGIS **context** fields (identifiers for joining and labeling), including **`GISJOIN`** (primary key for linking to NHGIS shapefiles), **`STUSAB`** (state postal code), **`STATEA`** (state FIPS), **`GEO_ID`**, **`TL_GEO_ID`**, and other geographic roll-up codes. Each file also includes **`YEAR`** (file reference year for the 5-year period).

NHGIS supplies **estimates** and, where applicable, **margins of error**; estimate columns typically use an `E` suffix pattern in the data dictionary (e.g. table codes like `AUO6`), and margins use `M`. See each codebook for the exact column names.

### Two ACS table bundles (datasets)

The extract contains **two** NHGIS dataset IDs, both for the **2020–2024 ACS 5-year** release but with different **minimum geography** and **tables**:

| NHGIS ID | Census / NHGIS dataset label | Geography coverage in this extract | ACS tables included (by census table ID) |
|----------|-------------------------------|--------------------------------------|------------------------------------------|
| **ds272** | `2020_2024_ACS5a` — *Block Groups & Larger Areas* | State, county, place, **census tract** | **B01003** Total population; **B08301** Means of transportation to work; **B08303** Travel time to work; **B19013** Median household income (in **2024 inflation-adjusted dollars**); **B25001** Housing units |
| **ds273** | `2020_2024_ACS5b` — *Tracts & Larger Areas* | State, county, place, **census tract** | **B08201** Household size by vehicles available |

For each dataset, NHGIS provides **four** geographic resolutions:

| Geographic level | ds272 CSV (inside zip) | ds273 CSV (inside zip) | Codebooks (`.txt`) |
|------------------|------------------------|------------------------|--------------------|
| State | `nhgis0008_ds272_20245_state.csv` | `nhgis0008_ds273_20245_state.csv` | `*_state_codebook.txt` |
| County | `nhgis0008_ds272_20245_county.csv` | `nhgis0008_ds273_20245_county.csv` | `*_county_codebook.txt` |
| Place (Census place) | `nhgis0008_ds272_20245_place.csv` | `nhgis0008_ds273_20245_place.csv` | `*_place_codebook.txt` |
| Census tract | `nhgis0008_ds272_20245_tract.csv` | `nhgis0008_ds273_20245_tract.csv` | `*_tract_codebook.txt` |

### Nationwide row counts (for scale)

These counts include all U.S. areas in the extract (before any Maryland filter):

| Level | Rows per ds272 CSV | Rows per ds273 CSV |
|-------|--------------------|--------------------|
| State | 52 | 52 |
| County | 3,222 | 3,222 |
| Place | 32,330 | 32,330 |
| Census tract | 85,382 | 85,382 |

To build a single tract-level analytic file, you would typically **merge** `ds272` and `ds273` tract tables on **`GISJOIN`** (or `GEO_ID` / FIPS components), then restrict to Maryland.

### Codebooks

Every CSV has a matching **`*_codebook.txt`** file in the same ZIP. Each codebook lists:

- Data summary (dataset, years, geographic level, tables)
- Full **data dictionary** (context fields + table variables)
- NHGIS **citation and use** language

Authoritative variable definitions are in those text files, not duplicated here.

---

## Shapefiles (`nhgis0008_shape.zip`)

The outer archive contains **three** inner ZIPs, each a full Esri shapefile set for **2024 TIGER/Line**, national extent:

| Inner archive (path inside `nhgis0008_shape.zip`) | Likely layer |
|---------------------------------------------------|--------------|
| `nhgis0008_shapefile_tl2024_us_tract_2024.zip` | U.S. census tracts |
| `nhgis0008_shapefile_tl2024_us_county_2024.zip` | U.S. counties (and county equivalents) |
| `nhgis0008_shapefile_tl2024_us_place_2024.zip` | U.S. Census places |

Unzipping one of these yields the usual components (e.g. `.shp`, `.shx`, `.dbf`, `.prj`, …). NHGIS shapefiles include **`GISJOIN`** (and related fields) so they can be joined to the CSV extracts on **`GISJOIN`**.

### Local cache used by `crash_costs.ipynb`

The notebook extracts each inner shapefile ZIP once into **`tl2024_shapes_cache/`** (subfolders `county/`, `tract/`, `place/`) so **geopandas** can open `US_*_2024.shp` quickly on later runs. You can point QGIS or other tools at those same paths for visualization. Polygons are still filtered with **`STATEFP = '24'`** when building Maryland layers for spatial join.

---

## Maryland subset (for this project)

- Filter tabular CSVs: **`STUSAB == 'MD'`** (or **`STATEA == 24`**, Maryland state FIPS).
- After filtering, expect on the order of **24 county rows**, **hundreds of tract rows**, and **many place rows** (exact counts depend on the vintage and NHGIS place universe).
- For spatial work, clip or filter the national shapefiles to Maryland, or download a Maryland-only TIGER product if you prefer smaller files.

Crash coordinates in the main project use latitude/longitude; you can **spatially join** points to tract / place / county polygons once CRS is handled consistently (TIGER/Line uses NAD83 for recent vintages; confirm in each `.prj`).

---

## Documentation and citation

- NHGIS documentation: [https://www.nhgis.org/documentation](https://www.nhgis.org/documentation)  
- Tabular data overview: [https://www.nhgis.org/documentation/tabular-data](https://www.nhgis.org/documentation/tabular-data)  
- Suggested NHGIS citation: follow [IPUMS NHGIS citation guidance](https://www.nhgis.org/user-resources/citation) when publishing.

Underlying ACS data are from the **U.S. Census Bureau, American Community Survey**. Use Census guidance for ACS citation when reporting estimates.

---

## Quick reference: why two CSV datasets?

- **ds272** bundles **demographic, commuting, income, and housing-unit** tables that NHGIS distributes for **block group and larger** summary levels in this product line.
- **ds273** adds **vehicle-availability / household composition** (**B08201**) at **tract and larger** levels in this product line.

Together they support analyses that relate crash context to **population, journey-to-work, income, housing stock, and household vehicle ownership**, at tract, place, county, or state geography.
