import pandas as pd
import requests
import os
import time
from urllib.parse import quote
from bs4 import BeautifulSoup
import concurrent.futures

# ==============================
# CONFIGURATION (EDIT THESE)
# ==============================
CSV_PATH = "/home/behrad/University/research/Systematic_Review_Alzheimers_Model/data/cleaned_file.xlsx"  # Path to your CSV file
PDF_DIR = "pdfs"          # Output directory for PDFs
EMAIL = "behradbinal@ut.ac.ir"  # Your email for API requests
UNPAYWALL_API_KEY = "your_api_key"  # Get from https://unpaywall.org/products/api
THREADS = 5               # Number of parallel downloads (adjust carefully)
# ==============================

def setup_dirs():
    os.makedirs(PDF_DIR, exist_ok=True)

def get_pmc_id(pmid):
    """Convert PMID to PMC ID using NCBI's ID Converter API"""
    url = f"https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/?tool=py_script&email={EMAIL}&ids={pmid}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'xml')
        if soup.record and 'pmcid' in soup.record.attrs:
            return soup.record['pmcid']
    except Exception as e:
        print(f"PMC ID conversion failed for PMID {pmid}: {str(e)}")
    return None

def download_pmc_pdf(pmc_id):
    """Download PDF from PubMed Central by finding the real PDF URL"""
    base_url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{pmc_id}/pdf"
    pdf_page_url = f"{base_url}pdf/"
    
    
    
    # try:
    #     headers = {
    #         'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    #     }
        
    #     # First get the PDF page that contains the redirect
    #     session = requests.Session()
    #     response = session.get(pdf_page_url, headers=headers, timeout=30)
        
    #     if response.status_code == 200:
    #         # Parse the HTML to find the PDF URL
    #         soup = BeautifulSoup(response.text, 'html.parser')
    #         pdf_link = soup.find('iframe', {'id': 'pdf'})
            
    #         if pdf_link and pdf_link.get('src'):
    #             pdf_url = pdf_link['src']
    #             if not pdf_url.startswith('http'):
    #                 pdf_url = urljoin(base_url, pdf_url)
                
    #             # Now download the actual PDF
    #             pdf_response = session.get(pdf_url, headers=headers, stream=True, timeout=30)
    #             if pdf_response.status_code == 200 and 'pdf' in pdf_response.headers.get('Content-Type', '').lower():
    #                 return pdf_response.content
        
    #     print(f"Failed to find PDF for PMC{pmc_id}")
    #     return None
        
    # except Exception as e:
    #     print(f"Error downloading PMC{pmc_id}: {str(e)}")
    #     return None
    
def get_unpaywall_pdf_url(doi):
    """Get PDF URL from Unpaywall API"""
    url = f"https://api.unpaywall.org/v2/{quote(doi)}?email={EMAIL}"
    headers = {"Accept": "application/json", "Authorization": f"Bearer {UNPAYWALL_API_KEY}"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data.get('best_oa_location') and data['best_oa_location'].get('url_for_pdf'):
            return data['best_oa_location']['url_for_pdf']
    except Exception as e:
        print(f"Unpaywall failed for DOI {doi}: {str(e)}")
    return None

def download_pdf(url):
    """Generic PDF downloader"""
    try:
        response = requests.get(url, stream=True, timeout=15)
        if response.status_code == 200 and 'pdf' in response.headers.get('Content-Type', ''):
            return response.content
    except Exception as e:
        print(f"PDF download failed from {url}: {str(e)}")
    return None

def save_pdf(content, filename):
    """Save PDF to disk"""
    safe_name = "".join(c for c in filename if c.isalnum() or c in "._- ")
    path = os.path.join(PDF_DIR, f"{safe_name}.pdf")
    with open(path, 'wb') as f:
        f.write(content)
    return path

def process_paper(row):
    """Process a single paper record"""
    pmid, doi = str(row['PMID']).strip(), str(row['DOI']).strip()
    identifier = f"PMID_{pmid}" if pmid != 'nan' else f"DOI_{doi}"
    
    print(f"Processing {identifier}")
    pdf_content = None
    source = None
    
    # Try PMC first
    if pmid and pmid != 'nan':
        pmc_id = get_pmc_id(pmid)
        
        print(pmid + " converted to : " + str(pmc_id))
        
        if pmc_id:
            pdf_content = download_pmc_pdf(pmc_id)
            if pdf_content:
                source = "PMC"
    
    # Fallback to Unpaywall
    if not pdf_content and doi and doi != 'nan':
        pdf_url = get_unpaywall_pdf_url(doi)
        if pdf_url:
            pdf_content = download_pdf(pdf_url)
            if pdf_content:
                source = "Unpaywall"
    
    # Save results
    if pdf_content:
        save_path = save_pdf(pdf_content, identifier)
        print(f"✅ Downloaded {identifier} via {source}")
        return (pmid, doi, source, save_path)
    else:
        print(f"❌ No accessible PDF found for {identifier}")
        return (pmid, doi, "Not found", "")

def main():
    setup_dirs()
    df = pd.read_excel(CSV_PATH)
    results = []
    
    print(f"\nStarting download of {len(df)} papers...")
    
    # Process each paper sequentially
    for _, row in df.iterrows():
        result = process_paper(row)
        results.append(result)
        time.sleep(0.5)  # Still being kind to APIs
    
    # Generate report
    report = pd.DataFrame(results, columns=['PMID', 'DOI', 'source', 'path'])
    report_path = "download_report.csv"
    report.to_csv(report_path, index=False)
    print(f"\nDownload complete! Report saved to {report_path}")
    print(f"Summary:\n{report['source'].value_counts()}")

if __name__ == "__main__":
    main()
