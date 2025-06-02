import pandas as pd
import requests
import os
import time
from urllib.parse import quote
from bs4 import BeautifulSoup
import concurrent.futures

CSV_PATH = "/home/behrad/University/research/Systematic_Review_Alzheimers_Model/data/cleaned_file.xlsx"  # Path to your CSV file
FILE_PATH = "pmcids.txt"          
EMAIL = "behradbinal@ut.ac.ir"  


def get_pmc_id(pmid: str)->str:
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

def save_pmc_url(pmid:str, pmc_id:str):
    """Download PDF from PubMed Central by finding the real PDF URL"""
    base_url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmc_id}/pdf/"
    
    with open(FILE_PATH, "a") as f:
        f.write(pmid + ":" + base_url+"\n") 

def process_paper(row) -> None:
    pmid = str(row['PMID']).strip()
    pmc_url = ""
    
    if pmid and pmid != 'nan':
        pmc_id = get_pmc_id(pmid)
        
        print(pmid + " converted to : " + str(pmc_id))
        
        if pmc_id:
            save_pmc_url(pmid, pmc_id)
            print(f"✅ :" + pmid +":"+pmc_id)

        else:
            print(f"❌ No accessible PMCID found for " + pmid)

def main():
    df = pd.read_excel(CSV_PATH)
    results = []
    
    print(f"\nStarting get pmcid of {len(df)} papers...")
    
    for _, row in df.iterrows():
        process_paper(row)
        time.sleep(1)
    
if __name__ == "__main__":
    main()
