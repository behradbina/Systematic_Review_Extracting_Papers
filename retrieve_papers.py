from Bio import Entrez
import csv

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


def save_to_csv(articles, filename="search_result.csv"):
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)

        writer.writerow(["Title", "Year", "Abstract"])

        for article in articles:
            writer.writerow([article['title'], article['year'], article['abstract']])

def main():
    search_query = (
        '{"Streptozotocin"[Mesh Terms] OR streptozotocin[Title/Abstract] OR STZ[Title/Abstract]} '
        'AND {"Intracerebroventricular Injections"[Mesh Terms] OR intracerebroventricular[Title/Abstract] OR ICV[Title/Abstract]} '
        'AND {"Rodentia"[Mesh Terms] OR rodent[Title/Abstract] OR mice[Title/Abstract] OR mouse[Title/Abstract] OR "Mus musculus"[Mesh Terms] OR rat[Title/Abstract] OR rats[Title/Abstract]}'
    )

    article_ids = search_pubmed(search_query)
    
    if article_ids:
        articles = fetch_article_details(article_ids)
        article_list = []
        for article in articles['PubmedArticle']:
            title = article['MedlineCitation']['Article']['ArticleTitle']
            abstract = article['MedlineCitation']['Article'].get('Abstract', {}).get('AbstractText', ['No abstract available'])[0]
            year = article['MedlineCitation']['Article']['Journal']['JournalIssue']['PubDate'].get('Year', 'No year available')
            
            article_list.append({
                'title': title,
                'year': year,
                'abstract': abstract
            })
        
        save_to_csv(article_list)
        print(f"Results saved to search_result.csv")
    else:
        print("No articles found.")

if __name__ == "__main__":
    main()