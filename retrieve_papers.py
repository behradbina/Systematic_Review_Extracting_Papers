from Bio import Entrez
import csv
import requests
from scholarly import scholarly
import pandas as pd
import pybliometrics
from pybliometrics.scopus import ScopusSearch

class PubmedArticles:
    query = ""
    email = ""
    retmax = 0
    output_file_path = ""
    
    def __init__(self, query, email:str, retmax:int, output_file_path="search_result.csv"):
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
                    doi = "https://doi.org/"+article['MedlineCitation']['Article']['ELocationID'][0]
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
            print(f"Results saved to search_result.csv")
        else:
            print("No articles found.")
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
    
    def __init__(self, query:str):
        pybliometrics.scopus.init()
        self.fetch_articles(query)
        
    def extract_year(cover_date):
        if cover_date and isinstance(cover_date, str):
            return cover_date.split("-")[0]
        return ""

    def fetch_articles(self, query:str):
        
        s = ScopusSearch(query)
        results = s.results
        print(f"Found {len(results)} results.")
        
        with open('scopus_results.csv', 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['Title', 'Year', 'Journal', 'DOI']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            count = 0
            for item in results:
                title = getattr(item, 'title', '')
                year = extract_year(getattr(item, 'coverDate', ''))
                journal = getattr(item, 'publicationName', '')
                doi = getattr(item, 'doi', '')
                
                if doi:
                    writer.writerow({
                        'Title': title,
                        'Year': year,
                        'Journal': journal,
                        'DOI': doi
                    })
                    print(f"Saved: {title} with DOI: {doi}")
                    count += 1
                
                if count >= 10:
                    break

        print("Results saved in scopus_results.csv")


