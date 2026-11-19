# Final Thesis Tools — arcpy, PyQGIS and Python/GDAL scripts

*Português: [README.md](README.md)*

Conversion of the ModelBuilder models gathered in the toolbox
**`1_Ferramentas Finais da Tese.tbx`** into Python scripts using `arcpy`
(ArcGIS Pro), PyQGIS (QGIS) and plain Python with GDAL/OGR.

Each script was checked both against the parameters stored in the
original diagram (the tooltips of the model boxes) and, when available,
against the script exported natively from ArcMap 10.3 (Model → Export →
To Python Script).

> **A note on file and model names.** The file names, folder names and
> toolbox model names in this repository are in Portuguese (for example
> *Entalhamento do Vale*, *Dimensão Interfluvial*, *Grau de Dissecação*,
> *Fragilidade Ambiental*, *Vulnerabilidade Ambiental*). They are kept
> exactly as they are in the repository so that every path in this README
> works as written. The English terms used in the text are:
> *Entalhamento do Vale* = Valley Incision, *Dimensão Interfluvial Média* =
> Mean Interfluve Dimension, *Grau de Dissecação* = Dissection Degree,
> *Fragilidade Ambiental* = Environmental Fragility,
> *Vulnerabilidade Ambiental* = Environmental Vulnerability,
> *Uso e Cobertura da Terra* = Land Use and Land Cover.

## Link to the thesis

Alex da Silva Sousa. *Workflow científico aplicado à modelos ambientais:
automatização das classificações ecodinâmicas e análise espaço-temporal*
(in English: *A scientific workflow applied to environmental models:
automating ecodynamic classifications and spatio-temporal analysis* —
free translation of the title, for this README only).
Thesis (PhD) — Physical Geography Graduate Program, FFLCH-USP, 2024.
DOI: [10.11606/T.8.2024.tde-18022025-121027](https://doi.org/10.11606/T.8.2024.tde-18022025-121027)

## Pipeline

The toolbox gathers several models. The first three calculate the Relief
Dissection Degree; the fourth combines that result with the other
environmental layers of the thesis (soils, land use and land cover,
climate) to produce the Environmental Fragility map of the landscape
(Jean Tricart's ecodynamic methodology, with Ross's weights); the fifth
produces the Environmental Vulnerability map (Crepani's weights) as the
mean of five themes.

| # | Model (toolbox) | Script(s) | What it does |
|---|---|---|---|
| 1 | `1_Entalhamento do Vale_FINAL_Geografica` | `scripts/arcgis_pro/1_Entalhamento do Vale_ArcPRO.py` (ArcGIS Pro), `scripts/qgis/1_Entalhamento do Vale_QGIS.py` (QGIS, free software) and `scripts/software_livre/1_Entalhamento do Vale_SoftwareLivre.py` (Python + GDAL, no QGIS) | Calculates the valley incision depth from the DEM |
| 2 | `2_Dimensão Interfluvial Média_FINAL_Geografica` | `scripts/arcgis_pro/2_Dimensao Interfluvial_ArcPRO.py` (ArcGIS Pro), `scripts/qgis/2_Dimensao_Interfluvial_Media_QGIS.py` (QGIS, free software) and `scripts/software_livre/2_Dimensao_Interfluvial_Media_SoftwareLivre.py` (Python + GDAL, no QGIS) | Calculates the mean interfluve width from a sub-basin raster (any source, as long as it is already a raster) |
| 3 | `3_Grau de Dissecação` | `scripts/arcgis_pro/3_Grau de Dissecacao_ArcPRO.py` (ArcGIS Pro), `scripts/qgis/3_grau_de_dissecacao_QGIS.py` (QGIS, free software) and `scripts/software_livre/3_grau_de_dissecacao_SoftwareLivre.py` (Python + GDAL, no QGIS) | Combines the reclassified results of steps 1 and 2 into the final Dissection Degree indices (Fragility and Vulnerability) |
| 4 | `4_FragilidadeAmbiental` | `scripts/arcgis_pro/4_FragilidadeAmbiental_ArcPRO.py` (ArcGIS Pro), `scripts/qgis/4_FragilidadeAmbiental_QGIS.py` (QGIS, free software) and `scripts/software_livre/4_FragilidadeAmbiental_SoftwareLivre.py` (Python + GDAL, no QGIS) | Adds Relief (Dissection Degree) + Soils + Land Use and Land Cover + Climate (WorldClim) into the 4-digit Environmental Fragility matrix, one raster per land use year |
| 5 | `5_VulnerabilidadeAmbiental` | `scripts/arcgis_pro/5_VulnerabilidadeAmbiental_ArcPRO_V6_completa.py` (ArcGIS Pro), `scripts/qgis/5_VulnerabilidadeAmbiental_QGIS_V6_completa.py` (QGIS, free software) and `scripts/software_livre/5_VulnerabilidadeAmbiental_SoftwareLivre_V6_completa.py` (Python + GDAL, no QGIS) | Complete Vulnerability workflow (Crepani, scale × 10): builds the Relief (incision + interfluve dimension + DEM slope), converts Geology, Soils and Climate (vectors) into rasters and takes the mean (Cell Statistics, ignoring NoData) of these four themes together with Land Use and Land Cover; three products, two of them per land use year |
| — | `Modelo Geral_Fragilidade_DissecaçãoV5` and the remaining models (Fragility with INMET data, Potential/Emergent Fragility) | *not converted yet* | Variants and later stages of the environmental fragility/vulnerability maps |

The first 4 must be run in that order (the output of one feeds the next);
script 4 uses the output of script 3 and, besides it, data that come from
other methodological chapters of the thesis (pedology, climate, land use
and land cover — see the "Environmental Fragility" section below).
Script 5 (Vulnerability) does not use the output of script 3: it starts
from thematic rasters that are already on the vulnerability scale (see
the "Environmental Vulnerability" section) and from a table of weights
from the thesis ("Fragility and Vulnerability Weights", at the end of
this README).

## Repository structure

- `scripts/` — the converted scripts, one subfolder per program. Pick the
  folder according to what you have installed and follow steps 1 to 5 in
  order (the number at the start of the file name is the step):
  - `scripts/arcgis_pro/` — ArcGIS Pro (`arcpy`; requires Spatial Analyst).
  - `scripts/qgis/` — QGIS 3.x (PyQGIS; also runs without opening QGIS).
  - `scripts/software_livre/` — plain Python with GDAL/OGR, with no QGIS
    and no ArcGIS.
- `modelbuilder/1_Ferramentas Finais da Tese.tbx` — the original toolbox
  with the thesis models.
- `modelbuilder/exports_arc103/` — the Python code exported by ModelBuilder
  itself (ArcMap 10.3, *Model > Export > To Python Script*) for each
  model: it is the reference against which the parameters of the scripts
  were checked. For Vulnerability there are two, which in the toolbox are
  model **V6** and model **V7**: `5_VulnerabilidadeAmbiental_Arc103_V6_completa.py`
  (**V6**, the complete version of the thesis, on which scripts 5 are
  based) and `5_VulnerabilidadeAmbiental_Arc103_V7_simplificada.py`
  (**V7**, a simplified version that reads the four ready-made themes —
  see the note in the Environmental Vulnerability section).
  The file name of the step 1 export carries a warning that it comes out
  with an error caused by the ArcMap exporter itself (see the
  "Methodological transparency note"): for that model, use the toolbox or
  the script in `scripts/arcgis_pro/`.

## The four versions of "Valley Incision" (*Entalhamento do Vale*)

For this tool specifically, there are four equivalent ways of running the
same methodology (Chapter 6.3 of the thesis), each with a different way
of organizing folders/GDB and input data:

### 1) The original model (`1_Entalhamento do Vale_FINAL_Geografica`, inside the toolbox, ModelBuilder/ArcMap/ArcGIS Pro)

This is the original artifact used in the thesis. It **does not ask for
paths at run time** — the paths are stored inside the model diagram
itself (in each data box). To reuse it today, you need to:

1. Recreate, on your computer, the same folder and the same geodatabase
   that were stored in the original model (`D:\Doutorado\Entalhamento.gdb`),
   with exactly that name — or open the model in ModelBuilder and, in each
   data box, right-click to point it again to where the files are on your
   computer today.
2. Place inside that structure (or point the model to) the DEM/mosaic
   raster and the shapefile/feature class of the study-area boundary,
   with the same names/paths the model expects.
3. Run the model normally inside ArcMap/ArcGIS Pro (Catalog > Toolboxes >
   double-click the model).

In other words: with the model, the folder organization is fixed (defined
by the diagram) — it is you who adapt to it, either by recreating the
structure or by re-pointing the data.

### 2) `scripts/arcgis_pro/1_Entalhamento do Vale_ArcPRO.py` (ArcGIS Pro / arcpy)

It already comes organized automatically: the script creates the working
folder and geodatabase by itself, directly on drive C:, and asks for the
input data when you run it — there is no need to edit anything in the
code.

- **Working folder/GDB (created automatically):**
  `C:\alexgeopro\Entalhamento.gdb`
- **Input data (asked on screen at run time, may be in any folder):**
  - DEM / mosaic raster (e.g. `C:\dados\mosaicoRMSP.tif`)
  - study-area shapefile/feature class (e.g. `C:\dados\AreaEstudo.shp`)
- **Outputs** (all inside the geodatabase above): `a_` to `g_` are
  intermediate; `h_entalhamento` is the continuous incision (meters per
  pixel) and `i_EntalhamentoRecla` is the final result reclassified into
  5 weight classes (Ross/Crepani).

### 3) `scripts/qgis/1_Entalhamento do Vale_QGIS.py` (QGIS + Python, free software)

Same automatic organization logic, adapted to free tools (GeoPackage
instead of geodatabase):

- **Working folder (created automatically):**
  `C:\alexgeopro\Entalhamento_QGIS`
- **Inside it:** `Entalhamento.gpkg` (intermediate vector layers) and the
  `a_` to `i_` rasters as loose `.tif` files in the same folder.
- **Input data** (asked on screen at run time, may be in any folder): the
  same two as above — DEM/mosaic raster and study-area
  shapefile/feature class.
- **Outputs:** `h_entalhamento.tif` (continuous incision) and
  `i_EntalhamentoRecla.tif` (reclassified into 5 classes, Ross/Crepani) —
  the same two final products as the ArcGIS Pro version.

Running this version requires QGIS to be installed (with scipy and
scikit-image in its Python — see `Requirements` below); it can be run
from inside the QGIS Python Console, or from the terminal in "headless"
mode (without opening the QGIS window) — see the `Requirements` section.

### 4) `scripts/software_livre/1_Entalhamento do Vale_SoftwareLivre.py` (Python + GDAL/OGR, no QGIS)

Same automatic organization logic as the versions above, but with NO
dependency on QGIS whatsoever — it calls the GDAL/OGR libraries directly
(`osgeo.gdal`/`osgeo.ogr`), which are the same ones QGIS uses under the
hood, only without needing the QGIS program installed:

- **Working folder (created automatically):**
  `C:\alexgeopro\Entalhamento_SemQGIS`
- **Inside it:** `Entalhamento.gpkg` (intermediate vector layers) and the
  `a_` to `i_` rasters as loose `.tif` files in the same folder — same
  organization as the QGIS version.
- **Input data and outputs:** the same as the QGIS version (item 3 above).
- Runs on any ordinary Python installation (Windows, Linux, macOS) that
  has the `gdal`, `numpy`, `scipy` and `scikit-image` packages installed —
  the simplest way is via conda:
  `conda install -c conda-forge gdal numpy scipy scikit-image`.
- Just run `python "1_Entalhamento do Vale_SoftwareLivre.py"` in an
  ordinary terminal — there is no need to open QGIS or ArcGIS Pro for
  anything.

## Mean Interfluve Dimension (*Dimensão Interfluvial Média*)

Three versions, same automatic-organization pattern as the incision
script (the original model, inside the toolbox, follows the same logic as
"Valley Incision" — fixed paths stored in the diagram, see the section
above):

**Input data, in all versions** (asked on screen at run time, may be in
any folder): a sub-basin raster (e.g. `C:\dados\Subbacias.tif`). By
default, the data used are the official sub-basins of the State of São
Paulo (Secretaria do Meio Ambiente/CPLA, 2013, produced by FUNCATE in
partnership with the Instituto Geológico — see
`Ficha_Tecnica_Sub_bacia.pdf`), but any other source of sub-basins will
do, as long as it has already been converted to a raster before running
the script.

### `scripts/arcgis_pro/2_Dimensao Interfluvial_ArcPRO.py` (ArcGIS Pro)

- **Working folder/GDB (created automatically):**
  `C:\alexgeopro\DimensaoInterfluvial.gdb`
- **Outputs** (inside the geodatabase above): `a_` to `i_` are
  intermediate; `j_Dimensao` is the continuous mean interfluve dimension
  (meters) per sub-basin; `l_DimensaoReclaFrag` and `l_DimensaoReclaVul`
  are the two final reclassified results (Ross/Fragility and
  Crepani/Vulnerability).

### `scripts/qgis/2_Dimensao_Interfluvial_Media_QGIS.py` (QGIS, free software)

- **Working folder (created automatically):**
  `C:\alexgeopro\DimensaoInterfluvial_QGIS`, with the `a_`, `d_`, `i_`,
  `j_` and `l_` rasters as loose `.tif` files inside it.
- **Final outputs:** the same two as above — `j_Dimensao.tif`
  (continuous) and `l_DimensaoReclaFrag.tif` / `l_DimensaoReclaVul.tif`
  (reclassified).
- Since the sub-basin raster already carries the identifier of each
  sub-basin pixel by pixel, the "Raster to Polygon" and "Polygon To Line"
  steps of the original model are not needed — the edge of each sub-basin
  is identified directly in the array, by comparing each pixel with its
  neighbors. For the same reason, the iterative Eliminate cleanup (5x in
  the original model) is not needed here either. Full details in the
  script header.
- It uses the same degrees→meters conversion constant as the thesis
  (107015), unchanged — see the transparency note in the script header.

Running the QGIS version requires QGIS to be installed (with scipy and
scikit-image in its Python — see `Requirements` below).

### `scripts/software_livre/2_Dimensao_Interfluvial_Media_SoftwareLivre.py` (Python + GDAL, no QGIS)

Same logic as the QGIS version above, but with no dependency on QGIS —
it calls `gdal.Warp()` directly instead of QGIS's `gdal:warpreproject`
algorithm:

- **Working folder (created automatically):**
  `C:\alexgeopro\DimensaoInterfluvial_SemQGIS`.
- **Input data and outputs:** the same as the QGIS version.
- Runs on any ordinary Python installation with `gdal`, `numpy`, `scipy`
  and `scikit-image` installed (`conda install -c conda-forge gdal numpy
  scipy scikit-image`) — just run `python
  "2_Dimensao_Interfluvial_Media_SoftwareLivre.py"` in an ordinary
  terminal.

## Dissection Degree (*Grau de Dissecação*)

Combines the results of the two previous scripts into a single final
index, per area of interest. Three versions:

**Input data, in all of them:** the three reclassified rasters generated
by scripts 1 and 2 (the script looks for them by itself in the default
locations of each version, and only asks for the path on screen if it
cannot find one automatically), and the vector boundary of the area of
interest (by default, the State of São Paulo — but any study area will
do), which is always asked on screen.

### How to read the final value: Tables 19, 20 and 21 of the thesis

The final raster is the sum of the Valley Incision class (tens digit: 10
to 50) and the Mean Interfluve Dimension class (units digit: 1 to 5), so
each pixel gets a two-digit number: **the first digit is the row**
(Incision) **and the second is the column** (Interfluve Dimension) of the
tables below. For example, `34` = Incision of 40 to 80 m (row) combined
with an Interfluve Dimension of 250 to 750 m (column). The columns follow
the order of the units classes: class 1 is the left-hand column (larger
interfluve dimension, less dissected relief) and class 5 is the
right-hand one (smaller dimension, more dissected).

In the thesis, the cells of Tables 19 and 20 are colored, and Table 21
defines the meaning of each color (Fragility/Vulnerability). The color
scheme is the same in both tables:

- Dark green: `11`
- Light green: `12`, `21`, `22`
- Yellow: `13`, `23`, `31`, `32`, `33`
- Orange: `14`, `24`, `34`, `41`, `42`, `43`, `44`
- Red: `15`, `25`, `35`, `45`, `51`, `52`, `53`, `54`, `55`

**Table 19 — Fragility classes for medium and small scales**
(adapted from Crepani et al., 2001). Script: `b_GrauDeDissecacao_Fragilidade`.

Columns: Drainage Density or Mean Interfluve Dimension (m).

| Valley Incision Degrees (m) | Fragility | > 3,750 (Very Weak) | 1,750 to 3,750 (Weak) | 750 to 1,750 (Medium) | 250 to 750 (Strong) | < 250 (Very Strong) |
|---|---|:---:|:---:|:---:|:---:|:---:|
| < 20 | Very Weak | 11 | 12 | 13 | 14 | 15 |
| 20 to 40 | Weak | 21 | 22 | 23 | 24 | 25 |
| 40 to 80 | Medium | 31 | 32 | 33 | 34 | 35 |
| 80 to 160 | Strong | 41 | 42 | 43 | 44 | 45 |
| > 160 | Very Strong | 51 | 52 | 53 | 54 | 55 |

**Table 20 — Vulnerability classes for medium and small scales**
(adapted from Crepani et al., 2001). Script:
`b_GrauDeDissecacao_Vulnerabilidade`.

Columns: Interfluve Amplitude (m); the value in parentheses is the
vulnerability weight of the column.

| Altimetric Amplitude (m) | Vulnerability | > 5,000 (1.0) | 2,000 to 5,000 (1.5) | 750 to 2,000 (2.0) | 250 to 750 (2.5) | < 250 (3.0) |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| < 20 | 1.0 | 11 | 12 | 13 | 14 | 15 |
| 20 to 40 | 1.5 | 21 | 22 | 23 | 24 | 25 |
| 40 to 80 | 2.0 | 31 | 32 | 33 | 34 | 35 |
| 80 to 160 | 2.5 | 41 | 42 | 43 | 44 | 45 |
| > 160 | 3.0 | 51 | 52 | 53 | 54 | 55 |

**Table 21 — Assignment of Fragility and Vulnerability weights according
to the colors.** Prepared by the author.

| Color | Fragility/Vulnerability |
|---|---|
| Dark green | Very Weak |
| Light green | Weak |
| Yellow | Medium |
| Orange | Strong |
| Red | Very Strong |

The Interfluve Dimension ranges in the two tables are the same ones used
in the reclassification of script 2 (`REMAP_FRAGILIDADE` and
`REMAP_VULNERABILIDADE`), and the Incision ranges are those of script 1
(`REMAP_ENTALHAMENTO`).

### `scripts/arcgis_pro/3_Grau de Dissecacao_ArcPRO.py` (ArcGIS Pro)

- **Working folder/GDB (created automatically):**
  `C:\alexgeopro\GrauDeDissecacao.gdb`
- **Default locations the script looks in by itself:**
  `C:\alexgeopro\Entalhamento.gdb\i_EntalhamentoRecla`,
  `C:\alexgeopro\DimensaoInterfluvial.gdb\l_DimensaoReclaFrag` and
  `l_DimensaoReclaVul`.
- **Outputs** (inside the geodatabase above): `b_GrauDeDissecacao_Fragilidade`
  and `b_GrauDeDissecacao_Vulnerabilidade`.

### `scripts/qgis/3_grau_de_dissecacao_QGIS.py` (QGIS, free software)

- **Working folder (created automatically):**
  `C:\alexgeopro\GrauDeDissecacao_QGIS`, with the `a_`/`b_` rasters (and
  some intermediate aligned grids, prefix `_`) as loose `.tif` files
  inside it.
- **Default locations the script looks in by itself:**
  `C:\alexgeopro\Entalhamento_QGIS\i_EntalhamentoRecla.tif`,
  `C:\alexgeopro\DimensaoInterfluvial_QGIS\l_DimensaoReclaFrag.tif` and
  `l_DimensaoReclaVul.tif`.
- **Final outputs:** the same two as above, as `.tif`.
- Difference from the ArcGIS Pro version: before adding, the three
  rasters are reprojected/resampled (nearest neighbor) onto one common
  reference grid (based on the boundary of the area of interest), since
  scripts 1 and 2 clip with different masks and rarely come out with the
  same pixel grid "out of the box". Details in the script header.

### `scripts/software_livre/3_grau_de_dissecacao_SoftwareLivre.py` (Python + GDAL/OGR, no QGIS)

Same logic as the QGIS version above, but with no dependency on QGIS — it
calls `gdal.Warp()`/`gdal.VectorTranslate()` directly instead of QGIS's
`gdal:warpreproject`/`native:reprojectlayer`/
`gdal:cliprasterbymasklayer` algorithms:

- **Working folder (created automatically):**
  `C:\alexgeopro\GrauDeDissecacao_SemQGIS`.
- **Default locations the script looks in by itself:**
  `C:\alexgeopro\Entalhamento_SemQGIS\i_EntalhamentoRecla.tif`,
  `C:\alexgeopro\DimensaoInterfluvial_SemQGIS\l_DimensaoReclaFrag.tif` and
  `l_DimensaoReclaVul.tif` — that is, by default this version expects
  the outputs of the "no QGIS" versions of scripts 1 and 2 (not those of
  the QGIS version). If you ran scripts 1/2 in the QGIS version, just
  enter the correct path on screen when asked.
- **Final outputs:** the same as always, as `.tif`.
- Runs on any ordinary Python installation with `gdal` and `numpy`
  installed (scipy/scikit-image are not needed) — just run `python
  "3_grau_de_dissecacao_SoftwareLivre.py"` in an ordinary terminal.

Both final indices represent the two Geomorphology indices of the
Environmental Fragility/Vulnerability model (Tricart).

## Environmental Fragility (*Fragilidade Ambiental*)

Generates the Environmental Fragility map (Chapter 6.6.2 of the thesis) by
adding, pixel by pixel, four thematic rasters — each one already
multiplied by the "decimal place" that belongs to it, so that the final
value is a **four-digit matrix**:

| Digit | Theme | How it is obtained | Values |
|---|---|---|---|
| 1st (thousands) | Relief | Dissection Degree (script 3) reclassified into fragility | 1000 to 5000 |
| 2nd (hundreds) | Soils | `Frag` field of the pedological map × 100 | 100 to 500 |
| 3rd (tens) | Land Use and Land Cover | MapBiomas reclassified by Table 24 (below) | 10 to 50 |
| 4th (units) | Climate | `Fragilidade` field of the WorldClim climate vector | 1 to 5 |

`1111` is the lowest possible fragility and `5555` the highest. Urban
areas receive the digit **7** and water bodies the digit **9**, in any of
the variables (e.g. urban use = `70`, water = `90` in the tens digit).
For example, `3152` = relief of medium fragility (3), soil of very weak
fragility (1), land use of very high fragility (5) and climate of weak
fragility (2). These soil values (7 and 9) and the climate values already
come from the input data — the script only adds them up.

**Scope of this version.** Only the **WorldClim** climate data are used
(an already classified vector, `Fragilidade` field, produced by the
procedure of Chapter 6.4 of the thesis — Tables 13 and 22). The other
model, which lets you choose among seven climate classifications
(WorldClim + INMET normals by IDW and kriging) and required two chained
`Iterate` tools, **was not adapted** here. *Potential* and *Emergent
Environmental Fragility* (Chapters 6.6.2.1 and 6.6.2.2, Tables 25 and
26), which start from the 4-digit matrix generated by this script, are
also a different tool, not converted yet.

**Inputs (asked on screen at run time):**

- **Dissection Degree – Fragility** (`b_GrauDeDissecacao_Fragilidade`,
  output of script 3): the script looks for it by itself in the default
  location of the corresponding version and only asks if it cannot find
  it. In the original model, this stage started from the *continuous*
  incision and dimension rasters and redid the two reclassifications and
  the sum; since that is exactly what script 3 already does, here
  script 4 reuses its result (and then only applies the reclassification
  of the 25 combinations `11`–`55` into relief fragility 1000–5000).
- **Pedological map:** vector (e.g. `PEDOLOGICO_SP_ROSSI_2017_V4`) with
  the `Frag` field.
- **Already classified climate vector:** WorldClim (e.g. `wc21_Br`) with
  the `Fragilidade` field.
- **Land Use and Land Cover (MapBiomas):** a single raster, or a
  folder/geodatabase with **one raster per year** — it replaces the
  model's *Iterate Rasters*: the script generates one result
  `c_<raster name>_FRAGILIDADE_FINAL` for each raster. You can limit
  which rasters are included with the `FILTRO_NOME_USO` constant.
- **Vector boundary** of the area of interest.

**Table 24 — Fragility (and Vulnerability) weights of Land Use and Land
Cover, MapBiomas collection 8** (only the classes that occur in the
State of SP). The "Value in script" column = fragility × 10 (tens digit
of the matrix). Class names are the English names used by MapBiomas:

| Code | Class | Fragility | Vulnerability | Value in script |
|---:|---|:---:|:---:|:---:|
| 3 | Forest Formation | 1 | 1.6 | 10 |
| 4 | Savanna Formation | 2 | 2.1 | 20 |
| 5 | Mangrove | 1 | 1.4 | 10 |
| 49 | Wooded Sandbank Vegetation | 1 | 1.4 | 10 |
| 12 | Grassland | 2 | 2.7 | 20 |
| 50 | Herbaceous Sandbank Vegetation | 2 | 2.7 | 20 |
| 11 | Wetland | 5 | 3.0 | 50 |
| 32 | Hypersaline Tidal Flat | 5 | 3.0 | 50 |
| 29 | Rocky Outcrop | 5 | 3.0 | 50 |
| 13 | Other Non-Forest Natural Formation | 5 | 3.0 | 50 |
| 15 | Pasture | 3 | 2.8 | 30 |
| 19 | Temporary Crop | 5 | 3.0 | 50 |
| 39 | Soybean | 4 | 3.0 | 40 |
| 20 | Sugar Cane | 4 | 3.0 | 40 |
| 62 | Cotton | 4 | 3.0 | 40 |
| 41 | Other Temporary Crops | 5 | 3.0 | 50 |
| 46 | Coffee | 3 | 2.9 | 30 |
| 47 | Citrus | 3 | 2.9 | 30 |
| 48 | Other Perennial Crops | 4 | 2.9 | 40 |
| 9 | Forest Plantation | 3 | 2.9 | 30 |
| 21 | Mosaic of Uses | 5 | 3.0* | 50 |
| 23 | Beach, Dune and Sand Spot | 5 | 3.0* | 50 |
| 25 | Other Non-Vegetated Area | 5 | 3.0* | 50 |
| 30 | Mining | 5 | 3.0* | 50 |
| 33 | River, Lake and Ocean | 5* | 3.0* | **90** (water) |
| 31 | Aquaculture | 5* | 3.0* | **90** (water) |
| 24 | Urban Infrastructure | — | — | **70** (urban) |
| 0 | No Information | — | — | **90** (as in the model) |

\* Maximum value assigned because of the absence (or indefiniteness) of
vegetation cover. Urban (7) and water (9) do not receive a weight in the
thesis table: they are marked with these digits so that they stand out in
the matrix. The Vulnerability column is not used by this script (it is
the one of script 5, Environmental Vulnerability). Classes that are
**not** in this table (for example those that do not occur in SP) become
*NoData* in the result — the script warns on screen when it finds any.
This differs from the original model's `Reclassify` with the `DATA`
option, which would keep the original class code (adding a meaningless
number to the matrix).

**How the script prepares each theme:**

- Soils and climate: vector → SIRGAS 2000 geographic → ~30 m raster
  (0.00027777778°) from the fragility field.
- Land use: raster → SIRGAS 2000 geographic → nearest neighbor onto the
  relief grid → reclassification by Table 24.
- Final result clipped by the exact outline of the area boundary.

**Resuming long runs.** Since there are up to 38 years (1985–2022), if the
script is interrupted just run it again: by default
(`SOBRESCREVER = False`) it skips the years whose result already exists.
The intermediate rasters of each year are deleted at the end of that year
(`MANTER_INTERMEDIARIOS = False`) to save disk space.

### `scripts/arcgis_pro/4_FragilidadeAmbiental_ArcPRO.py` (ArcGIS Pro)

- **Working folder/GDB (created automatically):**
  `C:\alexgeopro\FragilidadeAmbiental.gdb`
- **Default location the script looks in by itself:**
  `C:\alexgeopro\GrauDeDissecacao.gdb\b_GrauDeDissecacao_Fragilidade`.
- **Outputs** (inside the geodatabase): `a_FragilidadeFinal` (Relief +
  Soils + Climate, still without land use — digits 1, 2 and 4, with 0 in
  the tens place) and one `c_<name>_FRAGILIDADE_FINAL` per land use
  raster (the complete 4-digit matrix).
- Differences from the model: the 2 km buffer now uses the geodesic
  method (the model used planar, on geographic data) and is dissolved
  into a single feature; vectors are only reprojected if they are not
  already in SIRGAS 2000; *Iterate Rasters* accepts a single raster, a
  folder or a geodatabase (the MapBiomas `.gdb` works directly here).
- Requires the Spatial Analyst extension.

### `scripts/qgis/4_FragilidadeAmbiental_QGIS.py` (QGIS, free software)

- **Working folder (created automatically):**
  `C:\alexgeopro\FragilidadeAmbiental_QGIS`, with the rasters as loose
  `.tif` files and one `.gpkg` for each reprojected vector layer.
- **Default location the script looks in by itself:**
  `C:\alexgeopro\GrauDeDissecacao_QGIS\b_GrauDeDissecacao_Fragilidade.tif`.
- **Outputs:** `a_FragilidadeFinal.tif` and
  `c_<name>_FRAGILIDADE_FINAL.tif` for each land use raster.
- Difference from the ArcGIS Pro version: each dataset is taken directly
  onto the relief raster grid (vectors with `gdal.Rasterize` — called
  directly on the GDAL library, because QGIS's `gdal:rasterize` algorithm
  can fail silently in *headless* mode —, land use with
  `gdal:warpreproject` using nearest neighbor), so the 2 km buffer and
  the model's intermediate clips are no longer needed; the sums are done
  in blocks of rows with numpy, so as not to load the whole State into
  memory.
- **MapBiomas must be provided as GeoTIFF** (one per year, in a folder):
  QGIS/GDAL cannot read rasters inside a `.gdb` geodatabase (in
  ArcGIS Pro: *Copy Raster*).
- It follows the same pattern as the other QGIS scripts (relaunches
  itself with QGIS's Python, works in *headless* mode, one `.gpkg` per
  layer).

### `scripts/software_livre/4_FragilidadeAmbiental_SoftwareLivre.py` (Python + GDAL/OGR, no QGIS)

Same logic as the QGIS version above, but with no dependency on QGIS — it
calls `gdal.Warp()`/`gdal.Rasterize()`/`gdal.VectorTranslate()`
directly:

- **Working folder (created automatically):**
  `C:\alexgeopro\FragilidadeAmbiental_SemQGIS`.
- **Default location the script looks in by itself:**
  `C:\alexgeopro\GrauDeDissecacao_SemQGIS\b_GrauDeDissecacao_Fragilidade.tif`
  (output of the "no QGIS" version of script 3; if you ran script 3 in
  another version, enter the path on screen).
- **Final outputs:** the same as the QGIS version.
- Runs on any ordinary Python installation with `gdal` and `numpy`
  installed — just run `python "4_FragilidadeAmbiental_SoftwareLivre.py"`
  in an ordinary terminal. Vectors inside a `.gdb` (e.g.
  `C:\dados\GDB Final.gdb\Camada`) are accepted; the MapBiomas raster,
  however, must be a GeoTIFF.

**Note on the MapBiomas value `0`.** In ArcGIS, the value `0` (the "no
information" class) goes into the reclassification and becomes `90`. In
the QGIS and no-QGIS versions, if the GeoTIFF declares `0` as *NoData*
(which is common), those pixels end up with no value in the result
instead of becoming `90`. Inside a boundary such as that of the State of
SP this hardly affects anything, but it is worth knowing when comparing
the results of the versions.

## Environmental Vulnerability (*Vulnerabilidade Ambiental*)

Generates the Environmental Vulnerability map (Chapter 6.6.1 and Figure 11
of the thesis; methodology of Crepani et al., 1996 and 2001). Unlike
Fragility (which adds digits), vulnerability is the **arithmetic mean,
pixel by pixel, of five themes** — each one already expressed as a
vulnerability degree from **1.0** (most stable, pedogenesis) to **3.0**
(most unstable, morphogenesis):

| Theme | How it is obtained (thesis) | Weight |
|---|---|---|
| Relief | `R = (G + A + D) / 3` — G: dissection (interfluve amplitude, Table 7), A: altimetric amplitude (Table 8) and D: clinography/slope (Table 9) | Tables 7, 8 and 9 |
| Soils | IAC pedological map (Rossi, 2017), 27 classes | Table 18 |
| Geology | CPRM lithological units (Peixoto, 2010); the lithotype of **highest** vulnerability when there is more than one | Table 10 (Crepani) and Table 52 (thesis appendix) |
| Climate | Rainfall intensity (annual rainfall ÷ seasonal distribution) | Table 14 |
| Land Use and Land Cover | MapBiomas collection 8, one raster per year (1985–2022) | Table 24 |

**Raster scale: vulnerability × 10.** In the model, everything is written
with vulnerability multiplied by 10 (1.6 → `16`; 3.0 → `30`): the land
use reclassification table and the *Calculate Field* of the geology,
soils and climate fields. The script does these multiplications by
itself — **the vector fields must be from 1.0 to 3.0**, and the script
shows the distinct values (already × 10) of each one and warns if they
seem to be outside what is expected (for example, if the field is already
multiplied by 10). At the end it also shows the minimum and maximum of
each theme. The result lies between 10 and 30, plus the values **70**
(urban area) and **90** (water) in the products that overlay those
classes.

**Three products** (as in the thesis, pp. 86–87):

| Product | Output | What it is |
|---|---|---|
| Without land use | `h_Vuln_CellStatisticNoDataGRSC_noLanduse` | Mean of Geology, Relief, Soils and Climate — natural factors only (GRSC = Geology, Relief, Soils, Climate) |
| With land use, urban/water left out of the mean | `h_Vuln_CellStatisticNoData_<land use raster name>` | Mean of the five themes; urban and water from land use become *NoData* (in those pixels the mean comes from the other four) |
| With land use, urban/water as a mask | `h_Vuln_CellStatisticNoDataUrbAgua_<land use raster name>` | Same as the previous one, with urban (`70`) and water (`90`) overlaid as a mask. It allows studying, for example, at which vulnerability levels the urban area expands |

**Why *NoData* and not the relief value.** The thesis (p. 85) reports
that it tested assigning the relief vulnerability to water areas
(geology and pedology) and urban areas (pedology), but adopted *NoData*:
*Cell Statistics* only counts cells that have a value in the mean, which
avoids weighting relief twice or three times. Example from the thesis:
where soils and geology are "water", the vulnerability is the mean of
land use, relief and climate.

**Inputs.** The script follows the complete model of the thesis (Figure
11; export `5_VulnerabilidadeAmbiental_Arc103_V6_completa.py`, which
corresponds to *Modelo Geral_VulnerabilidadeV6*, the **V6** model of the
toolbox): it starts from the raw data and builds the four natural
themes. The inputs are:

- **DEM** (`mosaico.tif`): basis of the slope and **reference grid** of
  everything else (SIRGAS 2000 geographic, cell of 0.00027777778° ≈ 30 m,
  bilinear interpolation, as in the model).
- **Valley Incision** (`h_entalhamento`) and **Mean Interfluve Dimension**
  (`j_Dimensao`): **continuous outputs, in meters, of scripts 1 and 2**
  (not the reclassified ones). The script looks in the default locations
  of each version and, if it does not find them, asks.
- **Geology vector** (field `Vulnerabil`), **soils vector** (field
  `Vulne`) and **climate vector** (field `Vulnerabilidade`), with
  vulnerability from **1.0 to 3.0** (water = 9 and urban = 7 in the
  geology and soils fields, which become 90 and 70 after the × 10).
  Vectors inside a `.gdb` work in all three versions (e.g.
  `C:\dados\GDB Final.gdb\Vulnerabilidade_Final`). If the field in your
  data has another name, adjust `CAMPO_GEOLOGIA`, `CAMPO_SOLOS` or
  `CAMPO_CLIMA` at the top of the script. In the model, the thesis
  generates **seven** versions of the climate (WorldClim; kriging of the
  INMET normals 1961–1990, 1981–2010 and 1991–2020; IDW of the same three
  periods): the script does not choose — just point to the vector of the
  version you want (the exported model uses `Vuln_wc21_30s_Brasil`, from
  WorldClim).
- **Land Use and Land Cover:** a single raster, or a folder/geodatabase
  with **one raster per year** (replaces the model's *Iterate Rasters*).
  You can limit which rasters are included with `FILTRO_NOME_USO`.
- **Vector boundary** of the area of interest.

**How each theme is built** (Chapter 6.6.1 and the model):

| Theme | Construction | Output |
|---|---|---|
| Relief | Incision → Table 8; Interfluve Dimension → Table 7; DEM slope (%) → Table 9 (Z factor `0.00000956`). Each is reclassified into 21 classes (10 to 30) and the Relief is the **mean of the three** — in the model: class ÷ 10, sum ÷ 3, × 10 (equivalent) | `rel_e2_Relevo` |
| Geology | Field `Vulnerabil` × 10 → raster on the relief grid. Water (90) → *NoData* | `geol_d2_Rochas` |
| Soils | Field `Vulne` × 10 → raster. Urban (70) and water (90) → *NoData* | `ped_d2_solos` |
| Climate | Field `Vulnerabilidade` × 10 → raster | `cli_c_clima` |

*About Tables 7 and 8:* the text of section 6.6.1 cites the tables in the
order incision → Table 7, dimension → Table 8, but by the titles — and by
the exported model — it is the other way around (Table 7 = interfluve
amplitude = interfluve dimension; Table 8 = altimetric amplitude =
incision). **The vulnerability Relief is not the output of script 3**:
that one is the dissection degree in classes from 1 to 5 (qualitative
Fragility/Vulnerability); here the relief uses the continuous values from
1.0 to 3.0 of Tables 7 to 9, plus the slope.

**Ranges of Tables 7, 8 and 9.** The *Reclassify* ranges are at the top
of the script (`LIMITES_ENTALHAMENTO`, `LIMITES_DIMENSAO` and
`LIMITES_DECLIVIDADE`) and were checked one by one against the ArcMap
10.3 export — each class goes from `[previous limit, next limit)`. See
the three tables in the weights section further below.

**Important notes (differences from the exported model):**

- Land use classes that are **not** in Table 24 become *NoData* (the
  script warns), instead of keeping the original code (the behavior of
  the model's `Reclassify` with `DATA`, which would let the class number
  enter the mean). Code `0` (no information) becomes *NoData*, as in the
  model (`0 NODATA`).
- **Aquaculture (31) = 3.0** (value `30`, enters the mean) and only class
  33 (river, lake and ocean) becomes water (`90`) — as in the exported
  model and in Table 24 of the thesis. In the Fragility script, by
  contrast, 31 and 33 both become `90`.
- The "without land use" product (GRSC) is clipped by the exact boundary;
  in the exported model it was left without this final clip (the others
  had it).
- The *Mosaic To New Raster* (`FIRST`) that overlays urban/water on the
  mean is done in the ArcGIS Pro version with `Con(IsNull(...))`,
  equivalent for this case; in the free versions the overlay is done in
  the block-wise calculation itself.
- The result is *Float32* (the mean is not an integer).
- **Slope:** the model uses `Slope_3d` (3D Analyst extension), in percent
  and with Z factor `0.00000956`. The ArcGIS Pro version uses
  `arcpy.sa.Slope` (Spatial Analyst, same calculation, without needing
  3D Analyst) and the free versions use `gdal.DEMProcessing` (Horn
  algorithm, scale = 1 / Z factor ≈ 104,603 m per degree). The Z factor
  converts degrees into meters for the latitude of São Paulo; for another
  region, adjust `Z_FACTOR` at the top of the script.
- **Reference grid:** it is that of the projected DEM. Incision and
  Interfluve Dimension (which come from scripts 1 and 2, possibly on
  another grid) and all the other themes are resampled to it by nearest
  neighbor; where any one of the three relief components is missing, the
  relief becomes *NoData* (as in the *Raster Calculator*).
- **Extreme *Reclassify* ranges:** in the free versions the first and
  last ranges go to −∞ / +∞ (in the model: −5000 and 5000, 200000 or
  2000); this only changes values that are impossible in practice.
- **Clipped vectors:** the model clips the vectors by the 2 km buffer
  before projecting. In the free versions the grid already limits the
  area, so only the features that touch the grid are reprojected (much
  faster for the climate of the whole of Brazil).

**Resuming long runs.** With `SOBRESCREVER = False` the script reuses what
already exists: the themes `rel_e2_Relevo`, `geol_d2_Rochas`,
`ped_d2_solos` and `cli_c_clima` (useful to rerun only the land use part)
and the years whose two results are already done. The themes and the
three products are always kept; the other intermediates (projected DEM,
slope, clipped vectors, rasters of each year) are deleted
(`MANTER_INTERMEDIARIOS = False`).

### Starting from the four ready-made themes (model V7, simplified version)

The toolbox has two Vulnerability models: **V6** is the complete workflow,
which starts from the raw data (it is what scripts 5 implement), and
**V7** is the simplified version, which already receives the four natural
themes ready-made (`rel_e2_Relevo`, `geol_d2_Rochas`, `ped_d2_solos` and
`cli_c_clima`, all × 10, on the same grid) and only handles land use and
takes the means. V7 is useful when the themes already exist: redoing only
the land use part (for example, with another MapBiomas collection) or
swapping a single theme — such as the climate, which the thesis generates
in seven versions — without rebuilding the relief.

The scripts do not have a "V7 mode" of their own, but they can be used
this way:

1. Save the four themes in the script's output folder (or geodatabase),
   with exactly these names (`.tif` in the QGIS and no-QGIS versions) and
   leave `SOBRESCREVER = False`. The script finds each ready-made theme,
   **does not rebuild it** and goes straight to the means and land use.
   To redo only one of them, delete it from the folder before running.
2. The script still **asks** for the DEM, the rasters of scripts 1 and 2
   and the three vectors. Since these data will not be used (the themes
   already exist), just point to any valid raster or vector for each
   question.
3. The ready-made themes must be **as V7 expects them**: vulnerability
   × 10 (10 to 30); water (and urban, in the soils) already as *NoData*;
   same SIRGAS 2000 geographic. In the **QGIS and no-QGIS** versions the
   four themes must also have **exactly the same grid** (extent, size and
   position of the cells) — if they come from another source, the script
   stops with a warning that the rasters are not on the same grid. The
   ArcGIS Pro version aligns to the relief grid, but it is worth checking.

### `scripts/arcgis_pro/5_VulnerabilidadeAmbiental_ArcPRO_V6_completa.py` (ArcGIS Pro)

- **Working geodatabase (created automatically):**
  `C:\alexgeopro\VulnerabilidadeAmbiental.gdb`.
- **Asks on screen for:** DEM, the rasters of scripts 1 and 2 (it looks
  in `C:\alexgeopro\Entalhamento.gdb\h_entalhamento` and
  `C:\alexgeopro\DimensaoInterfluvial.gdb\j_Dimensao`), the geology, soils
  and climate vectors, land use (raster or geodatabase/folder) and the
  boundary.
- **Outputs:** the four themes (`rel_e2_Relevo`, `geol_d2_Rochas`,
  `ped_d2_solos`, `cli_c_clima`), `h_Vuln_CellStatisticNoDataGRSC_noLanduse`
  and, for each land use raster, `h_Vuln_CellStatisticNoData_<name>` and
  `h_Vuln_CellStatisticNoDataUrbAgua_<name>`.
- As in the other ArcGIS scripts, the 2 km (geodesic) buffer clips the
  vectors and land use, and the results are clipped by the exact
  boundary. It only needs the Spatial Analyst extension (not 3D Analyst).

### `scripts/qgis/5_VulnerabilidadeAmbiental_QGIS_V6_completa.py` (QGIS, free software)

- **Working folder (created automatically):**
  `C:\alexgeopro\VulnerabilidadeAmbiental_QGIS`.
- **Looks by itself for** `C:\alexgeopro\Entalhamento_QGIS\h_entalhamento.tif`
  and `C:\alexgeopro\DimensaoInterfluvial_QGIS\j_Dimensao.tif` (outputs of
  scripts 1 and 2 of this version).
- **Outputs:** the same as the ArcGIS version, in GeoTIFF (`.tif`,
  Float32, *NoData* −9999).
- All the raster processing (projecting the DEM, slope, aligning,
  rasterizing) is called **directly on the GDAL library** of QGIS's
  Python (not through the Processing `gdal:*` algorithms, which in
  *headless* mode can fail silently); the means are computed in blocks
  with numpy. QGIS is used to clip and reproject the vectors
  (`native:extractbyextent` and `native:reprojectlayer`).
- **MapBiomas must be provided as GeoTIFF** (one per year, in a folder).
- It follows the same pattern as the other QGIS scripts (relaunches
  itself with QGIS's Python, works in *headless* mode).

### `scripts/software_livre/5_VulnerabilidadeAmbiental_SoftwareLivre_V6_completa.py` (Python + GDAL/OGR, no QGIS)

Same logic as the QGIS version, with no dependency on QGIS:

- **Working folder (created automatically):**
  `C:\alexgeopro\VulnerabilidadeAmbiental_SemQGIS`; it looks for
  `C:\alexgeopro\Entalhamento_SemQGIS\h_entalhamento.tif` and
  `C:\alexgeopro\DimensaoInterfluvial_SemQGIS\j_Dimensao.tif`.
- **Outputs:** the same as the QGIS version.
- Runs on any ordinary Python installation with `gdal` and `numpy` —
  just run `python "5_VulnerabilidadeAmbiental_SoftwareLivre_V6_completa.py"`.
  Vectors in `.gdb` are accepted for reading; MapBiomas must be a
  GeoTIFF.

**About the tests.** The **QGIS** (QGIS 3.34 in *headless* mode) and
**no-QGIS** (GDAL 3.8) versions were run end to end with synthetic data
(DEM, incision, dimension, three vectors, two land use rasters with
different resolution and origin, and a boundary), and every pixel of the
results was compared with an independent calculation: relief (Horn
slope, ranges and mean), vector themes, the two products of each year and
the product without land use — with no differences. The range tables
(Tables 7, 8 and 9) and the land use reclassification table were compared
programmatically with the ArcMap 10.3 export in all three versions. The
**ArcGIS Pro version was not run** (the environment where it was written
has no `arcpy`): it uses the same ranges and the same logic as the
others, but only running it with your data will confirm it. None of the
three has been run with the real data of the thesis.

## Fragility and Vulnerability weights (thesis tables)

The weights below come from the tables of Chapter 5.4 (theoretical
background) and Chapter 6 (application) of the thesis. Fragility follows
Ross (1994, 2012), in classes from 1 (very weak) to 5 (very strong);
Vulnerability follows Crepani et al. (1996, 2001), from 1.0 (stable) to
3.0 (unstable). They are already built into the input data (soils,
geology, climate) or into the reclassification tables of the scripts
(relief and land use) — this section only documents where they come
from.

### Soils — Table 18 (Rossi, 2017, adapted)

Values stored in the pedological map (fragility and vulnerability fields);
script 4 reads the fragility (field `Frag`) and script 5 reads the
vulnerability (field `Vulne`) and multiplies it by 10 (raster
`ped_d2_solos`). The soil class names are the official Brazilian soil
classification (SiBCS) names and are kept in Portuguese, as they appear
in the pedological map; the codes are those of the map.

| Class | Code | Fragility | Vulnerability |
|---|---|:---:|:---:|
| Afloramento Rochoso | AF | *5 | 3.0 |
| Argissolos | PA | 3 | 2.0 |
| Argissolos Vermelhos | PV1 to PV12 | 3 | 2.0 |
| Argissolos Vermelho-Amarelos | PVA1 to PVA44 | 3 | 2.0 |
| Cambissolos Húmicos | CH1 to CH4 | 4 | 2.5 |
| Cambissolos Háplicos | CX1 to CX24 | 4 | 2.5 |
| Chernossolos Argilúvicos | MT1 to MT6 | *1 | 2.0 |
| Espodossolos | EK | 5 | 2.0 |
| Gleissolos Tiomórficos | GJ | 5 | 3.0 |
| Gleissolos Sálicos | GZ | 5 | 3.0 |
| Gleissolos Melânicos | GM1 to GM3 | 5 | 3.0 |
| Gleissolos Háplicos | GX1 to GX12 | 5 | 3.0 |
| Latossolos Brunos | LB1 to LB3 | 1 | 1.0 |
| Latossolos Amarelos – Férricos | LA1 to LA5 | 2 | 1.0 |
| Latossolos Amarelos – Não Férricos | LA6 to LA13 | 2 | 1.0 |
| Latossolos Vermelhos – Férricos | LV1 to LV18 | 1 | 1.0 |
| Latossolos Vermelhos – Não Férricos | LV19 to LV31 | 1 | 1.0 |
| Latossolos Vermelho-Amarelos | LVA1 to LVA20 | 1 | 1.0 |
| Luvissolos Háplicos | TX1 to TX5 | *4 | 2.0 |
| Neossolos Litólicos | RL1 to RL26 | 5 | 3.0 |
| Neossolos Flúvicos | RY1 to RY3 | 5 | 3.0 |
| Neossolos Quartzarênicos | RQ1 to RQ8 | 5 | 3.0 |
| Nitossolos Vermelhos | NV1 to NV16 | 3 | 2.0 |
| Organossolos Tiomórficos | OJ1 to OJ2 | 5 | 3.0 |
| Organossolos Háplicos | OX1 to OX4 | 5 | 3.0 |
| Planossolos Háplicos | SX1 to SX4 | *4 | 2.0 |
| Plintossolos Pétricos | FF1 to FF2 | *2 | 3.0 |

\* Afloramento Rochoso (rock outcrop): Crepani considers the vulnerability
"High" (beginning of soil formation) and the same criterion was adopted
for fragility. Chernossolos Argilúvicos: developed textural B horizon,
suitable for agriculture (very low fragility). Luvissolos Háplicos: areas
with water deficit, a lot of clay, shallow, used for pasture (high
fragility). Planossolos Háplicos: hydromorphic soil, used for pasture and
rice growing (high fragility). Plintossolos Pétricos: poor for
agriculture, good for roads, already hardened and well-drained soils (low
fragility).

The classes "Urban Area" and "Rivers, reservoirs and lagoons" received,
in the soil map, separate values so that they would not receive a wrong
weight. In Fragility they appear as the digits 7 and 9; in Vulnerability
the model treats them as *NoData* (they leave the mean).

### Land Use and Land Cover — Table 24 (MapBiomas collection 8)

Only the classes present in the State of SP. "Script 4" = fragility × 10;
"Script 5" = vulnerability × 10 (as written in each model's
`Reclassify`). Classes from other regions of Brazil are not in the
scripts' tables and become *NoData* (the script warns).

| Code | Class | Fragility | Vulnerability | Script 4 | Script 5 |
|---:|---|:---:|:---:|:---:|:---:|
| 3 | Forest Formation | 1 | 1.6 | 10 | 16 |
| 4 | Savanna Formation | 2 | 2.1 | 20 | 21 |
| 5 | Mangrove | 1 | 1.4 | 10 | 14 |
| 49 | Wooded Sandbank Vegetation | 1 | 1.4 | 10 | 14 |
| 11 | Wetland | 5 | 3.0 | 50 | 30 |
| 12 | Grassland | 2 | 2.7 | 20 | 27 |
| 32 | Hypersaline Tidal Flat | 5 | 3.0 | 50 | 30 |
| 29 | Rocky Outcrop | 5 | 3.0 | 50 | 30 |
| 50 | Herbaceous Sandbank Vegetation | 2 | 2.7 | 20 | 27 |
| 13 | Other Non-Forest Natural Formation | 5 | 3.0 | 50 | 30 |
| 15 | Pasture | 3 | 2.8 | 30 | 28 |
| 19 | Temporary Crop | 5 | 3.0 | 50 | 30 |
| 39 | Soybean | 4 | 3.0 | 40 | 30 |
| 20 | Sugar Cane | 4 | 3.0 | 40 | 30 |
| 62 | Cotton | 4 | 3.0 | 40 | 30 |
| 41 | Other Temporary Crops | 5 | 3.0 | 50 | 30 |
| 46 | Coffee | 3 | 2.9 | 30 | 29 |
| 47 | Citrus | 3 | 2.9 | 30 | 29 |
| 48 | Other Perennial Crops | 4 | 2.9 | 40 | 29 |
| 9 | Forest Plantation | 3 | 2.9 | 30 | 29 |
| 21 | Mosaic of Uses | 5 | 3.0* | 50 | 30 |
| 23 | Beach, Dune and Sand Spot | 5 | 3.0* | 50 | 30 |
| 30 | Mining | 5 | 3.0* | 50 | 30 |
| 25 | Other Non-Vegetated Area | 5 | 3.0* | 50 | 30 |
| 24 | Urban Infrastructure | — | — | **70** | **70** |
| 33 | River, Lake and Ocean | 5* | 3.0* | **90** | **90** |
| 31 | Aquaculture | 5* | 3.0* | **90** | 30 |
| 0 | No Information | — | — | **90** | NoData |

\* Maximum value assigned because of the absence (or indefiniteness) of
vegetation cover. Urban and water do not receive a weight in the thesis
table: the scripts mark them with `70` and `90` so that they stand out
(in the Fragility matrix, and as a mask in the Vulnerability products).
Aquaculture differs between the two scripts because the exported models
treat the class differently (in the Vulnerability one, only class 33 is
water).

### Relief — Vulnerability (Tables 7, 8 and 9, Crepani et al., 2001)

Relief vulnerability is `R = (G + A + D) / 3` (Equation 1 of the thesis),
with G, A and D taken from the three tables below. Relief fragility comes
from the dissection degree (Tables 19 to 21 and script 3).

**Table 7 — Dissection intensity (interfluve amplitude, m):**

| Interfluve amplitude (m) | Vuln. | Interfluve amplitude (m) | Vuln. | Interfluve amplitude (m) | Vuln. |
|---|:---:|---|:---:|---|:---:|
| > 5,000 | 1.0 | 3,250 – 3,500 | 1.7 | 1,500 – 1,750 | 2.4 |
| 4,750 – 5,000 | 1.1 | 3,000 – 3,250 | 1.8 | 1,250 – 1,500 | 2.5 |
| 4,500 – 4,750 | 1.2 | 2,750 – 3,000 | 1.9 | 1,000 – 1,250 | 2.6 |
| 4,250 – 4,500 | 1.3 | 2,500 – 2,750 | 2.0 | 750 – 1,000 | 2.7 |
| 4,000 – 4,250 | 1.4 | 2,250 – 2,500 | 2.1 | 500 – 750 | 2.8 |
| 3,750 – 4,000 | 1.5 | 2,000 – 2,250 | 2.2 | 250 – 500 | 2.9 |
| 3,500 – 3,750 | 1.6 | 1,750 – 2,000 | 2.3 | < 250 | 3.0 |

**Table 8 — Altimetric amplitude (m):**

| Altimetric amplitude (m) | Vuln. | Altimetric amplitude (m) | Vuln. | Altimetric amplitude (m) | Vuln. |
|---|:---:|---|:---:|---|:---:|
| < 20 | 1.0 | 77 – 84.5 | 1.7 | 141.5 – 151 | 2.4 |
| 20 – 29.5 | 1.1 | 84.5 – 94 | 1.8 | 151 – 160.5 | 2.5 |
| 29.5 – 39 | 1.2 | 94 – 103.5 | 1.9 | 160.5 – 170 | 2.6 |
| 39 – 48.5 | 1.3 | 103.5 – 113 | 2.0 | 170 – 179.5 | 2.7 |
| 48.5 – 58 | 1.4 | 113 – 122.5 | 2.1 | 179.5 – 189 | 2.8 |
| 58 – 67.5 | 1.5 | 122.5 – 132 | 2.2 | 189 – 200 | 2.9 |
| 67.5 – 77 | 1.6 | 132 – 141.5 | 2.3 | > 200 | 3.0 |

**Table 9 — Clinography (slope):**

| In % | In degrees | Vuln. | In % | In degrees | Vuln. | In % | In degrees | Vuln. |
|---|---|:---:|---|---|:---:|---|---|:---:|
| < 2 | < 3.5 | 1.0 | 9.9 – 11.2 | 17.4 – 19.8 | 1.7 | 19.1 – 20.4 | 34.6 – 37.2 | 2.4 |
| 2 – 3.3 | 3.5 – 5.8 | 1.1 | 11.2 – 12.5 | 19.8 – 22.2 | 1.8 | 20.4 – 21.7 | 37.2 – 39.8 | 2.5 |
| 3.3 – 4.6 | 5.8 – 5.8 | 1.2 | 12.5 – 13.8 | 22.2 – 24.5 | 1.9 | 21.7 – 23.0 | 39.8 – 42.4 | 2.6 |
| 4.6 – 5.9 | 8.2 – 10.3 | 1.3 | 13.8 – 15.2 | 24.5 – 27.2 | 2.0 | 23.0 – 24.4 | 42.4 – 45.3 | 2.7 |
| 5.9 – 7.3 | 10.3 – 12.9 | 1.4 | 15.2 – 16.5 | 27.2 – 29.6 | 2.1 | 24.4 – 25.7 | 45.3 – 48.1 | 2.8 |
| 7.3 – 8.6 | 12.9 – 15.1 | 1.5 | 16.5 – 17.8 | 29.6 – 32.1 | 2.2 | 25.7 – 27.0 | 48.1 – 50.0 | 2.9 |
| 8.6 – 9.9 | 15.1 – 17.4 | 1.6 | 17.8 – 19.1 | 32.1 – 34.6 | 2.3 | > 27 | > 50 | 3.0 |

(Transcribed as it is in the thesis. In the row "3.3 – 4.6" the range in
degrees appears as "5.8 – 5.8", a probable typo — following the sequence
it should be "5.8 – 8.2". It is worth correcting in the thesis and
checking before using the table as a reference.)

### Geology — Table 10 (Crepani et al., 1996, 2001)

The thesis classifies **all the lithotypes of the State of SP** using
this scale (complete list in Table 52, in the appendix). Fragility does
not use lithology (Ross does not consider it directly); only
Vulnerability does.

| Vuln. | Rocks | Vuln. | Rocks | Vuln. | Rocks |
|:---:|---|:---:|---|:---:|---|
| 1.0 | Quartzites or metaquartzites | 1.7 | Mylonites, quartz-muscovite, biotite, chlorite schist | 2.4 | Quartz sandstones or orthoquartzites |
| 1.1 | Rhyolite, granite, dacite | 1.8 | Pyroxenite, amphibolite, kimberlite, dunite | 2.5 | Conglomerates, subgraywackes |
| 1.2 | Granodiorite, quartz-diorite, granulites | 1.9 | Hornblende, tremolite, actinolite schist | 2.6 | Graywackes, arkoses |
| 1.3 | Migmatites, gneisses | 2.0 | Staurolite schist, garnet schists | 2.7 | Siltstones, claystones |
| 1.4 | Phonolite, nepheline syenite, trachyte, syenite | 2.1 | Phyllite, metasiltstone | 2.8 | Shales |
| 1.5 | Andesite, diorite, basalt | 2.2 | Slate, meta-argillite | 2.9 | Limestones, dolomites, marls, evaporites |
| 1.6 | Anorthosite, gabbro, peridotite | 2.3 | Marbles | 3.0 | Unconsolidated sediments: alluvium, colluvium, etc. |

### Climate

**Fragility — Table 22** (Annual rainfall × seasonal distribution,
adapted from Ross, 2012; values marked with \* were adapted by the author
to smooth the transition between Ross's values). It is the matrix that
generates the `Fragilidade` field (1 to 5) of the climate vector of
script 4:

| Annual rainfall (mm) \ Rainy months | 8 | 9 | 10 | 11 | 12 |
|---|:---:|:---:|:---:|:---:|:---:|
| < 900 | 5 | 5 | 5 | 5 | 5 |
| 1000 | 5\* | 4\* | 4\* | 3\* | 3\* |
| 1300 | 4\* | 3\* | 3\* | 1 | 1 |
| 1600 | 4\* | 3 | 3 | 1\* | 1\* |
| 1800 | 4 | 4 | 3\* | 1\* | 1\* |
| 2000 | 5\* | 4\* | 3\* | 1\* | 1\* |
| 2500 | 5\* | 5\* | 4\* | 2 | 2 |
| > 2500 | 5 | 5 | 5 | 5 | 5 |

**Vulnerability — Table 14** (rainfall intensity in mm/month = annual
rainfall ÷ seasonal distribution, Crepani et al., 2001):

| Intensity (mm/month) | Vuln. | Intensity (mm/month) | Vuln. | Intensity (mm/month) | Vuln. |
|---|:---:|---|:---:|---|:---:|
| < 50 | 1.0 | 200 – 225 | 1.7 | 375 – 400 | 2.4 |
| 50 – 75 | 1.1 | 225 – 250 | 1.8 | 400 – 425 | 2.5 |
| 75 – 100 | 1.2 | 250 – 275 | 1.9 | 425 – 450 | 2.6 |
| 100 – 125 | 1.3 | 275 – 300 | 2.0 | 450 – 475 | 2.7 |
| 125 – 150 | 1.4 | 300 – 325 | 2.1 | 475 – 500 | 2.8 |
| 150 – 175 | 1.5 | 325 – 350 | 2.2 | 500 – 525 | 2.9 |
| 175 – 200 | 1.6 | 350 – 375 | 2.3 | > 525 | 3.0 |

## Requirements

**ArcGIS Pro scripts** (folder `scripts/arcgis_pro/`):
- ArcGIS Pro with `arcpy`
- Extensions: Spatial Analyst (all) and 3D Analyst (script 2, because of
  Add Surface Information)

**QGIS scripts** (folder `scripts/qgis/`, free versions):
- QGIS 3.x installed (it already ships GDAL, numpy and the `processing`
  framework)
- `scipy` and `scikit-image` inside QGIS's Python, needed by scripts 1
  and 2 (scripts 3 and 4 do not need them) — on Windows, open the
  "OSGeo4W Shell" (installed together with QGIS), type `py3_env` and then
  `python -m pip install scipy scikit-image` (only once)
- Run it any way you like, including the "Run" button of an ordinary
  editor (e.g. VS Code): all the QGIS scripts detect by themselves if
  they are not running with QGIS's Python and, if so, look for the
  installed `python-qgis.bat` (in any folder `C:\Program Files\QGIS
  <version>\bin\`, without needing to know the exact version) and
  relaunch themselves automatically with it — nothing to do manually in
  most cases.
- You can also run it from inside QGIS (Python Console > Script Editor >
  open the file and click "Run Script"), or directly from the terminal
  (Command Prompt/PowerShell) pointing to `python-qgis.bat` manually, for
  example:

  ```
  "C:\Program Files\QGIS 3.34\bin\python-qgis.bat" "C:\path\to\1_Entalhamento do Vale_QGIS.py"
  ```

  All of these modes still require QGIS to be installed on the machine
  (that is where `qgis.core`/`processing` come from underneath) — you just
  do not need to open the program. If the script cannot find
  `python-qgis.bat` by itself (installation in an unusual location), it
  warns you and you can run it manually pointing to the right path, as in
  the example above, or adjust the `CAMINHO_INSTALACAO_QGIS` constant at
  the top of each script.

**No-QGIS scripts** (folder `scripts/software_livre/`, free versions,
100% independent of QGIS):
- No GIS program needs to be installed — only the Python packages: `gdal`
  (`osgeo`), `numpy` and, for scripts 1 and 2, also `scipy` and
  `scikit-image`.
- Simplest installation: using conda —
  `conda install -c conda-forge gdal numpy scipy scikit-image` (only
  once; the plain PyPI `gdal` package is usually harder to compile on
  Windows, so conda-forge is the easiest path).
- Run: `python "1_Entalhamento do Vale_SoftwareLivre.py"` (and the
  equivalents) in an ordinary terminal, inside the environment where the
  packages above are installed.

## Before running

The scripts numbered 1 to 5 in the three folders (`scripts/arcgis_pro/`,
`scripts/qgis/` and `scripts/software_livre/`) already create the working
folder/GDB (or ordinary folder, in the QGIS/no-QGIS versions) by
themselves and ask for the input data on screen at run time (scripts 3
still try to find by themselves, in the default locations, the rasters
generated by scripts 1 and 2; scripts 4 the raster generated by script 3;
and scripts 5 also look for the outputs of scripts 1 and 2 and ask for
the DEM, the geology, soils and climate vectors, land use and the
boundary) — there is no need to edit anything in them before running.

## Methodological transparency note

When checking the script `1_Entalhamento do Vale_ArcPRO.py` against the
native ArcMap 10.3 export, we identified a translation flaw of the ArcMap
exporter itself (not of the model): the variable that the Eliminate tool
uses as input, generated automatically for the "derived output" of a
previous Select Layer By Location, is never correctly reassigned in the
exported script — it inherits a value from another element of the model
with no logical relation to the actual data flow. This is a known
limitation of ArcMap's Model→Python exporter for tools that change the
selection "in place" (Select Layer By Attribute, Select Layer By
Location, Add Join, etc.), not an error in how the model was built — run
inside ModelBuilder/ArcMap itself (which is what produced the results
published in the thesis), the data flow is correct, because the
ModelBuilder execution engine tracks the real connections of the diagram
internally. The Python script here already includes this correction.

This remark applies to the ArcGIS Pro version
(`1_Entalhamento do Vale_ArcPRO.py`). In the QGIS version
(`1_Entalhamento do Vale_QGIS.py`), the Fill/Flow Direction/Sink/Basin
stage was rewritten as a single routine in numpy/scipy/scikit-image
(instead of chaining QGIS SAGA/GRASS tools, whose names and parameters
vary between versions) — as a consequence, the iterative Eliminate
cleanup is no longer needed: the method used there (watershed) always
assigns each pixel to some zone/peak, without generating orphan
fragments. The details of this adaptation are in the header of the
script itself.

When actually running `1_Entalhamento do Vale_QGIS.py` in headless mode
(`python-qgis.bat`), one more real problem appeared, also fixed: the
intermediate vector layers (`a_limite_Proj` and `a_limite_Proj_Buffer`)
were originally stored inside a single shared GeoPackage, addressed as
`Entalhamento.gpkg|layername=a_limite_Proj`. In that mode, the
`processing` algorithm sometimes does not interpret this syntax as "open
the existing GeoPackage and add this layer" — it treats the whole string
as the literal name of a new datasource, and fails with
`sqlite3_open(...) failed: unable to open database file`. The fix was to
give each layer its own `.gpkg`, instead of several layers inside one
shared `.gpkg`.

## History

See the commit history of this repository to follow changes over time,
instead of duplicating files with suffixes such as `_v2`, `_FINAL`,
`_PRO`.
