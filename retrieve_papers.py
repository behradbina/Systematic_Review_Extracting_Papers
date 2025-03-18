from Bio import Entrez
import csv

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

