from Bio import Entrez

def search_pubmed(query):
    Entrez.email = "behradbina@gmail.com"  
    handle = Entrez.esearch(db="pubmed", term=query, retmax=100)
    record = Entrez.read(handle)
    handle.close()
    return record["IdList"]

def fetch_article_details(article_ids):
    Entrez.email = "behradbina@gmail.com"  
    handle = Entrez.efetch(db="pubmed", id=",".join(article_ids), rettype="abstract", retmode="xml")
    records = Entrez.read(handle)
    handle.close()
    return records

def main():
    search_query = (
        '{"Streptozotocin"[Mesh Terms] OR streptozotocin[Title/Abstract] OR STZ[Title/Abstract]} '
        'AND {"Intracerebroventricular Injections"[Mesh Terms] OR intracerebroventricular[Title/Abstract] OR ICV[Title/Abstract]} '
        'AND {"Rodentia"[Mesh Terms] OR rodent[Title/Abstract] OR mice[Title/Abstract] OR mouse[Title/Abstract] OR "Mus musculus"[Mesh Terms] OR rat[Title/Abstract] OR rats[Title/Abstract]}'
    )

    article_ids = search_pubmed(search_query)
    if article_ids:
        articles = fetch_article_details(article_ids)
        for article in articles['PubmedArticle']:
            title = article['MedlineCitation']['Article']['ArticleTitle']
            abstract = article['MedlineCitation']['Article'].get('Abstract', {}).get('AbstractText', ['No abstract available'])[0]
            year = article['MedlineCitation']['Article']['Journal']['JournalIssue']['PubDate'].get('Year', 'No year available')
            print(f"Title: {title}")
            print(f"Year: {year}")
            print(f"Abstract: {abstract}\n")
    else:
        print("No articles found.")

if __name__ == "__main__":
    main()