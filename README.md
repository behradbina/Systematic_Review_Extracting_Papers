# Systematic Review Paper Retrieval Pipeline

A Python toolkit that automates the first, most repetitive stages of a **systematic review / meta-analysis**: searching multiple scientific databases, merging and de-duplicating the results, finding open-access full texts, and preparing structured data-extraction sheets.

It was built for a real systematic review on the **intracerebroventricular streptozotocin (ICV-STZ) rodent model of sporadic Alzheimer's disease**, but every query and file path is configurable, so it can be reused for any review topic.

---

## Why

A systematic review usually starts with hundreds of records spread across several databases, each with its own export format and many duplicates between them. Doing this by hand is slow and error-prone. This project turns it into a reproducible pipeline:

```
 PubMed ─┐
 Scopus ─┤                         ┌─> unified, de-duplicated CSV ──> screening
 Scholar ┼─> retrieve ─> normalize ┤
 SciDir ─┘    (APIs /     & merge  └─> full-text finder (PMC, DOI, Unpaywall)
              scraping)                         │
                                                v
                               structured data extraction (LLM prompt + plot digitising)
                                                │
                                                v
                                         meta-analysis (R)
```

---

## Features

### 1. Multi-database search (`retrievers/retrieve_papers.py`)

| Source | How it is queried | Output |
|---|---|---|
| **PubMed** | NCBI E-utilities via `Biopython.Entrez` (`esearch` + `efetch`) | Title, abstract, journal, year, DOI, PMID |
| **Scopus** | Elsevier Scopus Search API via `pybliometrics` | JSON + CSV of results |
| **Google Scholar** | `scholarly` scraping; missing DOIs looked up from the title with the **CrossRef API** | Records with and without DOI |
| **ScienceDirect** | Parses the **RIS export** from ScienceDirect (incl. multi-line abstracts) into CSV | CSV |

### 2. Cleaning and merging
- Normalizes DOIs (strips `https://doi.org/` prefixes) so the same paper matches across sources
- Removes duplicates by **DOI**, and by **title** when no DOI is available
- Only keeps records from a new source that are not already in the base result file
- Merges all sources into one CSV with standard columns: `Title, Abstract, Journal, Year, DOI`

### 3. Full-text retrieval (legal, open-access sources only)
- `retrieve_pmcid.py`: converts **PMIDs to PMCIDs** with the NCBI ID Converter API and lists PubMed Central PDF links
- `download_fulltext.py`: looks up the PMCID, then downloads the best open-access PDF from the **Unpaywall API** (direct PMC PDF download is work in progress; use the links from `retrieve_pmcid.py` meanwhile)
- `PubmedArticles.retrieve_full_text()`: falls back to DOI resolution and publisher URL patterns (PLOS, Nature, Springer, Elsevier)
- Writes a `download_report.csv` and a `failed_papers.csv` for papers that need manual access
- Waits between requests to respect API rate limits

### 4. Data extraction for meta-analysis (`meta_analysis/`)
- `prompt.txt`: a structured **LLM extraction prompt** that turns a paper into one CSV row with 35 fields (animal model, strain, STZ dose, injection coordinates, sample sizes, behavioural tests, outcomes, molecular techniques, signalling pathways, ...)
- `extract.R`: sets up **metaDigitise / shinyDigitise** to pull numeric values (means, SDs) out of published plots
- `test.py`: collects the papers assigned to each reviewer (DOI, figure links, group sizes) from the shared extraction sheet
- `activity_report.py`: bar chart of how many papers each reviewer has extracted

---

## Project structure

```
Systematic_Review_Extracting_Papers/
├── retrievers/
│   ├── main.py                 # entry point: set your queries here
│   ├── retrieve_papers.py      # PubMed, Google Scholar, Scopus, ScienceDirect classes
│   ├── retrieve_pmcid.py       # PMID -> PMCID conversion
│   ├── download_fulltext.py    # PMC + Unpaywall PDF download
│   └── data/                   # search results from each database
├── meta_analysis/
│   ├── prompt.txt              # LLM data-extraction prompt
│   ├── extract.R               # metaDigitise / shinyDigitise setup
│   ├── test.py                 # per-reviewer extraction lists
│   └── activity_report.py      # reviewer progress chart
├── LICENSE
└── README.md
```

---

## Installation

Python 3.10+ recommended.

```bash
git clone https://github.com/behradbina/Systematic_Review_Extracting_Papers.git
cd Systematic_Review_Extracting_Papers
pip install biopython pybliometrics scholarly pandas requests beautifulsoup4 lxml tqdm openpyxl matplotlib
```

For the R part (plot digitising), see the package list in `meta_analysis/extract.R`.

### API configuration
| Service | What you need |
|---|---|
| PubMed (NCBI) | Your email address (passed as `email=`), required by NCBI |
| Scopus | An Elsevier API key. Run `pybliometrics.scopus.init()` once and enter it. Some fields need an institutional network. |
| Unpaywall | Your email address (set `EMAIL` in `download_fulltext.py`) |
| CrossRef | No key needed |

---

## Usage

1. Open `retrievers/main.py` and write your search query for each database (commented examples for PubMed, Google Scholar and Scopus are already in the file).
2. Un-comment the sources you want to run, then:

```bash
cd retrievers
python main.py
```

Example: PubMed search

```python
from retrieve_papers import PubmedArticles

query = '("Streptozotocin"[Mesh Terms] OR STZ[Title/Abstract]) AND (rat[Title/Abstract] OR mice[Title/Abstract])'
PubmedArticles(query=query, email="you@example.com", retmax=600,
               output_file_path="data/search_result.csv")
```

Example: merge a ScienceDirect RIS export into the existing results

```python
from retrieve_papers import ScienceDirect

ScienceDirect(ris_file="data/ScienceDirect_citations.ris",
              base_file="all.csv",
              csv_path="data/ScienceDirect.csv")
```

3. To find full texts for the final list, set the input path and your email in `download_fulltext.py` or `retrieve_pmcid.py` and run it.

---

## Notes and limitations
- Google Scholar has no official API. `scholarly` can be rate-limited or blocked, so keep `limit` small.
- Only legal, open-access sources are used for PDFs. Anything else is listed in `failed_papers.csv` for access through your institution.
- Check the terms of use of each database before sharing exported search results.

## Roadmap
- Finish direct PDF download from PubMed Central
- Move queries, paths and emails into a single config file
- Command-line interface (`python -m retrievers --source pubmed --query ...`)
- Run the LLM extraction prompt automatically over downloaded PDFs
- Simple GUI for researchers without programming experience

## License
MIT. See [LICENSE](LICENSE).
