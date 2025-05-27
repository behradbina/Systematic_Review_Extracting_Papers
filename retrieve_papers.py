import csv
import requests
import pandas as pd
import json
import os

from Bio import Entrez
from scholarly import scholarly
import pybliometrics
from pybliometrics.scopus import ScopusSearch

from tqdm import tqdm
import requests
from pyunpaywall import Unpaywall
import time

#!pip install requests pandas tqdm pyunpaywall

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
        
        article_ids = self.search_pubmed()
        self.fetch_data(article_ids)


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

    def download_pdf(self, url, filename, headers=None):
        """Generic PDF downloader with error handling"""
        if headers is None:
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

    def try_legal_sources(self, row):
        """Attempt to download from various legal sources"""
        pmid = str(row['Pmid'])
        doi = str(row['Doi']) if pd.notna(row['Doi']) else None
        title = row['Title']
        journal = row['Journal']
        
        filename = f"downloaded_pdfs/{pmid}_{journal.replace(' ', '_')[:20]}.pdf"
        
        # 1. Try PubMed Central (if available)
        if pd.notna(doi):
            # Check if DOI is from PMC
            pmc_url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/doi/{doi}/pdf/"
            if self.download_pdf(pmc_url, filename):
                return True, "PubMed Central"
        
        if doi:
            try:
                upw = Unpaywall(doi=doi, is_oa_only=True)
                if upw.is_oa and upw.best_oa_location:
                    pdf_url = upw.best_oa_location['url_for_pdf'] or upw.best_oa_location['url']
                    if self.download_pdf(pdf_url, filename):
                        return True, "Unpaywall"
            except:
                pass
        
        # 3. Try DOI.org redirect
        if doi:
            try:
                doi_url = f"https://doi.org/{doi}"
                response = requests.get(doi_url, allow_redirects=True, timeout=10)
                final_url = response.url
                if final_url != doi_url and 'pdf' in final_url.lower():
                    if self.download_pdf(final_url, filename):
                        return True, "Publisher Site"
            except:
                pass
        
        # 4. Try direct journal links (example for common journals)
        if pd.notna(journal):
            journal_lower = journal.lower()
            if 'plos' in journal_lower and doi:
                plos_url = f"https://journals.plos.org/plosone/article/file?id={doi}&type=printable"
                if self.download_pdf(plos_url, filename):
                    return True, "PLOS"
            elif 'nature' in journal_lower and doi:
                nature_url = f"https://www.nature.com/articles/{doi}.pdf"
                if self.download_pdf(nature_url, filename, headers={'Accept': 'application/pdf'}):
                    return True, "Nature"
        
        return False, "Not found"


    def retrieve_full_text(self):
        
        df = pd.read_csv("search_result.csv")
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
            time.sleep(1)  # Be polite to servers :))))

        # Save download report
        report_df = pd.DataFrame(results)
        report_df.to_csv("download_report.csv", index=False)

        print(f"\nDownload summary:")
        print(f"Successfully downloaded: {success_count}/{len(df)} papers")
        print(f"Download rate: {success_count/len(df)*100:.1f}%")
        print("Detailed report saved to download_report.csv")
        



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
        # Read the base file containing existing articles (with columns Doi and Title)
        search_df = pd.read_csv(self.base_file, usecols=['Doi', 'Title'])
        
        # Read all found articles from the CSV
        all_articles = pd.read_csv(self.filname_csv_data)
        
        # Split into articles with DOI and without DOI
        have_doi_articles = all_articles[all_articles['Doi'].notnull()].copy()  # Articles with DOI
        no_doi_found = all_articles[all_articles['Doi'].isnull()].copy()       # Articles without DOI
        
        # Process articles with DOI:
        # 1. Remove duplicates
        # 2. Remove articles that already exist in search_df (matched by DOI)
        have_doi_articles = have_doi_articles.drop_duplicates()
        have_doi_articles = have_doi_articles[~have_doi_articles['Doi'].isin(search_df['Doi'])]
        
        # Process articles without DOI:
        # 1. Remove duplicates
        # 2. Remove articles that already exist in search_df (matched by Title)
        no_doi_found = no_doi_found.drop_duplicates()
        no_doi_found = no_doi_found[~no_doi_found['Title'].isin(search_df['Title'])]
        
        # Combine both sets of articles
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
                
