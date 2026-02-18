# ADEPT

**Automated Data Extraction for Plant Traits**

## Overview

*This repository accompanies the ADEPT research paper.*

ADEPT is a workflow for the automated extraction of plant trait information from biodiversity literature, producing structured matrices of trait terms derived from taxonomic descriptions.

Descriptions are sourced from the Biodiversity Heritage Library (BHL), eFloras (Flora of North America; Flora of Chine; Flora of Pakistan), and EcoFlora. Because BHL literature contains a mixture of narrative text and formal species descriptions, ADEPT uses a binary text classifier to identify candidate descriptive passages before downstream processing.

Trait extraction is then performed using rule-based matching approaches designed for botanical descriptive language, enabling consistent identification of morphological and ecological trait terms from heterogeneous historical and contemporary texts.

The resulting outputs are structured trait matrices suitable for downstream ecological, evolutionary, and biodiversity informatics analyses. Output matrices for Angiosperms are available at https://doi.org/10.5519/p3dm31kc 


---

## Installation

ADEPT requires **Python 3.11+** and uses
[uv](https://github.com/astral-sh/uv) for dependency management.

### Install uv (if needed)

```bash
curl -Ls https://astral.sh/uv/install.sh | sh
```

### Create a virtual environment

```bash
uv venv --python 3.11
source .venv/bin/activate
```

### Install ADEPT from GitHub

```bash
uv pip install git+https://github.com/NaturalHistoryMuseum/ADEPT.git
```

For reproducible analyses, installing a tagged release rather than the main branch is recommended.

---

## Install Assets

ADEPT requires Biodiversity Heritage Library data downloaded locally.

### BHL Names Index (required)

Creates a **local index of taxonomic occurrences across BHL pages** derived from BHL data archives.

```bash
adept assets bhl-names
```

---

### BHL OCR Archive (optional — strongly recommended)

Downloads a local copy of the BHL Optical Character Recognition (OCR) full-text export:

Richard, Joel & Dearborn, Jacqueline (2022).
*BHL Optical Character Recognition (OCR) – Full Text Export*.
Smithsonian Libraries and Archives.
https://doi.org/10.25573/data.21422193.v22

If the BHL OCR archive is not locally, ADEPT will retrieve page text via the BHL API. This may significantly degrade processing speed.

```bash
adept assets bhl-ocr
```

---

## Models

Pretrained ADEPT machine-learning models used in the paper are available via Hugging Face:

* Taxonomic named-entity recognition model
  https://huggingface.co/benhartley/en_adept_ner_trf

* Description classification model
  https://huggingface.co/benhartley/en_description_classifier

These enable reproducibility of the text-mining workflow described in the manuscript.

---

## CLI Usage

ADEPT provides a command-line interface for running extraction workflows.

### Trait Extraction

Generate a trait matrix for a species:

```bash
adept traits --taxa "Anisotes trisulcus" --group angiosperm
```

Use Tesseract OCR instead of BHL OCR:

```bash
adept traits --taxa "Anisotes trisulcus" --group angiosperm --ocr TESSERACT
```

Process species from an input spreadsheet:

```bash
adept traits --file ../data/examples/angiosperm-10.xlsx --limit 4 --group angiosperm
```

---

### Botanical Descriptions

Retrieve botanical descriptions from BHL, Ecoflora, and eFlora sources:

```bash
adept descriptions --taxa "Achillea millefolium"
```

---

## Advanced Options

### OCR Source Selection

By default, ADEPT uses OCR text provided by BHL, which may contain OCR errors affecting downstream trait extraction.

To use locally generated OCR via Tesseract instead:

**.env configuration**

```
BHL_OCR_SOURCE=TESSERACT
```

or via CLI:

```bash
adept traits --ocr TESSERACT
```

---

### Caching

Requests to BHL services are cached. Supported backends:

* SQLite (default)
* Redis (recommended for large-scale processing)

Start Redis:

```bash
docker compose up -d redis
```

Configure:

```
CACHE_BACKEND=REDIS
```

---

## Data Sources

ADEPT uses OCR text and metadata derived from:

* Biodiversity Heritage Library (BHL)
* Associated biodiversity literature datasets
* Taxonomic reference datasets such as World Flora Online

Some BHL items may be restricted or unavailable via the public interface; local indexing improves retrieval efficiency while maintaining compatibility with API-based fallback retrieval when necessary.

---

## Luigi scheduler

ADEPT workflows are orchestrated using Luigi, which manages task dependencies, execution order, and pipeline monitoring. By default the pipeline runs with Luigi’s local scheduler, which is suitable for single-machine execution and simple workflows.

You can override this behaviour from the command line:

```
--local-scheduler False
```

or:

```
local_scheduler=False
```

Setting local_scheduler=False enables connection to a central Luigi scheduler, which is useful for distributed execution, multi-user environments, or long-running production pipelines.

#### Scheduler service (Tornado)

The Luigi central scheduler runs as a lightweight web service built on the Tornado web framework. This provides:

A task coordination endpoint for workers

A browser-based monitoring interface

Visibility into task status, failures, and dependencies

To use this mode, start the Luigi scheduler service separately (typically via luigid) before running ADEPT tasks.

--

## Citation

If you use ADEPT, please cite:

* The ADEPT paper (once published)
* The BHL OCR dataset
* The ADEPT Hugging Face models listed above

A BibTeX entry will be added once the paper is formally published.

---

## License

(Insert license information here.)

---
