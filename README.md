# **Systematic_Review_Extracting_Papers**

Automating literature retrieval, cleaning, and preparation for systematic reviews and meta-analysis.

---

## 📌 **Overview**

Systematic reviews require extensive searching across multiple databases and careful removal of duplicates.
Manually performing these steps is time-consuming, error-prone, and inefficient.

This repository provides a **fully automated pipeline** for:

* 🔍 **Searching four major scientific databases**

  * **Google Scholar**
  * **ScienceDirect**
  * **PubMed**
  * **Scopus**

* 📥 **Retrieving metadata & bibliographic information** based on a unified search query

* 🧹 **Cleaning and preprocessing the dataset**

  * Removing duplicate articles (by DOI / title)
  * Converting RIS → CSV
  * DOI normalization
  * Merging data from multiple sources

* 📊 **Preparing datasets for meta-analysis**, including:

  * Structured extraction tables
  * Automated indexing
  * Linking behavioural tests and DOI mappings

This pipeline significantly accelerates the early stages of a systematic review, ensuring a reproducible, transparent workflow.

---

## ⚙️ **Features**

### ✔ Automated multi-database search

Unified Python scripts retrieve results from PubMed, Scopus, ScienceDirect, and Google Scholar.

### ✔ RIS to CSV conversion

Supports extraction of:

* Title
* Abstract
* Journal
* DOI
* Date
* URL
  (including multi-line abstract handling)

### ✔ Duplicate removal

Detects duplicates based on DOI and removes repeated entries across databases.

### ✔ Merging datasets

Combines Scopus, PubMed, and custom datasets into a unified CSV with standardized headers.

### ✔ Integration with meta-analysis workflow

Outputs clean CSV files ready to be used for downstream statistical analysis in R or Python.

---

## 🧩 **Dependencies**

Install required libraries:

```bash
pip install biopython
```

```bash
conda install -c conda-forge scholarly
```

Additional optional packages depending on your system: pandas, numpy, selenium, requests, beautifulsoup4

---

## 🔎 **ScienceDirect Search Query (Example)**


Can be adapted for any systematic review topic.


## 📁 **Project Structure** (suggested)

```
Systematic_Review_Extracting_Papers/
│── meta_analysis/
│── retrievers/
│   ├── main.py
│── README.md

```

For running the script you should put the well-structured search query in the main.py. (samples are shown in main.py)

```bash
python main.py
```

---

## 🚀 **Future Improvements**

* Add Selenium-based full-text downloading
* Create a GUI for researchers with no programming background
