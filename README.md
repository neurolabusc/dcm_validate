[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.15310657.svg)](https://doi.org/10.5281/zenodo.15310657)

# dcm_validate

The `dcm_validate` repository serves as a centralized collection of all `dcm_qa` repositories. Each `dcm_qa` repository provides concise, illustrative examples of specific DICOM image file features. This repository acts as an index, bringing together these independent modules for easier access and management.

## Installation

To clone this repository and initialize all submodules, use the following commands:

```bash
git clone --recursive https://github.com/neurolabusc/dcm_validate.git
```

## Creating a Catalog Table for DICOM series

The included Python script catalog_dicoms.py recursively scans a folder for DICOM files and generates a CSV table summarizing the value of a specified DICOM tag. Since a single DICOM series typically consists of multiple files, the script includes only one representative file per series, determined by the SeriesInstanceUID (0020,000E).

Note that some DICOM attributes may vary across files within the same series. This script reports the value from the first file encountered per series. You can modify the script to suit custom requirements, or alternatively use tools like dcmdump or gdcmdump for more advanced queries.

An example usage to list the manufacturer (0008,0070) for each series:

```bash
python catalog_dicoms.py ./dcm_qa 0008,0070)
```

## Creating a Catalog Table for BIDS JSON images

The included Python script catalog_datasets.py helps identify imaging series that match specific criteria. For instance, you can list properties such as Manufacturer, BodyPart, PatientAge, and EchoTime for each series. Since there are many available properties, the script is designed to be run twice: the first run generates a catalog_fields.txt file listing all possible properties. You can then edit this file to retain only the fields of interest. Re-running the script will generate a table saved as a comma-separated values (CSV) file. To reset and list all properties again, simply delete the catalog_fields.txt file.

```bash
python catalog_datasets.py
# Generating field list file: catalog_fields.txt
# Edit the field list and re-run this script, or use --fields option.
python catalog_datasets.py
```

## Catalog

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

The latest version of this repository is stored on [Github](https://github.com/neurolabusc/dcm_validate). For long-term access and reproducibility, persistent snapshots are archived on both [Zenodo](https://doi.org/10.5281/zenodo.15310657) and the [Open Science Framework](https://doi.org/10.17605/OSF.IO/FT49). Please use the `Issues` functionality on Github to suggest enhancements.
