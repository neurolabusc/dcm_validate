[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.15310657.svg)](https://doi.org/10.5281/zenodo.15310934)

# dcm_validate

The `dcm_validate` repository serves as a centralized collection of all `dcm_qa` repositories. Each `dcm_qa` repository provides concise, illustrative examples of specific DICOM image file features. This repository acts as an index, bringing together these independent modules for easier access and management.

## Installation

To clone this repository and initialize all submodules, use the following commands:

```bash
git clone --recursive https://github.com/neurolabusc/dcm_validate.git
```

## Cataloging System

This repository includes a comprehensive cataloging system to help explore and analyze the DICOM datasets. The system consists of three main scripts and interactive exploration tools.

### Creating a Catalog Table for DICOM series

The `catalog_dicoms.py` script recursively scans a folder for DICOM files and generates a CSV table summarizing the value of a specified DICOM tag. Since a single DICOM series typically consists of multiple files, the script includes only one representative file per series, determined by the SeriesInstanceUID (0020,000E).

**Basic usage** to list the manufacturer (0008,0070) for each series:

```bash
python catalog_dicoms.py ./dcm_qa 0008,0070
```

**Additional options:**

```bash
# Use absolute paths instead of relative
python catalog_dicoms.py ./dcm_qa 0008,0070 --absolute-paths

# Specify custom output file
python catalog_dicoms.py ./dcm_qa 0008,0070 --out my_catalog.csv

# Enable verbose error messages
python catalog_dicoms.py ./dcm_qa 0008,0070 --verbose
```

Note that some DICOM attributes may vary across files within the same series. This script reports the value from the first file encountered per series. You can modify the script to suit custom requirements, or alternatively use tools like dcmdump or gdcmdump for more advanced queries.

### Creating a Catalog Table for BIDS JSON images

The `catalog_datasets.py` script helps identify imaging series that match specific criteria. For instance, you can list properties such as Manufacturer, BodyPart, PatientAge, and EchoTime for each series.

**Two-step workflow** (recommended for exploring available fields):

```bash
# Step 1: Generate field list template
python catalog_datasets.py
# Generating field list file: catalog_fields.txt
# Edit the field list and re-run this script, or use --fields option.

# Step 2: Edit catalog_fields.txt to select desired fields, then re-run
python catalog_datasets.py
```

**Direct field selection** (bypass field file):

```bash
# Specify fields directly on command line
python catalog_datasets.py --fields Manufacturer,Modality,EchoTime

# Catalog a specific dataset
python catalog_datasets.py dcm_qa_12bit --fields Manufacturer,Modality
```

**Additional options:**

```bash
# Use absolute paths instead of relative
python catalog_datasets.py --absolute-paths

# Specify custom field list file
python catalog_datasets.py --field-file my_custom_fields.txt

# Specify output directory
python catalog_datasets.py --out /path/to/output
```

By default, the script outputs **relative paths** from the current working directory, making catalogs portable across different systems and suitable for version control.

### Generating Catalogs for All Datasets

The `generate_all_catalogs.py` orchestration script automatically generates catalogs for all 38 dcm_qa datasets in the repository. It creates both individual per-dataset catalogs and a combined catalog with all datasets.

**Basic usage:**

```bash
# Generate catalogs with default fields (from catalog_fields.txt)
python generate_all_catalogs.py

# Specify fields to catalog across all datasets
python generate_all_catalogs.py --fields Manufacturer,Modality,EchoTime

# Use absolute paths
python generate_all_catalogs.py --absolute-paths
```

**Output structure:**

```
catalogs/
├── dcm_qa.csv              # Individual dataset catalogs
├── dcm_qa_12bit.csv
├── dcm_qa_agfa.csv
├── ... (38 total)
└── all_datasets.csv        # Combined catalog with Dataset column
```

The combined `all_datasets.csv` includes a "Dataset" column identifying the source dataset for each record, enabling cross-dataset queries and analysis.

### Exploring Catalogs Interactively

The repository includes an interactive exploration tool that provides easy access to catalog data through both terminal and web interfaces.

**Installation of exploration tools:**

```bash
pip install -r requirements.txt
```

**Launch the explorer:**

```bash
./explore_catalog.sh
```

This presents a menu with three options:

1. **VisiData** - Fast terminal-based interactive CSV viewer
   - Great for quick exploration and sorting/filtering
   - Press `h` for help, `q` to quit
   - Sort columns with `[` and `]`
   - Filter with `/` for search

2. **Datasette** - Web-based SQLite browser with search and SQL queries
   - Recommended for deep analysis and complex queries
   - Automatic CSV-to-SQLite conversion
   - Full SQL query support
   - Opens automatically in your browser at http://localhost:8001

3. **Convert to DB only** - Creates SQLite database without launching viewer
   - Useful for custom queries or programmatic access

**Direct mode** (skip menu):

```bash
./explore_catalog.sh 1    # Launch VisiData
./explore_catalog.sh 2    # Launch Datasette
./explore_catalog.sh 3    # Convert to SQLite only
```

### Git Workflow for Catalogs

Generated catalogs are stored in a separate `catalogs` branch to keep the main branch focused on code and reduce repository bloat. This follows the same pattern as GitHub Pages (`gh-pages` branch).

**To update catalogs:**

```bash
# 1. Generate catalogs from main branch
python generate_all_catalogs.py --fields Manufacturer,Modality,EchoTime

# 2. Switch to catalogs branch (create if first time)
git checkout -b catalogs    # First time
# OR
git checkout catalogs       # Subsequent times

# 3. Add and commit catalog files
git add catalogs/
git commit -m "Update catalogs for dcm2niix v1.0.20260416"

# 4. Push to remote
git push origin catalogs

# 5. Return to main branch
git checkout main
```

**To view existing catalogs:**

```bash
git checkout catalogs
./explore_catalog.sh
git checkout main    # When done
```

The `catalogs/` directory is excluded from the main branch via `.gitignore`.

## Dataset Catalog

Below is a comprehensive list of the included repositories. The Manufacturer refers to Canon (C), General Electric (G), Philips (P), Siemens (S), and United Imaging Healthcare (U).

| Repository Name                                                             | Manufacturer   | Comments                                                                  |
|-----------------------------------------------------------------------------|----------------|---------------------------------------------------------------------------|
| [`dcm_qa`](https://github.com/neurolabusc/dcm_qa)                           | S              | Image orientation, total readout time, multi-band, JPEG2000               |
| [`dcm_qa_12bit`](https://github.com/neurolabusc/dcm_qa_12bit)               | S              | 12-bit signed and unsigned voxel intensities                              |
| [`dcm_qa_agfa`](https://github.com/neurolabusc/dcm_qa_agfa)                 | S              | Renaming of private tags                                                  |
| [`dcm_qa_asl`](https://github.com/neurolabusc/dcm_qa_asl)                   | S              | Arterial spin labeling                                                    |
| [`dcm_qa_canon`](https://github.com/neurolabusc/dcm_qa_canon)               | C              | Canon 6.0 classic DICOM images                                            |
| [`dcm_qa_canon_61`](https://github.com/neurolabusc/dcm_qa_canon_61)         | C              | Canon 6.1 images saved as enhanced and classic DICOM                      |
| [`dcm_qa_canon_enh`](https://github.com/neurolabusc/dcm_qa_canon_enh)       | C              | Canon 6.0 enhanced DICOM images                                           |
| [`dcm_qa_cs_dl`](https://github.com/neurolabusc/dcm_qa_cs_dl)               | G, P, S        | Compressed Sensing (CS) and the Deep Learning filters                     |
| [`dcm_qa_ct`](https://github.com/neurolabusc/dcm_qa_ct)                     | G, P           | Computerized Axial Tomography with gantry tilt and varied inter-slice dx  |
| [`dcm_qa_decubitus`](https://github.com/neurolabusc/dcm_qa_decubitus)       | S              | Head first decubitus images                                               |
| [`dcm_qa_decubitus_ge`](https://github.com/neurolabusc/dcm_qa_decubitus_ge) | G              | Head first decubitus image                                                |
| [`dcm_qa_deident`](https://github.com/neurolabusc/dcm_qa_deident)           | S              | De-identification method parameters                                       |
| [`dcm_qa_dti`](https://github.com/neurolabusc/dcm_qa_dti)                   | S              | Diffusion directions with various slice angulations                       |
| [`dcm_qa_enh`](https://github.com/neurolabusc/dcm_qa_enh)                   | C, P, S        | Enhanced DICOM                                                            |
| [`dcm_qa_fmap`](https://github.com/neurolabusc/dcm_qa_fmap)                 | G, S           | Field mapping                                                             |
| [`dcm_qa_ge`](https://github.com/neurolabusc/dcm_qa_ge)                     | G              | Slice timing, acquisition acceleration                                    |
| [`dcm_qa_me`](https://github.com/neurolabusc/dcm_qa_me)                     | S              | Multi-echo sequences                                                      |
| [`dcm_qa_mosaic`](https://github.com/neurolabusc/dcm_qa_mosaic)             | S              | Mosaic images with recommended and deprecated image numbering             |
| [`dcm_qa_mprage`](https://github.com/neurolabusc/dcm_qa_mprage)             | S              | Magnetization Prepared - RApid Gradient Echo sequences                    |
| [`dcm_qa_nih`](https://github.com/neurolabusc/dcm_qa_nih)                   | G, S           | Phase encoding polarity                                                   |
| [`dcm_qa_pdt2`](https://github.com/neurolabusc/dcm_qa_pdt2)                 | S              | Proton-Density and T2-weighted imaging                                    |
| [`dcm_qa_philips`](https://github.com/neurolabusc/dcm_qa_philips)           | P              | Philips classic and enhanced DICOMs                                       |
| [`dcm_qa_philips_asl`](https://github.com/neurolabusc/dcm_qa_philips_asl)   | P              | Philips classic DICOM arterial spin labeling                              |
| [`dcm_qa_philips_asl_enh`](https://github.com/neurolabusc/dcm_qa_philips_asl_enh) | P        | Philips enhanced DICOM arterial spin labeling                             |
| [`dcm_qa_philips_dwi`](https://github.com/neurolabusc/dcm_qa_philips_dwi)   | P              | Philips diffusion-weighted imaging with unusual volume ordering           |
| [`dcm_qa_philips_enh`](https://github.com/neurolabusc/dcm_qa_philips_enh)   | P              | Philips enhanced DICOM                                                    |
| [`dcm_qa_polar`](https://github.com/neurolabusc/dcm_qa_polar)               | G              | GE reversed phase encoding polarity                                       |
| [`dcm_qa_sag`](https://github.com/neurolabusc/dcm_qa_sag)                   | S              | Sagittal diffusion images                                                 |
| [`dcm_qa_stc`](https://github.com/neurolabusc/dcm_qa_stc)                   | G, S, U        | Slice timing correction                                                   |
| [`dcm_qa_table`](https://github.com/neurolabusc/dcm_qa_table)               | G, P, S        | Tracking table position                                                   |
| [`dcm_qa_toshiba`](https://github.com/neurolabusc/dcm_qa_toshiba)           | C              | Toshiba 5.0 classic DICOMs                                                |
| [`dcm_qa_trt`](https://github.com/neurolabusc/dcm_qa_trt)                   | G              | Total Readout Time                                                        |
| [`dcm_qa_ts`](https://github.com/neurolabusc/dcm_qa_ts)                     | S              | Various DICOM transfer syntaxes                                           |
| [`dcm_qa_uih`](https://github.com/neurolabusc/dcm_qa_uih)                   | U              | United Imaging Healthcare ("UIH") MRI scanners                            |
| [`dcm_qa_xa30`](https://github.com/neurolabusc/dcm_qa_xa30)                 | S              | Siemens XA30 enhanced DICOMs                                              |
| [`dcm_qa_xa30i`](https://github.com/neurolabusc/dcm_qa_xa30i)               | S              | Siemens XA30 classic (interoperability) DICOM                             |

## Duplicate Archives

The latest version of this repository is stored on [Github](https://github.com/neurolabusc/dcm_validate). For long-term access and reproducibility, persistent snapshots are archived on both [Zenodo](https://doi.org/10.5281/zenodo.15310934) and the [Open Science Framework](https://doi.org/10.17605/OSF.IO/FT49). Please use the `Issues` functionality on Github to suggest enhancements.
