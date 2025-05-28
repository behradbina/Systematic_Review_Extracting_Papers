from Bio import Entrez
import csv
import json
import os
import pandas as pd
import pybliometrics
from pybliometrics.scopus import ScopusSearch
import requests
from tqdm import tqdm
import time

class PubmedArticles:
    query = ""
    email = ""
    retmax = 0
    output_file_path = ""
    
    def __init__(self, query, email:str, retmax:int, output_file_path="data/search_result.csv"):
        self.query= query
        self.email = email
        self.retmax = retmax
        self.output_file_path = output_file_path
        
        #article_ids = self.search_pubmed()
        #self.fetch_data(article_ids)
        self.retrieve_full_text()

    def search_pubmed(self):
        Entrez.email = self.email 
        handle = Entrez.esearch(db="pubmed", term=self.query, retmax=self.retmax)
        record = Entrez.read(handle)
        handle.close()
        return record["IdList"]

    def fetch_article_details(self, article_ids):
        Entrez.email = self.email  
        handle = Entrez.efetch(db="pubmed", id=",".join(article_ids), rettype="abstract", retmode="xml")
        records = Entrez.read(handle)
        handle.close()
        return records


    def save_to_csv(self, articles):
        with open(self.output_file_path, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)

            writer.writerow(["Title", "Year", "Abstract", "Pmid", "Journal", "Doi"])

            for article in articles:
                writer.writerow([article['title'], article['year'], article['abstract'], article['pmid'], article['journal'], article['doi']])

    def fetch_data(self, article_ids):
        if article_ids:
            articles = self.fetch_article_details(article_ids)
            article_list = []
            for article in articles['PubmedArticle']:
                title = article['MedlineCitation']['Article']['ArticleTitle']
                abstract = article['MedlineCitation']['Article'].get('Abstract', {}).get('AbstractText', ['No abstract available'])[0]
                year = article['MedlineCitation']['Article']['Journal']['JournalIssue']['PubDate'].get('Year', 'No year available')
                pmid =  article['MedlineCitation']['PMID']
                journal = article['MedlineCitation']['Article']['Journal']['ISOAbbreviation']
                
                doi = ""
                try:
                    doi = article['MedlineCitation']['Article']['ELocationID'][0]
                except:
                    doi = "N/A"
                
                article_list.append({
                    'title': title,
                    'year': year,
                    'abstract': abstract,
                    'pmid' : pmid,
                    'journal' : journal,
                    'doi' : doi
                })
            
            self.save_to_csv(article_list)
            print(f"Results saved to "+ self.output_file_path)
        else:
            print("No articles found.")

    def download_pdf(self,url, filename):
        """Generic PDF downloader with error handling"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        try:
            response = requests.get(url, headers=headers, stream=True, timeout=30)
            if response.status_code == 200:
                # Check if content is actually PDF
                content_type = response.headers.get('content-type', '').lower()
                if 'pdf' in content_type or 'octet-stream' in content_type:
                    with open(filename, 'wb') as f:
                        for chunk in response.iter_content(1024):
                            f.write(chunk)
                    return True
            return False
        except Exception as e:
            print(f"Error downloading {url}: {str(e)}")
            return False

    def try_legal_sources(self,row):
        """Attempt to download from various legal sources"""
        pmid = str(row['Pmid'])
        doi = str(row['Doi']) if pd.notna(row['Doi']) else None
        title = row['Title']
        journal = row['Journal']
        
        # Create a safe filename
        safe_title = "".join(c if c.isalnum() else "_" for c in title)[:50]
        filename = f"downloaded_pdfs/{pmid}_{safe_title}.pdf"
        
        # 1. Try PubMed Central (if available)
        if pd.notna(doi):
            pmc_url1 = f"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{pmid}/pdf/"
            # PMC URL pattern 2 (for DOIs)
            pmc_url2 = f"https://www.ncbi.nlm.nih.gov/pmc/articles/doi/{doi}/pdf/"
            
            for url in [pmc_url1, pmc_url2]:
                if self.download_pdf(url, filename):
                    return True, "PubMed Central"
        
        # 2. Try direct DOI resolution
        if doi:
            try:
                # First get the final URL from DOI.org
                doi_url = f"https://doi.org/{doi}"
                response = requests.get(doi_url, allow_redirects=True, timeout=10)
                final_url = response.url
                
                # Check if the final URL looks like a PDF
                if final_url.lower().endswith('.pdf'):
                    if self.download_pdf(final_url, filename):
                        return True, "Publisher PDF"
                
                # Some sites have PDF links on their page
                if 'sciencedirect' in final_url:
                    pdf_url = final_url.replace('/science/article/', '/science/article/pii/') + '/pdfft'
                    if self.download_pdf(pdf_url, filename):
                        return True, "ScienceDirect"
                
                elif 'springer' in final_url:
                    pdf_url = final_url.replace('/article/', '/content/pdf/') + '.pdf'
                    if self.download_pdf(pdf_url, filename):
                        return True, "Springer"
                        
            except Exception as e:
                print(f"Error processing DOI {doi}: {str(e)}")
        
        # 3. Try journal-specific patterns
        if pd.notna(journal):
            journal_lower = journal.lower()
            
            # PLOS journals
            if 'plos' in journal_lower and doi:
                plos_url = f"https://journals.plos.org/plosone/article/file?id={doi}&type=printable"
                if self.download_pdf(plos_url, filename):
                    return True, "PLOS"
            
            # Nature journals
            elif 'nature' in journal_lower and doi:
                nature_url = f"https://www.nature.com/articles/{doi}.pdf"
                if self.download_pdf(nature_url, filename):
                    return True, "Nature"
            
            # ScienceDirect journals
            elif 'elsevier' in journal_lower and doi:
                sciencedirect_url = f"https://www.sciencedirect.com/science/article/pii/{doi}/pdfft"
                if self.download_pdf(sciencedirect_url, filename):
                    return True, "Elsevier"
        
        return False, "Not found"



    def retrieve_full_text(self):
        
        df = pd.read_csv(self.output_file_path)
        # Create directories for PDFs
        os.makedirs("downloaded_pdfs", exist_ok=True)
        os.makedirs("failed_downloads", exist_ok=True)
        
        # Process all papers
        results = []
        success_count = 0

        for _, row in tqdm(df.iterrows(), total=len(df)):
            success, source = self.try_legal_sources(row)
            results.append({
                'PMID': row['Pmid'],
                'Title': row['Title'],
                'DOI': row['Doi'],
                'Journal': row['Journal'],
                'Downloaded': success,
                'Source': source
            })
            if success:
                success_count += 1
            time.sleep(1)  # Respectful delay between requests

        report_df = pd.DataFrame(results)
        report_df.to_csv("download_report.csv", index=False)

        print(f"\nDownload summary:")
        print(f"Successfully downloaded: {success_count}/{len(df)} papers")
        print(f"Download rate: {success_count/len(df)*100:.1f}%")
        print("Detailed report saved to download_report.csv")

        # Generate list of failed downloads for manual processing
        failed_df = report_df[report_df['Downloaded'] == False]
        if not failed_df.empty:
            failed_df.to_csv("failed_downloads/failed_papers.csv", index=False)
            print(f"\nCould not download {len(failed_df)} papers.")
            print("You can try these methods for the remaining papers:")
            print("1. Check if your institution has access via their library portal")
            print("2. Search for the paper title on Google Scholar and look for [PDF] links")
            print("3. Use the 'Request PDF' option on ResearchGate")
            print("4. Email the authors directly (most will gladly share their work)")
        else:
            print("\nSuccessfully downloaded all papers!")


        



class GoogleScholar:
    base_file = ""
    output_file = ""
    
    def __init__(self, query:str, limit:int, base_file:str, output_file:str):
        self.output_file = output_file
        self.base_file = base_file
        have_doi_articles , no_doi_found = self.scraping_articles_google_scholar(query=query, limit=limit)
        self.process_found_articles(have_doi_articles , no_doi_found)

    def get_doi_from_crossref(self, title):
        """
        Given a paper title, query CrossRef for its DOI.
        """
        url = "https://api.crossref.org/works"
        params = {"query.title": title, "rows": 1}
        try:
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            if data["message"]["items"]:
                return data["message"]["items"][0].get("DOI")
        except Exception as e:
            print(f"Error querying CrossRef for title: {title}\n{e}")
        return None

    def scraping_articles_google_scholar(self, query, limit: int):    
        have_doi_articles = {
            'Title' : [],
            'Year' : [],
            'Journal' : [],
            'Doi' : []
        }

        no_doi_found = {
            'Title' : [],
            'Year' : [],
            'Journal' : [],
            'Doi' : []
        }

        print(f"Searching Google Scholar for: {query}\n")

        search_query = scholarly.search_pubs(query)

        doi_count = 0

        for pub in search_query:
            bib = pub.get('bib', {})
            title = bib.get('title', '')
            year = bib.get('pub_year') or bib.get('year', '')
            journal = bib.get('venue', '') # The journal name 
            
            if not title:
                continue
            
            doi = self.get_doi_from_crossref(title)
            if doi :
                have_doi_articles['Title'].append(title)
                have_doi_articles['Year'].append(year)
                have_doi_articles['Journal'].append(journal)
                have_doi_articles['Doi'].append('https://doi.org/'+doi)    
            else: 
                no_doi_found['Title'].append(title)
                no_doi_found['Year'].append(year)
                no_doi_found['Journal'].append(journal)
                no_doi_found['Doi'].append(None)
                    
            print(f"Saved paper: with DOI: {doi}")
            doi_count += 1

            if doi_count >= limit:
                break

        have_doi_articles = pd.DataFrame(have_doi_articles)
        no_doi_found = pd.DataFrame(no_doi_found)
        return have_doi_articles , no_doi_found

    def process_found_articles(self,have_doi_articles , no_doi_found):
        search_df = pd.read_csv(self.base_file, usecols=['Doi', 'Title'])

        have_doi_articles = have_doi_articles.drop_duplicates()
        have_doi_articles = have_doi_articles[~have_doi_articles['Doi'].isin(search_df['Doi'])]

        no_doi_found = no_doi_found.drop_duplicates()
        no_doi_found = no_doi_found[~no_doi_found['Title'].isin(search_df['Title'])]

        combined_df = pd.concat([have_doi_articles, no_doi_found], ignore_index=True)

        combined_df.to_csv(self.output_file, index=False)

class Scopus:
    filname_json_data = r"data/scopus_results.json"
    filname_csv_data = r"data/scopus_results.csv"
    base_file =  ""
    def __init__(self, query:str, base_file:str):
        
        self.base_file = base_file
        
        #pybliometrics.scopus.init()
        #self.fetch_articles(query)
        
        self.save_in_csv()
        self.process_found_articles()
        
                
    def extract_year(cover_date):
        if cover_date and isinstance(cover_date, str):
            return cover_date.split("-")[0]
        return ""

    def fetch_articles(self, query:str):
        
        s = ScopusSearch(
            query,
            download=True,  
            max_entries=0 
        )
        results = [dict(r._asdict()) for r in s.results]
        with open(self.filname_json_data, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=4, default=str)  
        print(f"Successfully saved {len(results)} results to "+ self.filname_json_data)
    
    def save_in_csv(self):
        with open(self.filname_json_data, 'r', encoding='utf-8') as json_file:
            data = json.load(json_file)  

        field_mapping = {
            'title': 'Title',
            'coverDate': 'Year',
            'description': 'Abstract',
            'publicationName': 'Journal',
            'doi': 'Doi'
        }

        json_fields = list(field_mapping.keys())
        csv_headers = list(field_mapping.values())

        with open(self.filname_csv_data, 'w', newline='', encoding='utf-8') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=csv_headers)
            writer.writeheader()
            
            for item in data:
                row = {field_mapping[field]: item.get(field, '') for field in json_fields}
                writer.writerow(row)

    
    def process_found_articles(self):
        search_df = pd.read_csv(self.base_file, usecols=['Doi', 'Title'])
        
        all_articles = pd.read_csv(self.filname_csv_data)
        
        have_doi_articles = all_articles[all_articles['Doi'].notnull()].copy()  # Articles with DOI
        no_doi_found = all_articles[all_articles['Doi'].isnull()].copy()       # Articles without DOI
        
        have_doi_articles = have_doi_articles.drop_duplicates()
        have_doi_articles = have_doi_articles[~have_doi_articles['Doi'].isin(search_df['Doi'])]
        no_doi_found = no_doi_found.drop_duplicates()
        no_doi_found = no_doi_found[~no_doi_found['Title'].isin(search_df['Title'])]
        
        combined_df = pd.concat([have_doi_articles, no_doi_found], ignore_index=True)
        combined_df['Year'] = pd.to_datetime(combined_df['Year']).dt.year
        combined_df.to_csv(self.filname_csv_data, index=False)

class ScienceDirect:
    filname_json_data = r"data/siencedirect_results.json"
    filname_csv_data = r"data/siencedirect_results.csv"
    api_key = '75ecad9636d0bc96d40ed6a5518e7e44'
    base_file =  ""
    
    def __init__(self, query:str, base_file:str):
        
        self.base_file = base_file
        articles = self.get_all_articles(query)
        self.save_articles_to_csv(articles=articles)

    def search_sciencedirect(self, query, start=0, count=25):
        """
        Searches ScienceDirect for articles matching the query.
        
        Parameters:
            query (str): The search query.
            api_key (str): Your Elsevier API key.
            start (int): The starting index for the results.
            count (int): The number of results to retrieve per request.
        
        Returns:
            dict: The JSON response from the API.
        """
        
        url = "https://api.elsevier.com/content/search/sciencedirect"
        headers = {
            "X-ELS-APIKey": self.api_key,
            "Accept": "application/json"
        }
        params = {
            "query": query,
            "start": start,
            "count": count
        }
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code != 200:
            print("Error:", response.status_code, response.text)
            return None
        
        return response.json()

    def get_all_articles(self, query):
        """
        Retrieves all articles information from ScienceDirect that match the search query.
        
        Parameters:
            query (str): The search query.
            api_key (str): Your Elsevier API key.
        
        Returns:
            list: A list of article entries.
        """
        articles = []
        start = 0
        count = 25  # page size; adjust if necessary

        while True:
            data = self.search_sciencedirect(query, start=start, count=count)
            if data is None:
                break
            
            entries = data.get('search-results', {}).get('entry', [])
            if not entries:
                break
            
            articles.extend(entries)
            
            # If fewer entries are returned than requested, assume it's the last page.
            if len(entries) < count:
                break
            start += count

        return articles

    def save_articles_to_csv(self, articles):
        fieldnames = ["Title", "DOI", "Publication"]
        
        with open(self.filname_csv_data, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for article in articles:
                writer.writerow({
                    "Title": article.get("dc:title", "N/A"),
                    "DOI": article.get("prism:doi", "N/A"),
                    "Publication": article.get("prism:publicationName", "N/A")
                })
                
