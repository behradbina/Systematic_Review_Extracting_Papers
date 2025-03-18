from retrieve_papers import PubmedArticles, GoogleScholar

def main():
    pubmed_search_query = (
        '("Streptozotocin"[Mesh Terms] OR streptozotocin[Title/Abstract] OR STZ[Title/Abstract]) AND ("Intracerebroventricular Injections"[Mesh Terms] OR intracerebroventricular[Title/Abstract] OR ICV[Title/Abstract]) AND ("Rodentia"[Mesh Terms] OR rodent[Title/Abstract] OR mice[Title/Abstract] OR mouse[Title/Abstract] OR "Mus musculus"[Mesh Terms] OR rat[Title/Abstract] OR rats[Title/Abstract] OR "Rattus norvegicus"[Mesh Terms] OR "Rattus rattus"[Mesh Terms])'
    )
    
    base_file = "search_result.csv"
    
    PubmedArticles(query=pubmed_search_query, email="behradbina@gmail.com", retmax=600, output_file_path="search_result.csv")
    
    google_scholar_query = "Streptozotocin AND streptozotocin AND STZ AND Intracerebroventricular AND intracerebroventricular AND rat"
    
    GoogleScholar(query=google_scholar_query, limit=600, base_file=base_file, output_file= 'google_scholar.csv')

if __name__ == "__main__":
    main()
